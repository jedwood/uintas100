use std::path::Path;
use std::process::Command;

pub struct ScriptResult {
    pub success: bool,
    pub stdout: String,
    pub stderr: String,
}

/// Run a Python script using the venv interpreter
pub fn run_python_script(project_dir: &Path, script_name: &str) -> ScriptResult {
    let python = project_dir.join("venv/bin/python3");
    let script = project_dir.join("scripts").join(script_name);

    // Fall back to system python if venv doesn't exist
    let python_path = if python.exists() {
        python
    } else {
        std::path::PathBuf::from("python3")
    };

    let scripts_dir = project_dir.join("scripts");

    match Command::new(&python_path)
        .arg(&script)
        .current_dir(&scripts_dir)
        .output()
    {
        Ok(output) => ScriptResult {
            success: output.status.success(),
            stdout: String::from_utf8_lossy(&output.stdout).to_string(),
            stderr: String::from_utf8_lossy(&output.stderr).to_string(),
        },
        Err(e) => ScriptResult {
            success: false,
            stdout: String::new(),
            stderr: format!("Failed to spawn process: {}", e),
        },
    }
}

/// Run the notes-to-db sync shell script
pub fn run_notes_sync_script(project_dir: &Path) -> ScriptResult {
    let script = project_dir.join("scripts/sync_notes_to_db.sh");

    match Command::new("bash")
        .arg(&script)
        .current_dir(project_dir)
        .output()
    {
        Ok(output) => ScriptResult {
            success: output.status.success(),
            stdout: String::from_utf8_lossy(&output.stdout).to_string(),
            stderr: String::from_utf8_lossy(&output.stderr).to_string(),
        },
        Err(e) => ScriptResult {
            success: false,
            stdout: String::new(),
            stderr: format!("Failed to spawn process: {}", e),
        },
    }
}

/// Run the db-to-notes push JXA script
pub fn run_notes_push_script(project_dir: &Path) -> ScriptResult {
    let script = project_dir.join("scripts/sync_db_to_notes_jxa.js");

    match Command::new("osascript")
        .arg(&script)
        .arg(project_dir.to_string_lossy().as_ref())
        .current_dir(project_dir)
        .output()
    {
        Ok(output) => ScriptResult {
            success: output.status.success(),
            stdout: String::from_utf8_lossy(&output.stdout).to_string(),
            stderr: String::from_utf8_lossy(&output.stderr).to_string(),
        },
        Err(e) => ScriptResult {
            success: false,
            stdout: String::new(),
            stderr: format!("Failed to spawn process: {}", e),
        },
    }
}
