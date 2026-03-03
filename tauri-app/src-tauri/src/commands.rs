use crate::scheduler::{save_config, ScheduleConfig, SchedulerState};
use crate::scripts;
use serde::Serialize;
use std::sync::{Arc, Mutex};
use tauri::State;

#[derive(Debug, Serialize)]
pub struct RunResult {
    pub success: bool,
    pub stdout: String,
    pub stderr: String,
}

#[derive(Debug, Serialize)]
pub struct AppStatus {
    pub stocking: TaskStatus,
    pub notes_sync: TaskStatus,
    pub db_size_bytes: u64,
    pub db_modified: Option<String>,
}

#[derive(Debug, Serialize)]
pub struct TaskStatus {
    pub last_run: String,
    pub last_success: bool,
    pub last_error: Option<String>,
    pub next_run: Option<String>,
    pub enabled: bool,
    pub interval_hours: u64,
}

// -- Script runners --
// These run blocking scripts on a background thread to avoid blocking the main thread.

#[tauri::command]
pub async fn run_stocking_update(
    state: State<'_, Arc<Mutex<SchedulerState>>>,
    app: tauri::AppHandle,
) -> Result<RunResult, String> {
    let project_dir = {
        let state_guard = state.lock().map_err(|e| e.to_string())?;
        state_guard.project_dir.clone()
    };

    let result = tauri::async_runtime::spawn_blocking(move || {
        let fetch = scripts::run_python_script(&project_dir, "fetch_latest_stocking.py");
        if !fetch.success {
            return RunResult {
                success: false,
                stdout: fetch.stdout,
                stderr: fetch.stderr,
            };
        }
        let update = scripts::run_python_script(&project_dir, "update_stocking.py");
        RunResult {
            success: update.success,
            stdout: format!("{}\n---\n{}", fetch.stdout, update.stdout),
            stderr: format!("{}{}", fetch.stderr, update.stderr),
        }
    })
    .await
    .map_err(|e| e.to_string())?;

    // Update state
    {
        let mut state_guard = state.lock().map_err(|e| e.to_string())?;
        state_guard.config.stocking_update.last_run = chrono::Utc::now();
        state_guard.config.stocking_update.last_success = result.success;
        state_guard.config.stocking_update.last_error = if result.success {
            None
        } else {
            Some(result.stderr.clone())
        };
        save_config(&app, &state_guard.config);
    }

    if !result.success {
        send_failure_notification(&app, "Stocking Update Failed", &result.stderr);
    }

    Ok(result)
}

#[tauri::command]
pub async fn run_notes_sync(
    state: State<'_, Arc<Mutex<SchedulerState>>>,
    app: tauri::AppHandle,
) -> Result<RunResult, String> {
    let project_dir = {
        let state_guard = state.lock().map_err(|e| e.to_string())?;
        state_guard.project_dir.clone()
    };

    let result = tauri::async_runtime::spawn_blocking(move || {
        let r = scripts::run_notes_sync_script(&project_dir);
        RunResult {
            success: r.success,
            stdout: r.stdout,
            stderr: r.stderr,
        }
    })
    .await
    .map_err(|e| e.to_string())?;

    {
        let mut state_guard = state.lock().map_err(|e| e.to_string())?;
        state_guard.config.notes_sync.last_run = chrono::Utc::now();
        state_guard.config.notes_sync.last_success = result.success;
        state_guard.config.notes_sync.last_error = if result.success {
            None
        } else {
            Some(result.stderr.clone())
        };
        save_config(&app, &state_guard.config);
    }

    if !result.success {
        send_failure_notification(&app, "Notes Sync Failed", &result.stderr);
    }

    Ok(result)
}

#[tauri::command]
pub async fn run_notes_push(
    state: State<'_, Arc<Mutex<SchedulerState>>>,
) -> Result<RunResult, String> {
    let project_dir = {
        let state_guard = state.lock().map_err(|e| e.to_string())?;
        state_guard.project_dir.clone()
    };

    let result = tauri::async_runtime::spawn_blocking(move || {
        let r = scripts::run_notes_push_script(&project_dir);
        RunResult {
            success: r.success,
            stdout: r.stdout,
            stderr: r.stderr,
        }
    })
    .await
    .map_err(|e| e.to_string())?;

    Ok(result)
}

// -- Schedule management --

#[tauri::command]
pub async fn get_schedule(
    state: State<'_, Arc<Mutex<SchedulerState>>>,
) -> Result<ScheduleConfig, String> {
    let state_guard = state.lock().map_err(|e| e.to_string())?;
    Ok(state_guard.config.clone())
}

#[tauri::command]
pub async fn set_schedule(
    state: State<'_, Arc<Mutex<SchedulerState>>>,
    app: tauri::AppHandle,
    config: ScheduleConfig,
) -> Result<(), String> {
    let mut state_guard = state.lock().map_err(|e| e.to_string())?;
    state_guard.config = config;
    save_config(&app, &state_guard.config);
    Ok(())
}

// -- Log reading --

#[tauri::command]
pub async fn read_log(
    state: State<'_, Arc<Mutex<SchedulerState>>>,
    log_name: String,
) -> Result<String, String> {
    let log_path = {
        let state_guard = state.lock().map_err(|e| e.to_string())?;
        match log_name.as_str() {
            "stocking" => state_guard.project_dir.join("logs/stocking_update.log"),
            "notes" => state_guard.project_dir.join("logs/notes_sync.log"),
            "fetch" => state_guard.project_dir.join("stocking_fetch.log"),
            _ => return Err(format!("Unknown log: {}", log_name)),
        }
    };

    match std::fs::read_to_string(&log_path) {
        Ok(content) => {
            let lines: Vec<&str> = content.lines().collect();
            let start = lines.len().saturating_sub(200);
            Ok(lines[start..].join("\n"))
        }
        Err(e) => {
            if e.kind() == std::io::ErrorKind::NotFound {
                Ok(String::from("(no log file found)"))
            } else {
                Err(format!("Error reading log: {}", e))
            }
        }
    }
}

// -- Status --

#[tauri::command]
pub async fn get_status(
    state: State<'_, Arc<Mutex<SchedulerState>>>,
) -> Result<AppStatus, String> {
    let state_guard = state.lock().map_err(|e| e.to_string())?;
    let config = &state_guard.config;

    let db_path = state_guard.project_dir.join("uinta_lakes.db");
    let (db_size_bytes, db_modified) = match std::fs::metadata(&db_path) {
        Ok(meta) => {
            let modified = meta
                .modified()
                .ok()
                .map(|t| {
                    let dt: chrono::DateTime<chrono::Utc> = t.into();
                    dt.format("%Y-%m-%d %H:%M:%S UTC").to_string()
                });
            (meta.len(), modified)
        }
        Err(_) => (0, None),
    };

    let stocking_next = if config.stocking_update.enabled {
        Some(
            (config.stocking_update.last_run
                + chrono::Duration::hours(config.stocking_update.interval_hours as i64))
            .format("%Y-%m-%d %H:%M:%S UTC")
            .to_string(),
        )
    } else {
        None
    };

    let notes_next = if config.notes_sync.enabled {
        Some(
            (config.notes_sync.last_run
                + chrono::Duration::hours(config.notes_sync.interval_hours as i64))
            .format("%Y-%m-%d %H:%M:%S UTC")
            .to_string(),
        )
    } else {
        None
    };

    Ok(AppStatus {
        stocking: TaskStatus {
            last_run: config
                .stocking_update
                .last_run
                .format("%Y-%m-%d %H:%M:%S UTC")
                .to_string(),
            last_success: config.stocking_update.last_success,
            last_error: config.stocking_update.last_error.clone(),
            next_run: stocking_next,
            enabled: config.stocking_update.enabled,
            interval_hours: config.stocking_update.interval_hours,
        },
        notes_sync: TaskStatus {
            last_run: config
                .notes_sync
                .last_run
                .format("%Y-%m-%d %H:%M:%S UTC")
                .to_string(),
            last_success: config.notes_sync.last_success,
            last_error: config.notes_sync.last_error.clone(),
            next_run: notes_next,
            enabled: config.notes_sync.enabled,
            interval_hours: config.notes_sync.interval_hours,
        },
        db_size_bytes,
        db_modified,
    })
}

// -- Autostart --

#[tauri::command]
pub async fn get_autostart_status(app: tauri::AppHandle) -> Result<bool, String> {
    use tauri_plugin_autostart::ManagerExt;
    app.autolaunch()
        .is_enabled()
        .map_err(|e| e.to_string())
}

#[tauri::command]
pub async fn set_autostart(app: tauri::AppHandle, enabled: bool) -> Result<(), String> {
    use tauri_plugin_autostart::ManagerExt;
    let autostart = app.autolaunch();
    if enabled {
        autostart.enable().map_err(|e| e.to_string())
    } else {
        autostart.disable().map_err(|e| e.to_string())
    }
}

fn send_failure_notification(app: &tauri::AppHandle, title: &str, body: &str) {
    use tauri_plugin_notification::NotificationExt;
    let truncated = if body.len() > 200 {
        &body[..200]
    } else {
        body
    };
    let _ = app.notification().builder().title(title).body(truncated).show();
}
