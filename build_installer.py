import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ISS_PATH = ROOT / "installer.iss"
OUTPUT_DIR = ROOT / "installer"


def find_iscc():
    candidates = [
        shutil.which("iscc"),
        shutil.which("ISCC"),
        r"C:\Program Files\Inno Setup 7\ISCC.exe",
        r"C:\Program Files (x86)\Inno Setup 7\ISCC.exe",
        r"C:\Program Files\Inno Setup 6\iscc.exe",
        r"C:\Program Files (x86)\Inno Setup 6\iscc.exe",
        r"C:\Program Files\Inno Setup 6\ISCC.exe",
        r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
    ]
    for candidate in candidates:
        if candidate and os.path.exists(candidate):
            return candidate
    return None


def main():
    parser = argparse.ArgumentParser(description="Build the Hanshar Windows Toolkit installer.")
    parser.add_argument("--iss", type=str, default=str(ISS_PATH), help="Inno Setup script path")
    parser.add_argument("--output-dir", type=str, default=str(OUTPUT_DIR), help="Installer output directory")
    args = parser.parse_args()

    iss_path = Path(args.iss)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    iscc = find_iscc()
    if not iscc:
        print("Inno Setup not found on this machine.")
        print("Install Inno Setup 6 and run:")
        print(f"  {sys.executable} {ROOT / 'build_installer.py'}")
        return 1

    cmd = [iscc, str(iss_path), "/O" + str(output_dir)]
    print("Building installer using Inno Setup...")
    result = subprocess.run(cmd, check=False)
    if result.returncode == 0:
        print(f"Installer output folder: {output_dir}")
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
