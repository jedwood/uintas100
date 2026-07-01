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

    function findLakeNote(folder, lakeName, letterNumber, notes) {
        try {
            // Create proper note name (no parentheses if no lake name)
            const baseName = lakeName && lakeName.trim() ? `${lakeName.trim()} (${letterNumber})` : letterNumber;

            console.log(`Searching for lake ${letterNumber} using Apple Notes search API`);

            // Use Notes' built-in search to find notes containing the letter-number
            // This is much more efficient than looping through all notes in folder
            let searchResults;
            try {
                searchResults = notes.notes.whose({ name: { _contains: letterNumber } })();
                console.log(`  Found ${searchResults.length} notes containing '${letterNumber}' across all folders`);
            } catch (e) {
                console.log(`  Search API failed, falling back to folder iteration: ${e}`);
                return findLakeNoteFallback(folder, lakeName, letterNumber);
            }

            // All possible note name variations
            const possibleNames = [
                baseName,                    // No emoji
                `${baseName} 🎣`,           // CAUGHT
                `${baseName} 👥🎣`,         // OTHERS (matches the in-app icon)
                `${baseName} ✖️`,           // NONE (and legacy OTHERS notes)
                `${baseName} 🚫`            // NO_FISH
            ];

            // Filter search results to only notes in our target folder with exact title match
            for (let i = 0; i < searchResults.length; i++) {
                const note = searchResults[i];

                try {
                    // Check if note is in the target folder
                    const noteFolder = note.container();
                    if (noteFolder.id() === folder.id()) {
                        const noteName = note.name();
                        console.log(`  Checking note in correct folder: '${noteName}'`);

                        // Check for exact title match
                        for (const possibleName of possibleNames) {
                            if (noteName === possibleName) {
                                console.log(`  Found exact match: '${possibleName}'`);
                                return note;
                            }
                        }
                    }
                } catch (e) {
                    console.log(`  Error checking search result ${i}: ${e}`);
                }
            }

            console.log(`  No matching note found for ${letterNumber}`);
            return null;
        } catch (e) {
            console.log(`Error in findLakeNote: ${e}`);
            return findLakeNoteFallback(folder, lakeName, letterNumber);
        }
    }

    function findLakeNoteFallback(folder, lakeName, letterNumber) {
        // Fallback to original method if search API fails
        try {
            console.log(`  Using fallback method for ${letterNumber}`);
            const notesInFolder = folder.notes();

            // Create proper note name (no parentheses if no lake name)
            const baseName = lakeName && lakeName.trim() ? `${lakeName.trim()} (${letterNumber})` : letterNumber;

            // All possible note name variations
            const possibleNames = [
                baseName,                    // No emoji
                `${baseName} 🎣`,           // CAUGHT
                `${baseName} 👥🎣`,         // OTHERS (matches the in-app icon)
                `${baseName} ✖️`,           // NONE (and legacy OTHERS notes)
                `${baseName} 🚫`            // NO_FISH
            ];

            for (let i = 0; i < notesInFolder.length; i++) {
                const noteName = notesInFolder[i].name();

                for (const possibleName of possibleNames) {
                    if (noteName === possibleName) {
                        console.log(`  Found matching note (fallback): '${possibleName}'`);
                        return notesInFolder[i];
                    }
                }
            }
            return null;
        } catch (e) {
            console.log(`Error in fallback search: ${e}`);
            return null;
        }
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

        // Find existing note (searches all possible emoji variations)
        let lakeNote = findLakeNote(drainageFolder, lakeName, letterNumber, notes);

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
            // Everything before the delimiter run, minus a dangling open tag that
            // wrapped the delimiter paragraph.
            let above = oldBody.slice(0, delimMatch.index).replace(/<[a-zA-Z][^>]*>\s*$/, '');
            // Refresh only the title line; leave Status / Jed's / Trip verbatim.
            above = /<h1[\s\S]*?<\/h1>/i.test(above)
                ? above.replace(/<h1[\s\S]*?<\/h1>/i, freshTitle)
                : freshTitle + above;
            aboveEditable = above;

            if (dryRun) {
                console.log(`  [dry-run] would UPDATE '${lakeNote.name()}' — preserve ${aboveEditable.length} chars above ═, refresh auto-data. No write.`);
                return;
            }
            backupNoteBody(letterNumber, oldBody);
        }

        lakeNote.body = `${aboveEditable}${DELIMITER}${autoBelow}`;
        lakeNote.name = lakeNoteName;
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
