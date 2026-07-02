// JXA script to sync only flagged database entries to Apple Notes
// This script processes lakes where notes_needs_update = TRUE
//
// WIPE-SAFE: Apple Notes has no surgical edit — writing a note replaces its whole
// body. So for an EXISTING note we do NOT rebuild the user-editable section from
// the database (that clobbered un-captured trip reports / notes). Instead we read
// the live note, preserve everything ABOVE the ═══ delimiter verbatim, and rebuild
// the body as: preserved-above + fresh delimiter + DB-regenerated auto-data. Only
// the <h1> title emoji is refreshed. Safety nets: the old body is backed up before
// any overwrite, and a note with no delimiter is skipped rather than overwritten.
//
// Hard-won rules (2026-07-01 incident):
//  - Wait for iCloud to settle before reading (see settle window below): reading
//    a stale replica and rewriting it makes iCloud concatenate both versions.
//  - The title round-trips as a <div><b><span 24px> line, NOT <h1> — replace that
//    line, never blindly prepend a fresh <h1> (doubled every title).
//  - NEVER set note.name after setting body — the body's first line already
//    becomes the name; setting both doubled the title text.
//  - Skip notes that already look conflict-merged (2+ delimiters / doubled title).
// Dry run (preview, no writes):  UINTAS_DRYRUN=1 osascript scripts/sync_db_to_notes_jxa.js

ObjC.import('Foundation');

function run() {
    const app = Application.currentApplication();
    app.includeStandardAdditions = true;

    const notes = Application("Notes");

    // --- Configuration ---
    // Accept project dir as CLI argument, fall back to default
    const args = $.NSProcessInfo.processInfo.arguments;
    const argCount = args.count;
    const defaultProjectDir = "/Volumes/OLAF-EXT/jedwoodx/repos/uintas";
    const projectDir = argCount > 4 ? ObjC.unwrap(args.objectAtIndex(4)) : defaultProjectDir;
    const dbPath = projectDir + "/uinta_lakes.db";

    // Dry run: preview only, never write notes or clear flags.
    const dryRun = ObjC.unwrap($.NSProcessInfo.processInfo.environment.objectForKey('UINTAS_DRYRUN')) === '1';
    const BACKUP_DIR = projectDir + "/logs/notes_backups";
    if (dryRun) console.log("=== DRY RUN — no notes will be modified ===");

    // --- iCloud settle window ---
    // 2026-07-01 incident: this script launched Notes and immediately read a
    // STALE local replica (the user's recent edits hadn't synced down yet), then
    // rewrote notes from it. iCloud saw two conflicting edits and "resolved" by
    // concatenating both versions into one note. There is no scriptable
    // "sync now / sync done" API, so the mitigation is: make sure Notes is
    // running, then give iCloud time to pull before reading anything.
    // Override with UINTAS_SYNC_SETTLE=<seconds> (0 skips, e.g. when Notes has
    // already been open and syncing for a while).
    const settleRaw = ObjC.unwrap($.NSProcessInfo.processInfo.environment.objectForKey('UINTAS_SYNC_SETTLE'));
    const settleSecs = settleRaw !== undefined && settleRaw !== null ? parseInt(settleRaw, 10) || 0 : 30;
    if (settleSecs > 0) {
        notes.activate();
        console.log(`Waiting ${settleSecs}s for Notes to sync with iCloud (UINTAS_SYNC_SETTLE=0 to skip)...`);
        delay(settleSecs);
    }

    // --- Helper Functions ---
    function runQuery(query) {
        try {
            // Use a unique separator that won't appear in content: ASCII 30 (Record Separator)
            return app.doShellScript(`sqlite3 -newline '||' -separator '' "${dbPath}" "${query}"`);
        } catch (e) {
            console.log(`Error running query: ${query}`);
            console.log(e);
            return "";
        }
    }

    function backupNoteBody(letterNumber, body) {
        // Save a note's current HTML before we overwrite it — insurance against
        // any regression in the preserve-above logic.
        try {
            app.doShellScript("mkdir -p " + JSON.stringify(BACKUP_DIR));
            const stamp = new Date().toISOString().replace(/[:.]/g, '-');
            const safeLn = String(letterNumber).replace(/[^A-Za-z0-9_-]/g, '_');
            const path = BACKUP_DIR + "/" + safeLn + "-" + stamp + ".html";
            $.NSString.stringWithString(body).writeToFileAtomicallyEncodingError(
                path, true, $.NSUTF8StringEncoding, null);
            console.log("  Backed up old note body -> " + path);
            return path;
        } catch (e) {
            console.log("  WARNING: backup failed for " + letterNumber + ": " + e);
            return null;
        }
    }

    function findLakeNote(letterNumber, notes) {
        // Match on the unique designation token across ALL folders: a note whose
        // name contains "(LETTER-NUMBER)" (named lakes) or is exactly the
        // designation (unnamed lakes), with an optional trailing status emoji.
        //
        // Folder-agnostic ON PURPOSE. Apple Notes here has duplicate drainage
        // folders (e.g. two "Duchesne River Drainage"), and some notes have
        // renamed / typo'd title prefixes (e.g. "QUARTER CORNER LG103 (G-103)").
        // Requiring an exact name in a specific folder missed those and would
        // CREATE duplicates. The designation is globally unique, so matching it
        // anywhere resolves the real note and we UPDATE it in place.
        const esc = letterNumber.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
        const re = new RegExp('(^|\\()' + esc + '(\\)|\\s|$)');
        console.log(`Searching for note matching (${letterNumber})...`);
        let results;
        try {
            results = notes.notes.whose({ name: { _contains: letterNumber } })();
        } catch (e) {
            console.log(`  Search API failed for ${letterNumber}: ${e}`);
            return null;
        }
        const matches = [];
        for (let i = 0; i < results.length; i++) {
            let noteName;
            try { noteName = results[i].name(); } catch (e) { continue; }
            if (re.test(noteName)) matches.push({ note: results[i], name: noteName });
        }
        if (matches.length === 0) {
            console.log(`  No existing note found for ${letterNumber}`);
            return null;
        }
        if (matches.length > 1) {
            // e.g. "Lower Lyman (G-25)" AND "Little Lyman (G-25)" both exist.
            // Updating the first arbitrary one may hit the wrong note.
            console.log(`  WARNING: ${matches.length} notes match (${letterNumber}): ` +
                matches.map(m => `'${m.name}'`).join(', ') + ` — using '${matches[0].name}'.`);
        }
        console.log(`  Matched existing note: '${matches[0].name}'`);
        return matches[0].note;
    }

    // --- Find Lakes Needing Updates ---
    const flaggedLakesQuery = `SELECT letter_number FROM lakes WHERE notes_needs_update = TRUE;`;
    const flaggedLakesResult = runQuery(flaggedLakesQuery);

    if (!flaggedLakesResult || flaggedLakesResult.trim() === "") {
        console.log("No lakes flagged for updates.");
        return "No updates needed.";
    }

    const flaggedLakes = flaggedLakesResult.split('||').filter(lake => lake.trim() !== "");
    console.log(`Found ${flaggedLakes.length} lakes needing updates: ${flaggedLakes.join(', ')}`);

    let updatedCount = 0;
    let skippedCount = 0;

    // --- Process Each Flagged Lake ---
    flaggedLakes.forEach(letterNumber => {
        console.log(`Processing ${letterNumber}...`);

        // --- Fetch Data ---
        const lakeInfoQuery = `SELECT name, drainage, size_acres, max_depth_ft, elevation_ft, fish_species, fishing_pressure, dwr_notes, junesucker_notes, status, jed_notes, trip_reports, no_fish FROM lakes WHERE letter_number = '${letterNumber}';`;
        const lakeInfoResult = runQuery(lakeInfoQuery);
        if (!lakeInfoResult) return;

        const [lakeName, drainageName, lakeSize, lakeDepth, lakeElevation, lakeSpecies, lakePressure, dwrNotes, junesuckerNotes, lakeStatus, jedNotes, tripReports, noFish] = lakeInfoResult.split('');


        const stockingQuery = `SELECT stock_date, species, quantity, length FROM stocking_records WHERE lake_id = (SELECT id FROM lakes WHERE letter_number = '${letterNumber}') ORDER BY stock_date DESC;`;
        const stockingRecordsResult = runQuery(stockingQuery);
        const stockingRecords = stockingRecordsResult ? stockingRecordsResult.split('||') : [];

        // --- Create/Find Folders and Notes ---
        const mainFolderName = "Uintas 💯";
        let mainFolder = notes.folders.byName(mainFolderName);
        if (!mainFolder.exists()) {
            const newFolder = notes.Folder({name: mainFolderName});
            notes.folders.push(newFolder);
            mainFolder = newFolder;
        }

        let drainageFolder = mainFolder.folders.byName(drainageName);
        if (!drainageFolder.exists()) {
            const newFolder = notes.Folder({name: drainageName});
            mainFolder.folders.push(newFolder);
            drainageFolder = newFolder;
        }

        // Find existing note by its unique designation, across all folders.
        let lakeNote = findLakeNote(letterNumber, notes);

        // Build the note name with current status emoji
        let titleEmoji = "";
        if (noFish === "1" || noFish === "true") {
            titleEmoji = " 🚫";  // No fish lakes get prohibition emoji
        } else if (lakeStatus === "CAUGHT") {
            titleEmoji = " 🎣";
        } else if (lakeStatus === "OTHERS") {
            titleEmoji = " 👥🎣";  // others have caught here (matches the in-app icon)
        } else if (lakeStatus === "NONE") {
            titleEmoji = " ✖️";
        }

        // Create proper note name (no parentheses if no lake name)
        const baseName = lakeName && lakeName.trim() ? `${lakeName.trim()} (${letterNumber})` : letterNumber;
        const lakeNoteName = `${baseName}${titleEmoji}`;
        const freshTitle = `<h1>${baseName}${titleEmoji}</h1>`;

        // --- Auto-generated section (BELOW the ═══ delimiter) — always rebuilt from the DB ---
        const DELIMITER = "<p>═════════════════════════════════════</p>";
        let autoBelow = "<ul>";
        autoBelow += `<li><b>Drainage:</b> ${drainageName}</li>`;
        autoBelow += `<li><b>Elevation:</b> ${lakeElevation || 'Unknown'} ft</li>`;
        autoBelow += `<li><b>Size:</b> ${lakeSize || 'Unknown'} acres</li>`;
        autoBelow += `<li><b>Max Depth:</b> ${lakeDepth || 'Unknown'} ft</li>`;
        autoBelow += `<li><b>Fishing Pressure:</b> ${lakePressure || 'Unknown'}</li>`;
        autoBelow += `<li><b>Fish Species:</b> ${lakeSpecies || 'Unknown'}</li>`;
        autoBelow += "</ul><br>";
        if (junesuckerNotes) {
            autoBelow += "<h2>Junesucker.com Notes</h2>";
            let fj = junesuckerNotes.replace(/## (.*?):/g, '<br><br><b>$1:</b><br>');
            fj = fj.replace(/\n/g, '<br>');
            fj = fj.replace(/^<br><br><b>/, '<b>');
            autoBelow += fj + "<br><br>";
        }
        autoBelow += "<h2>Stocking Records</h2>";
        if (stockingRecords.length > 0 && stockingRecords[0].trim() !== "") {
            autoBelow += "<ul>";
            stockingRecords.forEach(record => {
                if (record.trim() !== "") {
                    const [stockDate, species, quantity, fishLength] = record.split('');
                    autoBelow += `<li>${stockDate} - ${quantity} ${species}, ${fishLength}"</li>`;
                }
            });
            autoBelow += "</ul><br>";
        } else {
            autoBelow += "<p>No stocking records found.</p><br>";
        }
        if (dwrNotes) {
            autoBelow += "<h2>DWR Notes</h2>";
            autoBelow += `<p>${dwrNotes.replace(/\n/g, '<br>')}</p>`;
        }

        // --- Editable section (ABOVE the ═══ delimiter) ---
        let aboveEditable;

        if (lakeNote === null) {
            // Brand-new note: no user content exists yet, so build the editable
            // section from the DB (nothing to preserve).
            if (dryRun) {
                console.log(`  [dry-run] would CREATE note '${lakeNoteName}'`);
                return;
            }
            console.log(`Note not found. Creating new note: '${lakeNoteName}'`);
            const newNote = notes.Note({name: lakeNoteName});
            drainageFolder.notes.push(newNote);
            lakeNote = newNote;

            aboveEditable = `${freshTitle}<br>`;
            aboveEditable += `<p><b>Status:</b> ${lakeStatus || ''}</p>`;
            aboveEditable += "<br><h2>Jed's Notes</h2>";
            if (jedNotes) {
                aboveEditable += (jedNotes.includes('<br>') || jedNotes.includes('<i>') || jedNotes.includes('<b>') || jedNotes.includes('<div>'))
                    ? `<div>${jedNotes}</div><br>`
                    : `<p>${jedNotes.replace(/\n/g, '<br>')}</p><br>`;
            } else {
                aboveEditable += "<p><i>Add your notes here...</i></p><br>";
            }
            aboveEditable += "<h2>Trip Reports</h2>";
            if (tripReports) {
                if (tripReports.includes('<ul') && tripReports.includes('<li>')) {
                    aboveEditable += tripReports + "<br>";
                } else {
                    aboveEditable += `<ul class="Apple-dash-list">`;
                    tripReports.split('\n').forEach(trip => { if (trip.trim()) aboveEditable += `<li>${trip}</li>`; });
                    aboveEditable += "</ul><br>";
                }
            } else {
                aboveEditable += "<p><i>Add trip reports here...</i></p><br>";
            }
        } else {
            // EXISTING note: preserve everything above the ═══ delimiter VERBATIM
            // (the user's Status / Jed's Notes / Trip Reports). Only refresh the
            // <h1> title emoji. Refuse to touch a note that has no delimiter.
            console.log(`Found existing note: '${lakeNote.name()}'`);
            const oldBody = lakeNote.body();
            const delimMatch = oldBody.match(/═{5,}/);
            if (!delimMatch) {
                console.log(`  SKIP ${letterNumber}: no ═ delimiter in note; refusing to overwrite (flag left set).`);
                skippedCount++;
                return;  // continue; do NOT clear the flag
            }
            // Sanity guard: a body with 2+ delimiters or a doubled title line is
            // an unresolved iCloud conflict-merge (or leftover damage). Rewriting
            // it would bake the duplication in — skip and leave the flag set.
            const delimCount = (oldBody.match(/═{5,}/g) || []).length;
            const oldLines = oldBody.split('\n');
            const doubledTitle = oldLines.length > 1 &&
                oldLines[0].indexOf('font-size: 24px') !== -1 &&
                oldLines[1].indexOf('font-size: 24px') !== -1;
            if (delimCount > 1 || doubledTitle) {
                console.log(`  SKIP ${letterNumber}: note looks conflict-merged (delims=${delimCount}, doubledTitle=${doubledTitle}); fix the note manually, flag left set.`);
                skippedCount++;
                return;
            }
            // Everything before the delimiter run, minus a dangling open tag that
            // wrapped the delimiter paragraph.
            let above = oldBody.slice(0, delimMatch.index).replace(/<[a-zA-Z][^>]*>\s*$/, '');
            // Refresh only the title line; leave Status / Jed's / Trip verbatim.
            // The title we wrote as <h1> comes back from Notes round-tripped as
            // <div><b><span style="font-size: 24px">…</span></b></div>, so match
            // either form; only prepend when there is genuinely no title line.
            const aboveLines = above.split('\n');
            const firstIsTitle = /<h1[\s\S]*?<\/h1>/i.test(aboveLines[0]) ||
                aboveLines[0].indexOf('font-size: 24px') !== -1;
            if (firstIsTitle) {
                aboveLines[0] = freshTitle;
                above = aboveLines.join('\n');
            } else {
                above = freshTitle + above;
            }
            aboveEditable = above;

            if (dryRun) {
                console.log(`  [dry-run] would UPDATE '${lakeNote.name()}' — preserve ${aboveEditable.length} chars above ═, refresh auto-data. No write.`);
                return;
            }
            backupNoteBody(letterNumber, oldBody);
        }

        // Setting the body is enough: Apple Notes derives the note's name from
        // the first line. ALSO setting .name here corrupted titles (the name
        // setter re-edits the first line, doubling the text) — never set both.
        lakeNote.body = `${aboveEditable}${DELIMITER}${autoBelow}`;
        updatedCount++;

        // --- Clear the flag ---
        const clearFlagQuery = `UPDATE lakes SET notes_needs_update = FALSE WHERE letter_number = '${letterNumber}';`;
        runQuery(clearFlagQuery);
        console.log(`Cleared update flag for ${letterNumber}`);
    });

    const summary = `Updated ${updatedCount} lake notes` + (skippedCount ? `, skipped ${skippedCount} (no delimiter)` : "") + (dryRun ? " [dry run]" : "") + ".";
    console.log(summary);
    return summary;
}
