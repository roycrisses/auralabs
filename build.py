import os
import subprocess
import shutil
import sys
from pathlib import Path

# Project structure
ROOT = Path(__file__).parent.absolute()
BACKEND_DIR = ROOT
UI_DIR = ROOT / "ui"
TAURI_DIR = UI_DIR / "src-tauri"

def run(cmd, cwd=None, check=True):
    if isinstance(cmd, list):
        cmd_str = ' '.join(cmd)
    else:
        cmd_str = cmd
    
    print(f"\n  > {cmd_str}")
    # On Windows, we must use shell=True for 'call', 'pnpm', etc.
    result = subprocess.run(cmd_str, cwd=cwd, shell=True)
    if check and result.returncode != 0:
        print(f"  ERROR: Command failed with code {result.returncode}")
        sys.exit(result.returncode)
    return result

def main():
    skip_backend = "--skip-backend" in sys.argv
    
    print("=" * 60)
    print("  AgentAura Build System")
    print("=" * 60)

    if not skip_backend:
        print("\n" + "=" * 60)
        print("  Building Python backend (aura-server.exe)")
        print("=" * 60)
        
        # Build the backend with PyInstaller
        # We use the spec file for consistent builds
        python_exe = sys.executable
        run([python_exe, "-m", "PyInstaller", "--clean", "--noconfirm", "Aura.spec"])
    else:
        print("\n  [Skipping Python backend build]")

    print("\n" + "=" * 60)
    print("  Preparing UI (pnpm build)")
    print("=" * 60)
    
    # Ensure UI dependencies are installed
    if not (UI_DIR / "node_modules").exists():
        run(["pnpm", "install"], cwd=UI_DIR)

    # Note: Tauri build performs pnpm build internally if configured in tauri.conf.json
    # But we'll do it explicitly if needed, or just let Tauri handle it.
    
    print("\n" + "=" * 60)
    print("  Copying sidecar to Tauri bin/")
    print("=" * 60)
    
    # The built server needs to be placed where Tauri expects it as a sidecar
    # Tauri expects the binary name to include the target triple
    bin_dir = TAURI_DIR / "bin"
    bin_dir.mkdir(exist_ok=True)
    
    server_exe = ROOT / "dist" / "aura-server.exe"
    if not server_exe.exists():
        print(f"  ERROR: Could not find {server_exe}. Backend build might have failed.")
        sys.exit(1)
        
    # Standard sidecar name: [binary]-[target-triple].exe
    # For Windows x64: aura-server-x86_64-pc-windows-msvc.exe
    target_exe = bin_dir / "aura-server-x86_64-pc-windows-msvc.exe"
    shutil.copy2(server_exe, target_exe)
    # Also copy as generic for local dev testing if needed
    shutil.copy2(server_exe, bin_dir / "aura-server.exe")
    
    print(f"\n  Copied to: {target_exe}")
    print(f"  Copied to: {bin_dir / 'aura-server.exe'}")

    print("\n" + "=" * 60)
    print("  Building Tauri application (AgentAura.exe)")
    print("=" * 60)
    
    # Use vcvars64.bat on Windows to ensure MSVC (cl.exe) is in the PATH
    vcvars_path = r"C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat"
    if os.path.exists(vcvars_path):
        cmd = f'call "{vcvars_path}" && pnpm tauri build'
        run(cmd, cwd=UI_DIR)
    else:
        run(["pnpm", "tauri", "build"], cwd=UI_DIR)

    # Find the output exe
    release_dir = TAURI_DIR / "target" / "release"
    bundle_dir = release_dir / "bundle" / "msi" # Or 'exe' depending on config
    
    print("\n" + "=" * 60)
    print("  Build complete!")
    print("=" * 60)
    print(f"\n  Find your application in: {release_dir}")

if __name__ == "__main__":
    main()
