// JXA script to sync only flagged database entries to Apple Notes
// This script processes lakes where notes_needs_update = TRUE

function run() {
    const app = Application.currentApplication();
    app.includeStandardAdditions = true;

    const notes = Application("Notes");

    // --- Configuration ---
    const dbPath = "/Volumes/OLAF EXT/jedwoodx/repos/uintas/uinta_lakes.db";

    // --- Helper Functions ---
    function runQuery(query) {
        try {
            return app.doShellScript(`sqlite3 -newline '||' -separator '|' "${dbPath}" "${query}"`);
        } catch (e) {
            console.log(`Error running query: ${query}`);
            console.log(e);
            return "";
        }
    }

    function findLakeNote(folder, lakeName, letterNumber) {
        try {
            const notesInFolder = folder.notes();
            console.log(`Looking for lake ${letterNumber} note in folder with ${notesInFolder.length} notes`);
            
            // All possible note name variations
            const possibleNames = [
                `${lakeName} (${letterNumber})`,           // No emoji
                `${lakeName} (${letterNumber}) 🎣`,        // CAUGHT
                `${lakeName} (${letterNumber}) 🚫`         // OTHERS/NONE
            ];
            
            for (let i = 0; i < notesInFolder.length; i++) {
                const noteName = notesInFolder[i].name();
                console.log(`  Checking note: '${noteName}'`);
                
                for (const possibleName of possibleNames) {
                    if (noteName === possibleName) {
                        console.log(`  Found matching note: '${possibleName}'`);
                        return notesInFolder[i];
                    }
                }
            }
            console.log(`  No matching note found`);
            return null;
        } catch (e) {
            console.log(`Error in findLakeNote: ${e}`);
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

    // --- Process Each Flagged Lake ---
    flaggedLakes.forEach(letterNumber => {
        console.log(`Processing ${letterNumber}...`);

        // --- Fetch Data ---
        const lakeInfoQuery = `SELECT name, drainage, size_acres, max_depth_ft, elevation_ft, fish_species, fishing_pressure, dwr_notes, junesucker_notes, status, jed_notes, trip_reports FROM lakes WHERE letter_number = '${letterNumber}';`;
        const lakeInfoResult = runQuery(lakeInfoQuery);
        if (!lakeInfoResult) return;

        const [lakeName, drainageName, lakeSize, lakeDepth, lakeElevation, lakeSpecies, lakePressure, dwrNotes, junesuckerNotes, lakeStatus, jedNotes, tripReports] = lakeInfoResult.split('|');

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
        let lakeNote = findLakeNote(drainageFolder, lakeName, letterNumber);
        
        // Build the note name with current status emoji
        let titleEmoji = "";
        if (lakeStatus === "CAUGHT") {
            titleEmoji = " 🎣";
        } else if (lakeStatus === "OTHERS" || lakeStatus === "NONE") {
            titleEmoji = " 🚫";
        }
        const lakeNoteName = `${lakeName} (${letterNumber})${titleEmoji}`;

        if (lakeNote === null) {
            console.log(`Note not found. Creating new note: '${lakeNoteName}'`);
            const newNote = notes.Note({name: lakeNoteName});
            drainageFolder.notes.push(newNote);
            lakeNote = newNote;
        } else {
            console.log(`Found existing note: '${lakeNote.name()}'`);
            // Update the note name if emoji status changed
            if (lakeNote.name() !== lakeNoteName) {
                console.log(`Updating note name from '${lakeNote.name()}' to '${lakeNoteName}'`);
                lakeNote.name = lakeNoteName;
            }
        }

        // --- Build Bidirectional Note Body with Beautiful HTML Formatting ---
        // (emoji logic moved above)
        
        let noteBody = `<h1>${lakeName} (${letterNumber})${titleEmoji}</h1><br>`;
        
        // ABOVE ===== (Editable Section)
        if (lakeStatus) {
            noteBody += `<p><b>Status:</b> ${lakeStatus}</p>`;
        }
        
        // Always include Jed's Notes section (even if empty) for editing
        noteBody += "<br><h2>Jed's Notes</h2>";
        if (jedNotes) {
            noteBody += `<p>${jedNotes.replace(/\n/g, '<br>')}</p><br>`;
        } else {
            noteBody += "<p><i>Add your notes here...</i></p><br>";
        }
        
        // Always include Trip Reports section (even if empty) for editing
        noteBody += "<h2>Trip Reports</h2>";
        if (tripReports) {
            const trips = tripReports.split('\n');
            noteBody += "<ul>";
            trips.forEach(trip => {
                if (trip.trim()) {
                    noteBody += `<li>${trip}</li>`;
                }
            });
            noteBody += "</ul><br>";
        } else {
            noteBody += "<p><i>Add trip reports here...</i></p><br>";
        }
        
        // Add delimiter - use a clearer visual separator
        noteBody += "<p>═════════════════════════════════════</p>";
        
        // BELOW ===== (Auto-generated Section - Beautiful formatting restored)
        noteBody += "<ul>";
        noteBody += `<li><b>Drainage:</b> ${drainageName}</li>`;
        noteBody += `<li><b>Elevation:</b> ${lakeElevation || 'Unknown'} ft</li>`;
        noteBody += `<li><b>Size:</b> ${lakeSize || 'Unknown'} acres</li>`;
        noteBody += `<li><b>Max Depth:</b> ${lakeDepth || 'Unknown'} ft</li>`;
        noteBody += `<li><b>Fishing Pressure:</b> ${lakePressure || 'Unknown'}</li>`;
        noteBody += `<li><b>Fish Species:</b> ${lakeSpecies || 'Unknown'}</li>`;
        noteBody += "</ul><br>";

        if (junesuckerNotes) {
            noteBody += "<h2>Junesucker.com Notes</h2>";
            // Convert all ## headers to bold text with empty line above them
            let formattedJunesuckerNotes = junesuckerNotes.replace(/## (.*?):/g, '<br><br><b>$1:</b><br>');
            // Convert regular line breaks to <br> tags
            formattedJunesuckerNotes = formattedJunesuckerNotes.replace(/\n/g, '<br>');
            // Remove the leading <br><br> from the very first subheader (keep just one <br>)
            formattedJunesuckerNotes = formattedJunesuckerNotes.replace(/^<br><br><b>/, '<b>');
            noteBody += formattedJunesuckerNotes + "<br><br>";
        }

        noteBody += "<h2>Stocking Records</h2>";
        if (stockingRecords.length > 0 && stockingRecords[0].trim() !== "") {
            noteBody += "<ul>";
            stockingRecords.forEach(record => {
                if (record.trim() !== "") {
                    const [stockDate, species, quantity, fishLength] = record.split('|');
                    noteBody += `<li>${stockDate} - ${quantity} ${species}, ${fishLength}"</li>`;
                }
            });
            noteBody += "</ul><br>";
        } else {
            noteBody += "<p>No stocking records found.</p><br>";
        }

        if (dwrNotes) {
            noteBody += "<h2>DWR Notes</h2>";
            noteBody += `<p>${dwrNotes.replace(/\n/g, '<br>')}</p>`;
        }

        lakeNote.body = noteBody;
        updatedCount++;

        // --- Clear the flag ---
        const clearFlagQuery = `UPDATE lakes SET notes_needs_update = FALSE WHERE letter_number = '${letterNumber}';`;
        runQuery(clearFlagQuery);
        console.log(`Cleared update flag for ${letterNumber}`);
    });

    return `Updated ${updatedCount} lake notes.`;
}