// JXA script to create sample lake notes with advanced formatting and improved update logic.

function run() {
    const app = Application.currentApplication();
    app.includeStandardAdditions = true;

    const notes = Application("Notes");

    // --- Configuration ---
    const dbPath = "/Volumes/OLAF EXT/jedwoodx/repos/uintas/uinta_lakes.db";
    const lakeLetterNumbers = ["Z-1", "Z-16"]; // Butterfly and Echo

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

    function findNoteByName(folder, name) {
        const notesInFolder = folder.notes();
        for (let i = 0; i < notesInFolder.length; i++) {
            if (notesInFolder[i].name() === name) {
                return notesInFolder[i];
            }
        }
        return null;
    }

    // --- Process Each Lake ---
    lakeLetterNumbers.forEach(letterNumber => {
        console.log(`Processing ${letterNumber}...`);

        // --- Fetch Data ---
        const lakeInfoQuery = `SELECT name, drainage, size_acres, max_depth_ft, elevation_ft, fish_species, fishing_pressure, dwr_notes, junesucker_notes, status, jed_notes FROM lakes WHERE letter_number = '${letterNumber}';`;
        const lakeInfoResult = runQuery(lakeInfoQuery);
        if (!lakeInfoResult) return;

        const [lakeName, drainageName, lakeSize, lakeDepth, lakeElevation, lakeSpecies, lakePressure, dwrNotes, junesuckerNotes, lakeStatus, jedNotes] = lakeInfoResult.split('|');

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

        const lakeNoteName = `${lakeName} (${letterNumber})`;
        let lakeNote = findNoteByName(drainageFolder, lakeNoteName);

        if (lakeNote === null) {
            console.log(`Note '${lakeNoteName}' not found. Creating new note.`);
            const newNote = notes.Note({name: lakeNoteName});
            drainageFolder.notes.push(newNote);
            lakeNote = newNote;
        } else {
            console.log(`Note '${lakeNoteName}' found. Updating existing note.`);
        }

        // --- Build Note Body ---
        let noteBody = `<h1>${lakeName} (${letterNumber})</h1><br>`;
        
        noteBody += "<ul>";
        noteBody += `<li><b>Drainage:</b> ${drainageName}</li>`;
        noteBody += `<li><b>Elevation:</b> ${lakeElevation || 'Unknown'} ft</li>`;
        noteBody += `<li><b>Size:</b> ${lakeSize || 'Unknown'} acres</li>`;
        noteBody += `<li><b>Max Depth:</b> ${lakeDepth || 'Unknown'} ft</li>`;
        noteBody += `<li><b>Fishing Pressure:</b> ${lakePressure || 'Unknown'}</li>`;
        noteBody += `<li><b>Fish Species:</b> ${lakeSpecies || 'Unknown'}</li>`;
        if (lakeStatus) {
            noteBody += `<li><b>Status:</b> ${lakeStatus}</li>`;
        }
        noteBody += "</ul><br>";

        if (jedNotes) {
            noteBody += "<h2>Jed's Notes</h2><br>";
            noteBody += `<p>${jedNotes.replace(/\n/g, '<br>')}</p><br>`;
        }

        if (junesuckerNotes) {
            noteBody += "<h2>Junesucker.com Notes</h2><br>";
            // Convert all ## headers to bold text with empty line above them
            let formattedJunesuckerNotes = junesuckerNotes.replace(/## (.*?):/g, '<br><br><b>$1:</b><br>');
            // Convert regular line breaks to <br> tags
            formattedJunesuckerNotes = formattedJunesuckerNotes.replace(/\n/g, '<br>');
            // Remove the leading <br><br> from the very first subheader (keep just one <br>)
            formattedJunesuckerNotes = formattedJunesuckerNotes.replace(/^<br><br><b>/, '<b>');
            noteBody += formattedJunesuckerNotes + "<br>";
        }

        noteBody += "<br><h2>Stocking Records</h2><br>";
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
            noteBody += "<h2>DWR Notes</h2><br>";
            noteBody += `<p>${dwrNotes.replace(/\n/g, '<br>')}</p>`;
        }

        lakeNote.body = noteBody;
    });

    return "JXA script for advanced notes finished.";
}
