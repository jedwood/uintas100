// JXA script to sync Apple Notes with *update tag back to database
// This script finds notes with *update, parses content above delimiter, updates database

function run() {
    const app = Application.currentApplication();
    app.includeStandardAdditions = true;

    const notes = Application("Notes");

    // --- Configuration ---
    const dbPath = "/Volumes/OLAF EXT/jedwoodx/repos/uintas/uinta_lakes.db";
    const logPath = "/Volumes/OLAF EXT/jedwoodx/repos/uintas/output/notes_sync.log";
    const mainFolderName = "Uintas 💯";

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

    function logMessage(message) {
        const timestamp = new Date().toISOString().replace('T', ' ').substring(0, 19);
        const logEntry = `[${timestamp}] ${message}\n`;
        console.log(message);
        
        try {
            app.doShellScript(`echo "${logEntry}" >> "${logPath}"`);
        } catch (e) {
            console.log(`Failed to write to log: ${e}`);
        }
    }

    function extractLakeIdentifier(noteName) {
        // Extract letter-number from note name like "Lake Name (A-42) 🎣" or "Lake Name (A-42)"
        const match = noteName.match(/\(([A-Z]+-?\d+)\)/);
        return match ? match[1] : null;
    }

    function parseNoteContent(noteBody) {
        // Parse the note content to extract editable sections above the delimiter
        const delimiterPattern = /═{5,}/;
        const parts = noteBody.split(delimiterPattern);
        
        if (parts.length < 2) {
            console.log("No delimiter found in note, skipping parse");
            return null;
        }

        const editableContent = parts[0];
        
        // Parse status - handle multiple formats
        let status = null;
        const statusMatch = editableContent.match(/<b>Status:<\/b>\s*([^<\n]+)/i) || 
                           editableContent.match(/Status:\s*([^\n<]+)/i) ||
                           editableContent.match(/>Status:([^<]+)</i);
        if (statusMatch) {
            status = statusMatch[1].trim().toUpperCase();
            // Validate status values
            if (!["CAUGHT", "NONE", "OTHERS"].includes(status)) {
                status = null;
            }
        }

        // Parse Jed's Notes - handle both <h2> and <span> formats
        let jedNotes = null;
        const jedNotesMatch = editableContent.match(/<h2>Jed's Notes<\/h2>(.*?)(?=<h2>|<div>═|$)/is) ||
                             editableContent.match(/Jed's Notes.*?<\/div>\s*<div>(.*?)<\/div>/is);
        if (jedNotesMatch) {
            let jedContent = jedNotesMatch[1];
            // Clean up HTML and extract text
            jedContent = jedContent.replace(/<br\s*\/?>/gi, '\n');
            jedContent = jedContent.replace(/<\/?div>/g, '\n');
            jedContent = jedContent.replace(/<\/?[^>]+>/g, '');
            jedContent = jedContent.replace(/\n+/g, '\n').trim();
            
            // Don't save placeholder text
            if (jedContent && jedContent !== "Add your notes here...") {
                jedNotes = jedContent;
            }
        }

        // Parse Trip Reports - handle both <h2> and <span> formats, and both div and ul formats
        let tripReports = null;
        const tripReportsMatch = editableContent.match(/<h2>Trip Reports<\/h2>(.*?)(?=<h2>|<div>═|$)/is) ||
                                editableContent.match(/Trip Reports.*?<\/div>(.*?)(?=<div>═|<div><b><span|$)/is);
        if (tripReportsMatch) {
            let tripContent = tripReportsMatch[1];
            
            // Handle both list format and paragraph format
            if (tripContent.includes('<li>')) {
                // Extract from list items
                const listItems = tripContent.match(/<li>(.*?)<\/li>/g);
                if (listItems) {
                    tripReports = listItems.map(item => {
                        let cleaned = item.replace(/<\/?li>/g, '');
                        cleaned = cleaned.replace(/<br\s*\/?>/gi, '\n');
                        cleaned = cleaned.replace(/<\/?[^>]+>/g, '');
                        cleaned = cleaned.replace(/\n+/g, '\n').trim();
                        return cleaned;
                    }).join('\n');
                }
            } else {
                // Extract from paragraph
                tripContent = tripContent.replace(/<br\s*\/?>/gi, '\n');
                tripContent = tripContent.replace(/<\/?div>/g, '\n');
                tripContent = tripContent.replace(/<\/?[^>]+>/g, '');
                tripContent = tripContent.replace(/\n+/g, '\n').trim();
                
                if (tripContent && tripContent !== "Add trip reports here...") {
                    tripReports = tripContent;
                }
            }
        }

        return { status, jedNotes, tripReports };
    }

    function isNoteInUintasFolder(note, mainFolder) {
        try {
            // Get the note's folder
            const noteFolder = note.container();
            
            // Check if it's directly in the main folder
            if (noteFolder.id() === mainFolder.id()) {
                return true;
            }
            
            // Check if it's in a subfolder of the main folder
            const parentFolder = noteFolder.container();
            if (parentFolder && parentFolder.id() === mainFolder.id()) {
                return true;
            }
            
            return false;
        } catch (e) {
            console.log(`Error checking note folder: ${e}`);
            return false;
        }
    }

    function findNotesWithUpdateHashtag(mainFolder) {
        const notesToUpdate = [];
        
        try {
            logMessage("Using Notes search to find all notes containing '*update'");
            
            // Use Notes' built-in search to find all notes containing *update
            // This is much more reliable than #update which Apple Notes converts to functional links
            const searchResults = notes.notes.whose({ body: { _contains: '*update' } })();
            
            logMessage(`Found ${searchResults.length} total notes containing '*update' across all folders`);
            
            // Filter to only notes within the Uintas folder structure
            for (let i = 0; i < searchResults.length; i++) {
                const note = searchResults[i];
                
                try {
                    if (isNoteInUintasFolder(note, mainFolder)) {
                        const letterNumber = extractLakeIdentifier(note.name());
                        if (letterNumber) {
                            logMessage(`Found *update in Uintas note: ${note.name()} (${letterNumber})`);
                            notesToUpdate.push({
                                note: note,
                                letterNumber: letterNumber,
                                noteName: note.name()
                            });
                        } else {
                            logMessage(`Found *update in Uintas note but no lake identifier: ${note.name()}`);
                        }
                    }
                } catch (e) {
                    console.log(`Error processing search result ${i}: ${e}`);
                }
            }
            
        } catch (e) {
            logMessage(`Error using Notes search: ${e}`);
            // Fallback to manual folder traversal if search fails
            logMessage("Falling back to manual folder search");
            return findNotesWithUpdateHashtagManual(mainFolder);
        }
        
        return notesToUpdate;
    }

    function findNotesWithUpdateHashtagManual(folder) {
        // Fallback method - the original implementation
        const notesToUpdate = [];
        
        try {
            // Check notes in this folder
            try {
                const notesInFolder = folder.notes();
                logMessage(`Manually checking ${notesInFolder.length} notes in folder: ${folder.name()}`);
                
                for (let i = 0; i < notesInFolder.length; i++) {
                    const note = notesInFolder[i];
                    try {
                        const noteBody = note.body();
                        
                        if (noteBody.includes('*update')) {
                            const letterNumber = extractLakeIdentifier(note.name());
                            logMessage(`Found *update in note: ${note.name()}, extracted: ${letterNumber}`);
                            if (letterNumber) {
                                notesToUpdate.push({
                                    note: note,
                                    letterNumber: letterNumber,
                                    noteName: note.name()
                                });
                            }
                        }
                    } catch (e) {
                        console.log(`Error reading note ${i}: ${e}`);
                    }
                }
            } catch (e) {
                console.log(`Error accessing notes in folder ${folder.name()}: ${e}`);
            }
            
            // Check subfolders recursively
            try {
                const subfolders = folder.folders();
                
                for (let i = 0; i < subfolders.length; i++) {
                    try {
                        const subfolder = subfolders[i];
                        const subfolderNotes = findNotesWithUpdateHashtagManual(subfolder);
                        notesToUpdate.push(...subfolderNotes);
                    } catch (e) {
                        console.log(`Error accessing subfolder ${i}: ${e}`);
                    }
                }
            } catch (e) {
                console.log(`Error accessing subfolders of ${folder.name()}: ${e}`);
            }
            
        } catch (e) {
            console.log(`Error searching folder: ${e}`);
        }
        
        return notesToUpdate;
    }

    // --- Main Logic ---
    logMessage("Starting Notes → Database sync");

    // Find the main folder
    let mainFolder;
    try {
        mainFolder = notes.folders.byName(mainFolderName);
        if (!mainFolder.exists()) {
            logMessage(`Main folder "${mainFolderName}" not found`);
            return "Main folder not found";
        }
    } catch (e) {
        logMessage(`Error accessing main folder: ${e}`);
        return "Error accessing main folder";
    }

    // Find all notes with #update hashtag
    const notesToUpdate = findNotesWithUpdateHashtag(mainFolder);
    
    if (notesToUpdate.length === 0) {
        logMessage("No notes found with *update tag");
        return "No notes to update";
    }

    logMessage(`Found ${notesToUpdate.length} notes with *update tag`);

    let successCount = 0;
    let errorCount = 0;

    // Process each note
    notesToUpdate.forEach(noteInfo => {
        const { note, letterNumber, noteName } = noteInfo;
        
        try {
            logMessage(`Processing note: ${noteName} (${letterNumber})`);
            
            // Parse the note content
            const noteBody = note.body();
            logMessage(`  Parsing note body for ${letterNumber}...`);
            const parsedData = parseNoteContent(noteBody);
            
            if (!parsedData) {
                logMessage(`  Could not parse content for ${letterNumber}`);
                errorCount++;
                return;
            }

            // Build update query
            const updateFields = [];
            const values = [];
            
            if (parsedData.status !== null) {
                updateFields.push('status = ?');
                values.push(parsedData.status);
                logMessage(`  Status: ${parsedData.status}`);
            }
            
            if (parsedData.jedNotes !== null) {
                updateFields.push('jed_notes = ?');
                values.push(parsedData.jedNotes);
                logMessage(`  Jed's Notes: ${parsedData.jedNotes.substring(0, 50)}...`);
            }
            
            if (parsedData.tripReports !== null) {
                updateFields.push('trip_reports = ?');
                values.push(parsedData.tripReports);
                logMessage(`  Trip Reports: ${parsedData.tripReports.substring(0, 50)}...`);
            }

            if (updateFields.length === 0) {
                logMessage(`  No parseable content found for ${letterNumber}`);
                // Still remove the *update tag even if no content was parsed
                const updatedBody = noteBody.replace(/\*update/g, '');
                note.body = updatedBody;
                errorCount++;
                return;
            }

            // Escape single quotes in values for SQL
            const escapedValues = values.map(val => val.replace(/'/g, "''"));
            
            // Build and execute update query
            const updateQuery = `UPDATE lakes SET ${updateFields.join(', ').replace(/\?/g, (match, index) => `'${escapedValues[updateFields.indexOf(match.replace(' = ?', ' = ?'))]}'`)} WHERE letter_number = '${letterNumber}';`;
            
            // Execute the actual query with proper escaping
            let actualQuery = `UPDATE lakes SET `;
            for (let i = 0; i < updateFields.length; i++) {
                if (i > 0) actualQuery += ', ';
                actualQuery += updateFields[i].replace(' = ?', ` = '${escapedValues[i]}'`);
            }
            actualQuery += ` WHERE letter_number = '${letterNumber}';`;
            
            const result = runQuery(actualQuery);
            
            // Remove *update tag from note
            const updatedBody = noteBody.replace(/\*update/g, '');
            note.body = updatedBody;
            
            logMessage(`  Successfully updated database for ${letterNumber}`);
            successCount++;
            
        } catch (e) {
            logMessage(`  Error processing ${letterNumber}: ${e}`);
            errorCount++;
        }
    });

    const summary = `Completed sync: ${successCount} successful, ${errorCount} errors`;
    logMessage(summary);
    
    return summary;
}