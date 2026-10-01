#!/usr/bin/env python3
"""
Image Tile Puzzle
Entry point.
"""

import os
import subprocess
import sys
from pathlib import Path


def main() -> None:
    try:
        from src.app import run_app
    except ModuleNotFoundError as error:
        if error.name not in {"_tkinter", "tkinter", "cv2", "numpy", "PIL"}:
            raise

        project_root = Path(__file__).resolve().parent
        for environment in (project_root / ".venv", project_root / "venv"):
            if os.name == "nt":
                environment_python = environment / "Scripts" / "python.exe"
            else:
                environment_python = environment / "bin" / "python"

            if (
                not environment_python.is_file()
                or Path(sys.prefix).resolve() == environment.resolve()
            ):
                continue

            try:
                subprocess.run(
                    [
                        str(environment_python),
                        "-c",
                        "import tkinter, cv2, numpy; from PIL import Image, ImageTk",
                    ],
                    check=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            except (OSError, subprocess.CalledProcessError):
                continue

            print(
                f"{error.name} is unavailable; restarting with {environment.name}.",
                file=sys.stderr,
            )
            os.execv(
                str(environment_python),
                [str(environment_python), str(Path(__file__).resolve()), *sys.argv[1:]],
            )
        raise

    run_app()


if __name__ == "__main__":
    main()
