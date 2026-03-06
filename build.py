"""Build script for AgentAura.exe — bundles Python backend + Tauri/React UI.

Usage: python build.py

Steps:
1. Build the Python backend into aura-server.exe via PyInstaller
2. Copy aura-server.exe into ui/src-tauri/bin/
3. Build the Tauri app (compiles React UI + Rust wrapper)
4. Output: ui/src-tauri/target/release/AgentAura.exe
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent.resolve()
UI_DIR = ROOT / "ui"
TAURI_DIR = UI_DIR / "src-tauri"
TAURI_BIN = TAURI_DIR / "bin"
DIST_DIR = ROOT / "dist"


def step(msg: str):
    print(f"\n{'='*60}")
    print(f"  {msg}")
    print(f"{'='*60}\n")


def run(cmd: list[str], cwd: Path | None = None, check: bool = True):
    print(f"  > {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=str(cwd or ROOT), shell=True)
    if check and result.returncode != 0:
        print(f"  ERROR: Command failed with code {result.returncode}")
        sys.exit(1)
    return result


def build_python_backend():
    """Step 1: Build aura-server.exe with PyInstaller."""
    step("Building Python backend (aura-server.exe)")

    run(["pyinstaller", "--clean", "--noconfirm", "Aura.spec"], cwd=ROOT)

    exe_path = ROOT / "dist" / "aura-server.exe"
    if not exe_path.exists():
        print(f"  ERROR: {exe_path} not found after build!")
        sys.exit(1)

    print(f"  Built: {exe_path} ({exe_path.stat().st_size / 1024 / 1024:.1f} MB)")
    return exe_path


def copy_sidecar(exe_path: Path):
    """Step 2: Copy aura-server.exe into Tauri bin directory."""
    step("Copying sidecar to Tauri bin/")

    TAURI_BIN.mkdir(parents=True, exist_ok=True)

    # Tauri expects the sidecar name to match the platform triple
    # For Windows x86_64: aura-server-x86_64-pc-windows-msvc.exe
    target_triple = "x86_64-pc-windows-msvc"
    dest = TAURI_BIN / f"aura-server-{target_triple}.exe"

    shutil.copy2(str(exe_path), str(dest))
    print(f"  Copied to: {dest}")

    # Also copy without triple for our manual spawn
    dest_plain = TAURI_BIN / "aura-server.exe"
    shutil.copy2(str(exe_path), str(dest_plain))
    print(f"  Copied to: {dest_plain}")


def build_tauri():
    """Step 3: Build the Tauri application."""
    step("Building Tauri application (AgentAura.exe)")

    # First ensure node_modules are installed
    if not (UI_DIR / "node_modules").exists():
        run(["pnpm", "install"], cwd=UI_DIR)

    # Build the Tauri app
    run(["pnpm", "tauri", "build"], cwd=UI_DIR)

    # Find the output exe
    release_dir = TAURI_DIR / "target" / "release"
    exe_candidates = list(release_dir.glob("AgentAura.exe")) + list(release_dir.glob("aura.exe"))

    if exe_candidates:
        final_exe = exe_candidates[0]
        print(f"\n  SUCCESS: {final_exe} ({final_exe.stat().st_size / 1024 / 1024:.1f} MB)")
    else:
        # Check in bundle dir
        bundle_dir = release_dir / "bundle"
        if bundle_dir.exists():
            for p in bundle_dir.rglob("*.exe"):
                print(f"  Found bundle: {p}")
            for p in bundle_dir.rglob("*.msi"):
                print(f"  Found installer: {p}")
        print(f"\n  Build complete. Check {release_dir} for output.")


def main():
    print("=" * 60)
    print("  AgentAura Build System")
    print("=" * 60)

    # Step 1: Python backend
    exe_path = build_python_backend()

    # Step 2: Copy sidecar
    copy_sidecar(exe_path)

    # Step 3: Build Tauri
    build_tauri()

    step("BUILD COMPLETE!")
    print("  Output locations:")
    print(f"    Backend: {ROOT / 'dist' / 'aura-server.exe'}")
    print(f"    Sidecar: {TAURI_BIN / 'aura-server.exe'}")
    print(f"    App:     {TAURI_DIR / 'target' / 'release'}")
    print()


if __name__ == "__main__":
    main()
