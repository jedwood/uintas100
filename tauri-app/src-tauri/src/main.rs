// Prevents additional console window on Windows in release
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

mod commands;
mod scheduler;
mod scripts;

use scheduler::SchedulerState;
use std::path::{Path, PathBuf};
use std::sync::{Arc, Mutex};
use tauri::Manager;
use tauri_plugin_autostart::MacosLauncher;
use tauri_plugin_store::StoreExt;

const KNOWN_PROJECT_DIR: &str = "/Users/jed/repos/uintas";

fn find_project_dir(app: &tauri::App) -> PathBuf {
    // 1. Check if we saved a path from a previous run
    if let Ok(store) = app.handle().store("settings.json") {
        if let Some(val) = store.get("project_dir") {
            if let Some(s) = val.as_str() {
                let p = PathBuf::from(s);
                if p.join("uinta_lakes.db").exists() {
                    return p;
                }
            }
        }
    }

    // 2. Dev mode: CARGO_MANIFEST_DIR -> src-tauri -> tauri-app -> repo root
    if let Ok(manifest) = std::env::var("CARGO_MANIFEST_DIR") {
        let p = PathBuf::from(manifest);
        if let Some(repo) = p.parent().and_then(|p| p.parent()) {
            if repo.join("uinta_lakes.db").exists() {
                return repo.to_path_buf();
            }
        }
    }

    // 3. Known project directory
    let known = PathBuf::from(KNOWN_PROJECT_DIR);
    if known.join("uinta_lakes.db").exists() {
        return known;
    }

    // 4. Current working directory
    if let Ok(cwd) = std::env::current_dir() {
        if cwd.join("uinta_lakes.db").exists() {
            return cwd;
        }
    }

    // 5. Walk up from executable
    if let Ok(exe) = std::env::current_exe() {
        let mut dir = exe.parent().unwrap_or(Path::new(".")).to_path_buf();
        for _ in 0..6 {
            if dir.join("uinta_lakes.db").exists() {
                return dir;
            }
            match dir.parent() {
                Some(parent) => dir = parent.to_path_buf(),
                None => break,
            }
        }
    }

    // Fallback
    PathBuf::from(KNOWN_PROJECT_DIR)
}

fn main() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_notification::init())
        .plugin(tauri_plugin_autostart::init(
            MacosLauncher::LaunchAgent,
            None,
        ))
        .plugin(tauri_plugin_store::Builder::default().build())
        .setup(|app| {
            let resolved_dir = find_project_dir(app);

            // Persist for future launches
            if let Ok(store) = app.handle().store("settings.json") {
                let _ = store.set("project_dir", serde_json::json!(resolved_dir.to_string_lossy()));
                let _ = store.save();
            }

            println!("Uintas project dir: {:?}", resolved_dir);

            let config = scheduler::load_config(&app.handle());

            let state = Arc::new(Mutex::new(SchedulerState {
                config,
                project_dir: resolved_dir,
            }));

            app.manage(state.clone());

            // Start the scheduler
            scheduler::start_scheduler(app.handle().clone(), state);

            Ok(())
        })
        .invoke_handler(tauri::generate_handler![
            commands::run_stocking_update,
            commands::run_notes_sync,
            commands::run_notes_push,
            commands::get_schedule,
            commands::set_schedule,
            commands::read_log,
            commands::get_status,
            commands::get_autostart_status,
            commands::set_autostart,
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
