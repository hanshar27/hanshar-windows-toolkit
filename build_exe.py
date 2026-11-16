import argparse
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DIST = ROOT / "dist"
BUILD = ROOT / "build"
SPEC = ROOT / "HansharWindowsToolkit.spec"
ICON = ROOT / "assets" / "app_icon.ico"
ASSET_DIR = ROOT / "assets"


def ensure_pyinstaller():
    try:
        subprocess.run([sys.executable, "-m", "PyInstaller", "--version"], check=True, capture_output=True, text=True)
        return True
    except Exception:
        return False


def build_exe(output_dir: str | Path | None = None, onefile: bool = True, clean: bool = True):
    output_dir = Path(output_dir) if output_dir else DIST
    output_dir.mkdir(parents=True, exist_ok=True)
    BUILD.mkdir(parents=True, exist_ok=True)

    if not ensure_pyinstaller():
        raise RuntimeError(
            "PyInstaller is not installed. Run: "
            f"{sys.executable} -m pip install pyinstaller"
        )

    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--name",
        "HansharWindowsToolkit",
        "--windowed",
        "--distpath",
        str(output_dir),
        "--workpath",
        str(BUILD),
        "--specpath",
        str(ROOT),
        "--add-data",
        f"{ROOT / 'config.json'}{os.pathsep}.",
    ]

    if clean:
        cmd.append("--clean")
    if onefile:
        cmd.append("--onefile")
    else:
        cmd.append("--onedir")

    if ASSET_DIR.exists():
        cmd.extend([
            "--add-data",
            f"{ASSET_DIR}{os.pathsep}assets",
        ])
    if ICON.exists():
        cmd.extend(["--icon", str(ICON)])

    cmd.append(str(ROOT / "main.py"))
    return cmd


def main():
    parser = argparse.ArgumentParser(description="Build the Hanshar Windows Toolkit executable bundle.")
    parser.add_argument("--output-dir", type=str, default=str(DIST), help="Dist output folder")
    parser.add_argument("--onedir", action="store_true", help="Build a directory bundle instead of a single EXE")
    parser.add_argument("--no-clean", action="store_true", help="Skip cleaning temporary PyInstaller files")
    args = parser.parse_args()

    onefile = not args.onedir
    clean = not args.no_clean
    output_dir = Path(args.output_dir)

    cmd = build_exe(output_dir=output_dir, onefile=onefile, clean=clean)
    print("Building Hanshar Windows Toolkit EXE...")
    subprocess.run(cmd, check=True)

    exe_path = output_dir / "HansharWindowsToolkit.exe"
    if not exe_path.exists():
        print(f"Build succeeded. Output folder: {output_dir}")
        return 0

    print(f"EXE output: {exe_path}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1)
