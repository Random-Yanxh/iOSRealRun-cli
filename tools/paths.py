"""
Path helpers for source and frozen builds.
"""

import os
import sys
from pathlib import Path


def app_dir():
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


def app_path(*parts):
    return app_dir().joinpath(*parts)


def chdir_app_dir():
    os.chdir(app_dir())
