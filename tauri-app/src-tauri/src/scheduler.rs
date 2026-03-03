use chrono::{DateTime, Duration, Utc};
use serde::{Deserialize, Serialize};
use std::path::PathBuf;
use std::sync::Arc;
use std::sync::Mutex;
use tauri::{AppHandle, Emitter};
use tauri_plugin_store::StoreExt;

use crate::scripts;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TaskSchedule {
    pub enabled: bool,
    pub interval_hours: u64,
    #[serde(default = "Utc::now")]
    pub last_run: DateTime<Utc>,
    pub last_success: bool,
    pub last_error: Option<String>,
}

impl Default for TaskSchedule {
    fn default() -> Self {
        Self {
            enabled: false,
            interval_hours: 72,
            last_run: Utc::now() - Duration::days(365),
            last_success: true,
            last_error: None,
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ScheduleConfig {
    pub stocking_update: TaskSchedule,
    pub notes_sync: TaskSchedule,
}

impl Default for ScheduleConfig {
    fn default() -> Self {
        Self {
            stocking_update: TaskSchedule {
                interval_hours: 72,
                ..Default::default()
            },
            notes_sync: TaskSchedule {
                interval_hours: 6,
                ..Default::default()
            },
        }
    }
}

#[derive(Debug, Serialize, Clone)]
pub struct ScheduleEvent {
    pub task: String,
    pub success: bool,
    pub error: Option<String>,
    pub timestamp: DateTime<Utc>,
}

pub struct SchedulerState {
    pub config: ScheduleConfig,
    pub project_dir: PathBuf,
}

pub fn load_config(app: &AppHandle) -> ScheduleConfig {
    match app.store("schedule.json") {
        Ok(store) => {
            let val: Option<serde_json::Value> = store.get("config");
            match val {
                Some(v) => serde_json::from_value::<ScheduleConfig>(v).unwrap_or_default(),
                None => ScheduleConfig::default(),
            }
        }
        Err(_) => ScheduleConfig::default(),
    }
}

pub fn save_config(app: &AppHandle, config: &ScheduleConfig) {
    if let Ok(store) = app.store("schedule.json") {
        let _ = store.set(
            "config",
            serde_json::to_value(config).unwrap_or_default(),
        );
        let _ = store.save();
    }
}

/// Runs the scheduler on a background OS thread (no Tokio runtime needed).
pub fn start_scheduler(app: AppHandle, state: Arc<Mutex<SchedulerState>>) {
    std::thread::Builder::new()
        .name("scheduler".into())
        .spawn(move || {
            loop {
                std::thread::sleep(std::time::Duration::from_secs(60));

                let now = Utc::now();

                // Read current config
                let (_stocking_enabled, stocking_due, _notes_enabled, notes_due, project_dir) = {
                    let state_guard = state.lock().unwrap();
                    let sc = &state_guard.config.stocking_update;
                    let nc = &state_guard.config.notes_sync;
                    let stocking_next = sc.last_run + Duration::hours(sc.interval_hours as i64);
                    let notes_next = nc.last_run + Duration::hours(nc.interval_hours as i64);
                    (
                        sc.enabled,
                        sc.enabled && now >= stocking_next,
                        nc.enabled,
                        nc.enabled && now >= notes_next,
                        state_guard.project_dir.clone(),
                    )
                };

                // Run stocking update if due
                if stocking_due {
                    let r1 = scripts::run_python_script(&project_dir, "fetch_latest_stocking.py");
                    let result = if r1.success {
                        scripts::run_python_script(&project_dir, "update_stocking.py")
                    } else {
                        r1
                    };

                    let mut state_guard = state.lock().unwrap();
                    state_guard.config.stocking_update.last_run = now;
                    state_guard.config.stocking_update.last_success = result.success;
                    state_guard.config.stocking_update.last_error = if result.success {
                        None
                    } else {
                        Some(result.stderr.clone())
                    };
                    save_config(&app, &state_guard.config);

                    let _ = app.emit(
                        "schedule-update",
                        &ScheduleEvent {
                            task: "stocking_update".into(),
                            success: result.success,
                            error: if result.success { None } else { Some(result.stderr.clone()) },
                            timestamp: now,
                        },
                    );

                    if !result.success {
                        send_notification(&app, "Stocking Update Failed", &result.stderr);
                    }
                }

                // Run notes sync if due
                if notes_due {
                    let result = scripts::run_notes_sync_script(&project_dir);

                    let mut state_guard = state.lock().unwrap();
                    state_guard.config.notes_sync.last_run = now;
                    state_guard.config.notes_sync.last_success = result.success;
                    state_guard.config.notes_sync.last_error = if result.success {
                        None
                    } else {
                        Some(result.stderr.clone())
                    };
                    save_config(&app, &state_guard.config);

                    let _ = app.emit(
                        "schedule-update",
                        &ScheduleEvent {
                            task: "notes_sync".into(),
                            success: result.success,
                            error: if result.success { None } else { Some(result.stderr.clone()) },
                            timestamp: now,
                        },
                    );

                    if !result.success {
                        send_notification(&app, "Notes Sync Failed", &result.stderr);
                    }
                }
            }
        })
        .expect("failed to spawn scheduler thread");
}

fn send_notification(app: &AppHandle, title: &str, body: &str) {
    use tauri_plugin_notification::NotificationExt;
    let _ = app
        .notification()
        .builder()
        .title(title)
        .body(body)
        .show();
}
