"""Victor — The Artificial Soul: Standalone Desktop Application Builder.

Handles dependency checks, asset verification, test suite execution,
PyInstaller compilation, and optional portable zip packaging.
"""

import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import zipfile

BANNER = r"""
=============================================================
  __      ___      _               ____        _ _     _           
  \ \    / (_)    | |             |  _ \      (_) |   | |          
   \ \  / / _  ___| |_ ___  _ __  | |_) |_   _ _| | __| | ___ _ __ 
    \ \/ / | |/ __| __/ _ \| '__| |  _ <| | | | | |/ _` |/ _ \ '__|
     \  /  | | (__| || (_) | |    | |_) | |_| | | | (_| |  __/ |   
      \/   |_|\___|\__\___/|_|    |____/ \__,_|_|_|\__,_|\___|_|   
                     [ THE ARTIFICIAL SOUL BUILDER v2.5 ]
=============================================================
"""


class VictorBuilder:
    def __init__(self, skip_tests: bool = False, make_zip: bool = False, clean: bool = True, run_after: bool = False):
        self.root_dir = Path(__file__).resolve().parent
        self.dist_dir = self.root_dir / "dist"
        self.build_dir = self.root_dir / "build"
        self.spec_file = self.root_dir / "victor.spec"
        self.skip_tests = skip_tests
        self.make_zip = make_zip
        self.clean = clean
        self.run_after = run_after

    def log(self, step: str, msg: str):
        print(f"[{step}] {msg}")

    def error(self, msg: str):
        print(f"\n[ERROR] {msg}", file=sys.stderr)
        sys.exit(1)

    def success(self, msg: str):
        print(f"\n[SUCCESS] {msg}")

    def check_environment(self):
        self.log("1/5", "Auditing build environment and dependencies...")
        print(f"      Python: {sys.version.split()[0]} ({sys.executable})")
        print(f"      Workspace: {self.root_dir}")

        required_modules = [
            ("fastapi", "FastAPI"),
            ("uvicorn", "Uvicorn"),
            ("pydantic", "Pydantic"),
            ("PIL", "Pillow"),
            ("yaml", "PyYAML"),
            ("webview", "PyWebView"),
            ("sounddevice", "SoundDevice"),
            ("speech_recognition", "SpeechRecognition"),
            ("PyInstaller", "PyInstaller"),
        ]

        missing = []
        for mod, label in required_modules:
            try:
                __import__(mod)
                print(f"      [OK] {label}")
            except ImportError:
                missing.append(label)
                print(f"      [FAIL] {label} (missing)")

        if missing:
            self.error(f"Missing required build packages: {', '.join(missing)}.\nRun: pip install -r requirements.txt pyinstaller")

    def verify_assets(self):
        self.log("2/5", "Verifying application source assets...")
        required_paths = [
            self.root_dir / "victor" / "web" / "index.html",
            self.root_dir / "victor" / "web" / "style.css",
            self.root_dir / "victor" / "web" / "app.js",
            self.root_dir / "victor" / "sprite" / "neutral.png",
            self.root_dir / "victor" / "sprite" / "happy.png",
            self.root_dir / "victor" / "sprite" / "curious.png",
            self.root_dir / "victor" / "sprite" / "thinking.png",
            self.root_dir / "config" / "victor.yaml",
            self.spec_file,
        ]

        for p in required_paths:
            if not p.exists():
                self.error(f"Required asset not found: {p}")
            print(f"      [OK] {p.relative_to(self.root_dir)}")

    def run_tests(self):
        if self.skip_tests:
            self.log("3/5", "Skipping test suite (--skip-tests specified).")
            return

        self.log("3/5", "Executing full automated test suite...")
        res = subprocess.run([sys.executable, "-m", "pytest", "-v", "tests/"], cwd=self.root_dir)
        if res.returncode != 0:
            self.error("Test suite failed. Build aborted to prevent compiling broken binaries.")
        print("      [OK] All test assertions passed cleanly.")

    def compile_pyinstaller(self):
        self.log("4/5", "Compiling standalone desktop executable with PyInstaller...")

        cmd = [
            sys.executable,
            "-m",
            "PyInstaller",
            "--noconfirm",
        ]
        if self.clean:
            cmd.append("--clean")
        cmd.append(str(self.spec_file))

        print(f"      Executing: {' '.join(cmd)}")
        start_time = time.time()
        res = subprocess.run(cmd, cwd=self.root_dir)
        elapsed = time.time() - start_time

        if res.returncode != 0:
            self.error("PyInstaller compilation failed.")

        exe_path = self.dist_dir / "Victor" / "Victor.exe"
        if not exe_path.exists():
            self.error(f"Expected compiled binary not found at: {exe_path}")

        exe_size_mb = exe_path.stat().st_size / (1024 * 1024)
        print(f"      [OK] Standalone executable compiled in {elapsed:.1f}s: {exe_path} ({exe_size_mb:.1f} MB)")

    def package_distribution(self):
        self.log("5/5", "Finalizing distribution artifacts...")
        victor_dist = self.dist_dir / "Victor"

        # Ensure config directory is accessible in root dist folder for user customization
        user_config_dir = victor_dist / "config"
        user_config_dir.mkdir(exist_ok=True)
        src_config = self.root_dir / "config" / "victor.yaml"
        if src_config.exists() and not (user_config_dir / "victor.yaml").exists():
            shutil.copy2(src_config, user_config_dir / "victor.yaml")
            print("      [OK] Seeded user config at dist/Victor/config/victor.yaml")

        if self.make_zip:
            zip_path = self.dist_dir / "Victor-Standalone-v2.5.zip"
            print(f"      Packaging zip archive: {zip_path.name}...")
            with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
                for root, _, files in os.walk(victor_dist):
                    for file in files:
                        full_path = Path(root) / file
                        rel_path = full_path.relative_to(self.dist_dir)
                        zf.write(full_path, rel_path)
            zip_size_mb = zip_path.stat().st_size / (1024 * 1024)
            print(f"      [OK] Created portable distribution archive ({zip_size_mb:.1f} MB)")

    def launch(self):
        exe_path = self.dist_dir / "Victor" / "Victor.exe"
        if self.run_after and exe_path.exists():
            print(f"\n[LAUNCH] Launching {exe_path}...")
            subprocess.Popen([str(exe_path)], cwd=str(exe_path.parent))

    def build(self):
        print(BANNER)
        t0 = time.time()
        self.check_environment()
        self.verify_assets()
        self.run_tests()
        self.compile_pyinstaller()
        self.package_distribution()
        total_time = time.time() - t0

        self.success(f"BUILD COMPLETE in {total_time:.1f} seconds!")
        print("=============================================================")
        print(f"  Executable:  dist\\Victor\\Victor.exe")
        print(f"  Directory:   {self.dist_dir / 'Victor'}")
        if self.make_zip:
            print(f"  Zip Archive: dist\\Victor-Standalone-v2.5.zip")
        print("=============================================================\n")

        self.launch()


def main():
    parser = argparse.ArgumentParser(description="Victor Desktop Application Builder")
    parser.add_argument("--skip-tests", action="store_true", help="Skip running the pytest suite")
    parser.add_argument("--zip", action="store_true", help="Generate a portable distribution .zip archive")
    parser.add_argument("--no-clean", action="store_true", help="Do not pass --clean to PyInstaller")
    parser.add_argument("--run", action="store_true", help="Launch the compiled application after building")

    args = parser.parse_args()
    builder = VictorBuilder(
        skip_tests=args.skip_tests,
        make_zip=args.zip,
        clean=not args.no_clean,
        run_after=args.run
    )
    builder.build()


if __name__ == "__main__":
    main()
