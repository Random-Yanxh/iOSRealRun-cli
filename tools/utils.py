"""
utils.py
"""

import os
from tools.paths import app_path


# get the OS
def getOS():
    import sys
    OS = sys.platform
    if -1 != OS.find("win32"):
        return "win"
    elif -1 != OS.find("darwin"):
        return "darwin"
    else:
        return "linux"


OS = getOS()
seperator = {"win": "\\", "darwin": "/", "linux": "/"}[OS]


def getLibimobiledeviceDir():
    from tools.config import config
    return config.libimobiledeviceDir + seperator + OS


def getEnv():
    libimobiledeviceDir = getLibimobiledeviceDir()
    env = {
        "win": None,
        "darwin": {"DYLD_LIBRARY_PATH": str(app_path(libimobiledeviceDir))},
        "linux": {"LD_LIBRARY_PATH": str(app_path(libimobiledeviceDir))}
    }
    return env[OS]


# execute a command and return the output
def cmd(i_cmd, getoutp=True, libimobiledevice=True):
    import subprocess
    libimobiledeviceDir = getLibimobiledeviceDir()
    if libimobiledevice:
        if type(i_cmd) == str:
            i_cmd = str(app_path(libimobiledeviceDir, i_cmd))
        else:
            i_cmd[0] = str(app_path(libimobiledeviceDir, i_cmd[0]))
    startupinfo = None
    creationflags = 0
    if OS == "win":
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        creationflags = subprocess.CREATE_NO_WINDOW
    if getoutp:
        return subprocess.Popen(
            i_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=getEnv(),
            startupinfo=startupinfo,
            creationflags=creationflags,
        ).stdout.read().decode("utf-8")
    else:
        subprocess.run(
            i_cmd,
            env=getEnv(),
            startupinfo=startupinfo,
            creationflags=creationflags,
        )

# pair the device
def pair() -> int:
    resp = cmd(["idevicepair", "pair"])
    if -1 != resp.find("SUCCESS"):
        return 0
    if -1 != resp.find("No device found"):
        return 1
    if -1 != resp.find("passcode"):
        while -1 != resp.find("passcode"):
            input("请解锁手机后按回车")
            resp = cmd(["idevicepair", "pair"])
        if -1 != resp.find("SUCCESS"):
            return 0
    if -1 != resp.find("trust"):
        while -1 != resp.find("trust"):
            input("请在你的手机/或平板上按提示信任此电脑并按回车")
            resp = cmd(["idevicepair", "pair"])
        if -1 != resp.find("SUCCESS"):
            return 0
        else:
            return -1
    else:
        return -1

def getDeviceInfo():
    import re
    info = cmd("ideviceinfo")
    deviceName = re.search(r"DeviceName: (.+)\n", info).group(1).strip()
    version = re.search(r"ProductVersion: (.+)\n", info).group(1).strip()
    return deviceName, version


def setLoc(loc):
    cmd(["idevicesetlocation", "--", str(loc["lat"]), str(loc["lng"])], False)

def resetLoc():
    cmd(["idevicesetlocation", "reset"], False)


ES_CONTINUOUS = 0x80000000
ES_DISPLAY_REQUIRED = 0x00000002
def setDisplayRequired():
    import ctypes
    ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS | ES_DISPLAY_REQUIRED)
def resetDisplayRequired():
    import ctypes
    ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS)
