use std::sync::Mutex;
use tauri::Manager;

/// Holds the backend sidecar child process so we can kill it on exit.
struct BackendProcess(Mutex<Option<std::process::Child>>);

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .plugin(
            tauri_plugin_global_shortcut::Builder::new()
                .with_handler(|app, _shortcut, _event| {
                    if let Some(window) = app.get_webview_window("main") {
                        if window.is_visible().unwrap_or(false) {
                            let _ = window.hide();
                        } else {
                            let _ = window.show();
                            let _ = window.set_focus();
                        }
                    }
                })
                .build(),
        )
        .setup(|app| {
            // Register Alt+Space global shortcut
            use tauri_plugin_global_shortcut::GlobalShortcutExt;
            let _ = app.global_shortcut().register("Alt+Space");

            // Spawn the Python backend server as a sidecar
            let resource_dir = app
                .path()
                .resource_dir()
                .unwrap_or_else(|_| std::path::PathBuf::from("."));

            let sidecar_path = resource_dir.join("bin").join("aura-server.exe");

            let child = if sidecar_path.exists() {
                // Production: run the bundled sidecar
                match std::process::Command::new(&sidecar_path)
                    .arg("--server")
                    .stdout(std::process::Stdio::null())
                    .stderr(std::process::Stdio::null())
                    .spawn()
                {
                    Ok(child) => {
                        println!("[Aura] Backend sidecar started (pid {})", child.id());
                        Some(child)
                    }
                    Err(e) => {
                        eprintln!("[Aura] Failed to start sidecar: {}", e);
                        None
                    }
                }
            } else {
                // Development: try to start `python -m aura --server`
                match std::process::Command::new("python")
                    .args(["-m", "aura", "--server"])
                    .current_dir(r"D:\automation\aura")
                    .stdout(std::process::Stdio::null())
                    .stderr(std::process::Stdio::null())
                    .spawn()
                {
                    Ok(child) => {
                        println!("[Aura] Dev backend started (pid {})", child.id());
                        Some(child)
                    }
                    Err(e) => {
                        eprintln!("[Aura] Failed to start dev backend: {}", e);
                        None
                    }
                }
            };

            app.manage(BackendProcess(Mutex::new(child)));

            Ok(())
        })
        .on_window_event(|window, event| {
            if let tauri::WindowEvent::Destroyed = event {
                // Kill the backend process when the window is closed
                if let Some(state) = window.try_state::<BackendProcess>() {
                    if let Ok(mut guard) = state.0.lock() {
                        if let Some(mut child) = guard.take() {
                            let _ = child.kill();
                            println!("[Aura] Backend process killed");
                        }
                    }
                }
            }
        })
        .run(tauri::generate_context!())
        .expect("error while running Agent Aura");
}
