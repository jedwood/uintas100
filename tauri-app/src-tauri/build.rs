use std::path::Path;

/// The frontend is embedded into the binary at compile time by
/// `tauri::generate_context!()`, but `tauri_build::build()` only emits
/// rerun-if-changed for tauri.conf.json and capabilities/ — NOT for the
/// frontendDist directory. Without the emits below, editing
/// `frontend/index.html` alone leaves the crate looking unchanged, so cargo
/// skips the recompile and silently ships a stale UI. (Bit us once: a new
/// schedule-interval option only shipped because an unrelated .rs file
/// happened to change in the same build.)
fn watch(path: &Path) {
    println!("cargo:rerun-if-changed={}", path.display());
    if let Ok(entries) = std::fs::read_dir(path) {
        for entry in entries.flatten() {
            let p = entry.path();
            if p.is_dir() {
                watch(&p);
            } else {
                println!("cargo:rerun-if-changed={}", p.display());
            }
        }
    }
}

fn main() {
    watch(Path::new("../frontend"));
    tauri_build::build()
}
