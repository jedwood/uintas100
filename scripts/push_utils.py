#!/usr/bin/env python3
"""
Web Push utilities for the Uintas PWA — VAPID key handling, per-device
subscription storage, and broadcasting notifications to every subscribed device.

Mini-only secrets: the VAPID *private* key and the subscription list live in the
gitignored data/push/ directory. The repo is public, so those must never be
committed. The VAPID *public* key (the "application server key") is safe to
publish and is embedded in index.html — print it with `public-key` below.

Web Push on iOS 16.4+ works for a PWA installed to the Home Screen with no Apple
Developer account: Apple runs the push relay, and this module (via pywebpush)
just signs each message with the VAPID private key and POSTs it to the endpoint
Apple handed the device at subscribe time.

Used by:
  - edits_server.py           -> /api/push/{public-key,subscribe,unsubscribe}
  - fetch_latest_stocking.py  -> broadcast() when new stockings are found

CLI:
  python3 scripts/push_utils.py generate-keys   # one-time: create the VAPID keypair
  python3 scripts/push_utils.py public-key       # print the application server key
  python3 scripts/push_utils.py list             # show subscribed devices
  python3 scripts/push_utils.py test "message"   # send a real test push to all devices
"""
import base64
import json
import os
import sys
import threading
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(HERE)
# UINTAS_PUSH_DIR lets tests point the key/subscription store at a scratch dir.
PUSH_DIR = os.environ.get("UINTAS_PUSH_DIR") or os.path.join(REPO_ROOT, "data", "push")
PRIVATE_PEM = os.path.join(PUSH_DIR, "vapid_private.pem")
PUBLIC_KEY_FILE = os.path.join(PUSH_DIR, "vapid_public.txt")
SUBSCRIPTIONS = os.path.join(PUSH_DIR, "subscriptions.json")
DEFAULT_PUSH_DIR = os.path.join(REPO_ROOT, "data", "push")  # real store (never in git)

# VAPID "sub" claim — a contact the push service can reach about our sender.
VAPID_SUB = "mailto:jed@limechile.com"
# How long the push service should retain an undelivered message (device offline).
DEFAULT_TTL = 24 * 60 * 60

# Serializes reads/writes of subscriptions.json across the edits-server threads.
_lock = threading.Lock()


# ---------------------------------------------------------------- VAPID keys
def keys_exist():
    return os.path.exists(PRIVATE_PEM)


def generate_keys(force=False):
    """Create a P-256 VAPID keypair. Refuses to overwrite an existing key
    (that would invalidate every device's subscription) unless force=True."""
    from cryptography.hazmat.primitives.asymmetric import ec
    from cryptography.hazmat.primitives.serialization import (
        Encoding, NoEncryption, PrivateFormat,
    )

    if keys_exist() and not force:
        raise SystemExit(
            f"VAPID key already exists at {PRIVATE_PEM}. Regenerating would "
            f"invalidate all existing subscriptions. Pass --force to override."
        )
    os.makedirs(PUSH_DIR, exist_ok=True)
    priv = ec.generate_private_key(ec.SECP256R1())
    pem = priv.private_bytes(Encoding.PEM, PrivateFormat.PKCS8, NoEncryption())
    with open(PRIVATE_PEM, "wb") as f:
        f.write(pem)
    os.chmod(PRIVATE_PEM, 0o600)
    app_key = application_server_key()
    with open(PUBLIC_KEY_FILE, "w") as f:
        f.write(app_key + "\n")
    return app_key


def application_server_key():
    """The base64url (unpadded) uncompressed public point the browser passes to
    pushManager.subscribe() as applicationServerKey. Derived from the PEM so it
    is always in sync with the private key."""
    from cryptography.hazmat.primitives.serialization import (
        Encoding, PublicFormat, load_pem_private_key,
    )
    with open(PRIVATE_PEM, "rb") as f:
        priv = load_pem_private_key(f.read(), password=None)
    raw = priv.public_key().public_bytes(Encoding.X962, PublicFormat.UncompressedPoint)
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode()


# ---------------------------------------------------------- subscription store
def load_subscriptions():
    if not os.path.exists(SUBSCRIPTIONS):
        return []
    try:
        with open(SUBSCRIPTIONS, encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError):
        return []


def _save_subscriptions(subs):
    os.makedirs(PUSH_DIR, exist_ok=True)
    tmp = SUBSCRIPTIONS + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(subs, f, ensure_ascii=False, indent=2)
    os.replace(tmp, SUBSCRIPTIONS)


def add_subscription(sub, device=""):
    """Store (or refresh) a browser PushSubscription, deduped by endpoint.
    `sub` is the object PushSubscription.toJSON() produces:
       {endpoint, keys:{p256dh, auth}}"""
    endpoint = (sub or {}).get("endpoint")
    keys = (sub or {}).get("keys") or {}
    if not endpoint or not keys.get("p256dh") or not keys.get("auth"):
        raise ValueError("subscription missing endpoint/keys")
    record = {
        "endpoint": endpoint,
        "keys": {"p256dh": keys["p256dh"], "auth": keys["auth"]},
        "device": str(device)[:80],
        "added": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    with _lock:
        subs = [s for s in load_subscriptions() if s.get("endpoint") != endpoint]
        subs.append(record)
        _save_subscriptions(subs)
    return len(subs)


def remove_subscription(endpoint):
    with _lock:
        subs = load_subscriptions()
        kept = [s for s in subs if s.get("endpoint") != endpoint]
        if len(kept) != len(subs):
            _save_subscriptions(kept)
        return len(subs) - len(kept)


# ------------------------------------------------------------------- sending
def broadcast(title, body, report=None, badge=None, path="./?view=stocking-report",
              ttl=DEFAULT_TTL):
    """Send one notification to every subscribed device.

    Returns {"sent": n, "pruned": m, "failed": k}. Dead subscriptions (the push
    service answers 404/410 — device removed the app or the subscription
    expired) are pruned automatically. Never raises: a push problem must not
    break the caller (the stocking run)."""
    from pywebpush import webpush, WebPushException

    if not keys_exist():
        print("[push] no VAPID key — skipping broadcast (run generate-keys first)")
        return {"sent": 0, "pruned": 0, "failed": 0}

    payload = {"title": title, "body": body, "path": path}
    if report is not None:
        payload["report"] = report
    if badge is not None:
        payload["badge"] = badge
    data = json.dumps(payload, ensure_ascii=False)

    subs = load_subscriptions()
    sent = failed = 0
    dead = []
    for s in subs:
        try:
            webpush(
                subscription_info={"endpoint": s["endpoint"], "keys": s["keys"]},
                data=data,
                vapid_private_key=PRIVATE_PEM,
                # fresh dict per call — pywebpush mutates it (adds exp/aud)
                vapid_claims={"sub": VAPID_SUB},
                ttl=ttl,
            )
            sent += 1
        except WebPushException as e:
            code = getattr(getattr(e, "response", None), "status_code", None)
            if code in (404, 410):
                dead.append(s["endpoint"])
            else:
                failed += 1
                print(f"[push] send failed ({code}): {e}")
        except Exception as e:  # noqa: BLE001 — never let a push break the caller
            failed += 1
            print(f"[push] unexpected send error: {e}")

    pruned = 0
    for endpoint in dead:
        pruned += remove_subscription(endpoint)
    result = {"sent": sent, "pruned": pruned, "failed": failed}
    print(f"[push] broadcast: {result} (of {len(subs)} subscriptions)")
    return result


# ----------------------------------------------------------------------- CLI
def _cli(argv):
    if not argv:
        print(__doc__)
        return 1
    cmd = argv[0]
    if cmd == "generate-keys":
        key = generate_keys(force="--force" in argv)
        print("VAPID keypair written to", PUSH_DIR)
        print("\nApplication server key (paste into index.html VAPID_PUBLIC_KEY):\n")
        print(key)
        return 0
    if cmd == "public-key":
        if not keys_exist():
            print("no VAPID key yet — run: python3 scripts/push_utils.py generate-keys")
            return 1
        print(application_server_key())
        return 0
    if cmd == "list":
        subs = load_subscriptions()
        print(f"{len(subs)} subscription(s):")
        for s in subs:
            print(f"  - {s.get('device','?'):20s} added {s.get('added','?')}  "
                  f"{s.get('endpoint','')[:60]}...")
        return 0
    if cmd == "test":
        msg = argv[1] if len(argv) > 1 else "Test push from the Uintas Mini 🏔️"
        r = broadcast(
            title="🏔️ Uintas test",
            body=msg,
            badge=1,
            report={
                "when": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "total": 0, "items": [], "test": True, "message": msg,
            },
        )
        return 0 if r["failed"] == 0 else 1
    print(f"unknown command: {cmd}\n")
    print(__doc__)
    return 1


if __name__ == "__main__":
    sys.exit(_cli(sys.argv[1:]))
