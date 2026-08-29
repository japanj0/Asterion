import process_blocker
import sys
import json
import threading
import hashlib
import socket
import ssl
import time
import base64
import os
import platform
import psutil
from datetime import datetime
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
import mss
import numpy as np
import cv2
from crypto import TransportCipher
import html
import pygame
from io import BytesIO
from usbmonitor import USBMonitor
from usbmonitor.attributes import ID_MODEL, ID_MODEL_ID, ID_VENDOR_ID
import subprocess
import tempfile
import ctypes

import ctypes
import shlex
import shutil
try:
    import win32com.client
except:
    pass
def _setup_windows_persistence(script_path):
    exe_path = sys.executable
    if exe_path.endswith(".py") or exe_path.endswith(".pyw"):
        exe_path = os.path.join(os.path.dirname(sys.executable), "pythonw.exe")
        if not os.path.exists(exe_path):
            exe_path = sys.executable

    is_binary = os.path.abspath(sys.executable) == os.path.abspath(script_path)
    if is_binary:
        arguments = '--FromPlan'
    else:
        arguments = f'--FromPlan "{script_path}"'

    task_created = False
    try:
        scheduler = win32com.client.Dispatch("Schedule.Service")
        scheduler.Connect()
        root_folder = scheduler.GetFolder("\\")
        task_def = scheduler.NewTask(0)
        reg_info = task_def.RegistrationInfo
        reg_info.Description = "Asterion Blocker - System Lockdown"
        reg_info.Author = "Asterion"
        triggers = task_def.Triggers
        trigger = triggers.Create(9)
        trigger.Enabled = True
        action = task_def.Actions.Create(0)
        action.Path = exe_path
        action.Arguments = arguments
        action.WorkingDirectory = os.path.dirname(script_path)
        settings = task_def.Settings
        settings.Enabled = True
        settings.StartWhenAvailable = True
        settings.Hidden = False
        settings.AllowHardTerminate = True
        settings.RestartCount = 3
        settings.RestartInterval = "PT1M"
        principal = task_def.Principal
        principal.RunLevel = 1
        root_folder.RegisterTaskDefinition(
            "AsterionBlocker",
            task_def,
            6,
            "",
            "",
            3
        )
        task_created = True
    except Exception:
        pass

    if not task_created:
        try:
            subprocess.run([
                "schtasks", "/create", "/tn", "AsterionBlocker", "/tr",
                f'"{exe_path}" {arguments}',
                "/sc", "onlogon", "/rl", "highest", "/f"
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            task_created = True
        except:
            pass

    if not task_created:
        try:
            import winreg
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0,
                winreg.KEY_SET_VALUE
            )
            winreg.SetValueEx(key, "AsterionBlocker", 0, winreg.REG_SZ,
                            f'"{exe_path}" {arguments}')
            winreg.CloseKey(key)
        except:
            pass


def _setup_linux_persistence(script_path):
    systemd_dir = os.path.expanduser("~/.config/systemd/user")
    os.makedirs(systemd_dir, exist_ok=True)
    service_path = os.path.join(systemd_dir, "asterion-blocker.service")

    appimage_path = os.environ.get("APPIMAGE", "")
    if appimage_path and os.path.exists(appimage_path):
        exec_line = f"{appimage_path} --appimage-extract-and-run --FromPlan"
    else:
        is_binary = os.path.abspath(sys.executable) == os.path.abspath(script_path)
        if is_binary:
            exec_line = f"{script_path} --FromPlan"
        else:
            exec_line = f"{sys.executable} {script_path} --FromPlan"

    service_content = f"""[Unit]
Description=Asterion Blocker
After=graphical-session.target

[Service]
Type=simple
ExecStart={exec_line}
Restart=on-failure
RestartSec=10

[Install]
WantedBy=default.target
"""
    try:
        with open(service_path, 'w', encoding='utf-8') as f:
            f.write(service_content)
    except:
        pass
    try:
        subprocess.run(
            ["systemctl", "--user", "daemon-reload"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True
        )
        subprocess.run(
            ["systemctl", "--user", "enable", "asterion-blocker"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True
        )
    except:
        pass


def _setup_darwin_persistence(script_path):
    plist_dir = os.path.expanduser("~/Library/LaunchAgents")
    os.makedirs(plist_dir, exist_ok=True)
    plist_path = os.path.join(plist_dir, "com.asterion.blocker.plist")
    is_binary = os.path.abspath(sys.executable) == os.path.abspath(script_path)
    if is_binary:
        args_block = f"""    <string>{script_path}</string>
    <string>--FromPlan</string>"""
    else:
        args_block = f"""    <string>{sys.executable}</string>
    <string>{script_path}</string>
    <string>--FromPlan</string>"""
    plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.asterion.blocker</string>
    <key>ProgramArguments</key>
    <array>
{args_block}
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <dict>
        <key>SuccessfulExit</key>
        <false/>
    </dict>
    <key>ThrottleInterval</key>
    <integer>10</integer>
</dict>
</plist>"""
    try:
        with open(plist_path, 'w', encoding='utf-8') as f:
            f.write(plist_content)
    except:
        pass
    try:
        subprocess.run(
            ["launchctl", "unload", plist_path],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        subprocess.run(
            ["launchctl", "load", plist_path],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True
        )
    except:
        pass


_persistence_setup_done = False

def setup_persistence():
    global _persistence_setup_done
    if _persistence_setup_done:
        return
    _persistence_setup_done = True
    system = platform.system()
    script_path = os.path.abspath(sys.argv[0])
    if system == "Windows":
        _setup_windows_persistence(script_path)
    elif system == "Linux":
        _setup_linux_persistence(script_path)
    elif system == "Darwin":
        _setup_darwin_persistence(script_path)



def require_admin():
    system = platform.system()
    if system == "Windows":
        try:
            if ctypes.windll.shell32.IsUserAnAdmin():
                return
        except:
            pass
        try:
            args = " ".join(f'"{arg}"' for arg in sys.argv)
            ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, args, None, 1)
        except:
            pass
        sys.exit()
    elif system == "Linux":
        if os.geteuid() == 0:
            return
        for su_cmd in ('pkexec', 'gksu', 'kdesu', 'sudo'):
            try:
                if subprocess.run(['which', su_cmd], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0:
                    if sys.executable == sys.argv[0]:
                        cmd = [su_cmd] + sys.argv
                    else:
                        cmd = [su_cmd, sys.executable] + sys.argv
                    subprocess.run(cmd)
                    sys.exit()
            except:
                pass
        sys.exit(1)
    elif system == "Darwin":
        if os.getuid() == 0:
            return
        try:
            if sys.executable == sys.argv[0]:
                cmd_parts = sys.argv
            else:
                cmd_parts = [sys.executable] + sys.argv
            cmd = ' '.join(shlex.quote(arg) for arg in cmd_parts)
            subprocess.run([
                'osascript', '-e',
                f'do shell script {shlex.quote(cmd)} with administrator privileges'
            ])
            sys.exit()
        except:
            sys.exit(1)

SOUND_ALERT_MP3 = base64.b64decode("""SUQzAwAAAABIIlREQVQAAAAFAAAAMTQwM1RJTUUAAAAFAAAAMTc1NFBSSVYAABvoAABYTVAAPD94cGFja2V0IGJlZ2luPSLvu78iIGlkPSJXNU0wTXBDZWhpSHpyZVN6TlRjemtjOWQiPz4KPHg6eG1wbWV0YSB4bWxuczp4PSJhZG9iZTpuczptZXRhLyIgeDp4bXB0az0iQWRvYmUgWE1QIENvcmUgNS41LWMwMjEgNzkuMTU1MjQxLCAyMDEzLzExLzI1LTIxOjEwOjQwICAgICAgICAiPgogPHJkZjpSREYgeG1sbnM6cmRmPSJodHRwOi8vd3d3LnczLm9yZy8xOTk5LzAyLzIyLXJkZi1zeW50YXgtbnMjIj4KICA8cmRmOkRlc2NyaXB0aW9uIHJkZjphYm91dD0iIgogICAgeG1sbnM6eG1wTU09Imh0dHA6Ly9ucy5hZG9iZS5jb20veGFwLzEuMC9tbS8iCiAgICB4bWxuczpzdEV2dD0iaHR0cDovL25zLmFkb2JlLmNvbS94YXAvMS4wL3NUeXBlL1Jlc291cmNlRXZlbnQjIgogICAgeG1sbnM6c3RSZWY9Imh0dHA6Ly9ucy5hZG9iZS5jb20veGFwLzEuMC9zVHlwZS9SZXNvdXJjZVJlZiMiCiAgICB4bWxuczp4bXA9Imh0dHA6Ly9ucy5hZG9iZS5jb20veGFwLzEuMC8iCiAgICB4bWxuczp4bXBETT0iaHR0cDovL25zLmFkb2JlLmNvbS94bXAvMS4wL0R5bmFtaWNNZWRpYS8iCiAgICB4bWxuczpkYz0iaHR0cDovL3B1cmwub3JnL2RjL2VsZW1lbnRzLzEuMS8iCiAgICB4bWxuczpiZXh0PSJodHRwOi8vbnMuYWRvYmUuY29tL2J3Zi9iZXh0LzEuMC8iCiAgIHhtcE1NOkluc3RhbmNlSUQ9InhtcC5paWQ6MmYxZjVkMGUtYzIyMS00MzI0LWEwNGUtMTc0OTk3YTRjZTRlIgogICB4bXBNTTpEb2N1bWVudElEPSIwNGRhNTY4Yy1kOTJiLTFiZjMtM2VhMS02YjA0MDAwMDAwNDkiCiAgIHhtcE1NOk9yaWdpbmFsRG9jdW1lbnRJRD0ieG1wLmRpZDpiNmFkYmNkMS1hNzBmLTQ5NjUtYWNjMS00ODg2OWEwMDIxM2QiCiAgIHhtcDpNZXRhZGF0YURhdGU9IjIwMTQtMDMtMTRUMTc6NTQ6NTgtMDQ6MDAiCiAgIHhtcDpNb2RpZnlEYXRlPSIyMDE0LTAzLTE0VDE3OjU0OjU4LTA0OjAwIgogICB4bXA6Q3JlYXRlRGF0ZT0iMjAxNC0wMy0xNFQxNzo1NDoyOC0wNDowMCIKICAgeG1wRE06YXVkaW9TYW1wbGVSYXRlPSI0NDEwMCIKICAgeG1wRE06YXVkaW9TYW1wbGVUeXBlPSIxNkludCIKICAgeG1wRE06YXVkaW9DaGFubmVsVHlwZT0iU3RlcmVvIgogICB4bXBETTpzdGFydFRpbWVTY2FsZT0iMzAwMDAiCiAgIHhtcERNOnN0YXJ0VGltZVNhbXBsZVNpemU9IjEwMDEiCiAgIHhtcERNOnBhcnRPZkNvbXBpbGF0aW9uPSJmYWxzZSIKICAgZGM6Zm9ybWF0PSJNUDMiCiAgIGJleHQ6ZGVzY3JpcHRpb249Ik1VTFRJTUVESUEgQlVUVE9OIFRPTkFMIDAzIgogICBiZXh0Om9yaWdpbmF0b3I9IkFkb2JlIFN5c3RlbXMgSW5jIgogICBiZXh0Om9yaWdpbmF0aW9uRGF0ZT0iMjAxNC0wMy0wNSIKICAgYmV4dDpvcmlnaW5hdGlvblRpbWU9IjE5OjQ2OjExIgogICBiZXh0OnRpbWVSZWZlcmVuY2U9IjAiCiAgIGJleHQ6dmVyc2lvbj0iMSI+CiAgIDx4bXBNTTpIaXN0b3J5PgogICAgPHJkZjpTZXE+CiAgICAgPHJkZjpsaQogICAgICBzdEV2dDphY3Rpb249InNhdmVkIgogICAgICBzdEV2dDppbnN0YW5jZUlEPSIyZWZmN2MyMi1lMzMyLTMwNTMtNTFiYS0xZGVlMDAwMDAwNzYiCiAgICAgIHN0RXZ0OndoZW49IjIwMTQtMDMtMTRUMTc6NTQ6NTgtMDQ6MDAiCiAgICAgIHN0RXZ0OnNvZnR3YXJlQWdlbnQ9IkFkb2JlIEFkb2JlIE1lZGlhIEVuY29kZXIgQ0MgKE1hY2ludG9zaCkiCiAgICAgIHN0RXZ0OmNoYW5nZWQ9Ii8iLz4KICAgICA8cmRmOmxpCiAgICAgIHN0RXZ0OmFjdGlvbj0ic2F2ZWQiCiAgICAgIHN0RXZ0Omluc3RhbmNlSUQ9ImZkY2QyZDZhLWJmMmQtNDFkNS0wOTk0LWIxZTUwMDAwMDA3NiIKICAgICAgc3RFdnQ6d2hlbj0iMjAxNC0wMy0xMlQxMzo1NS0wNDowMCIKICAgICAgc3RFdnQ6c29mdHdhcmVBZ2VudD0iQWRvYmUgQWRvYmUgTWVkaWEgRW5jb2RlciBDQyAoTWFjaW50b3NoKSIKICAgICAgc3RFdnQ6Y2hhbmdlZD0iLyIvPgogICAgIDxyZGY6bGkKICAgICAgc3RFdnQ6YWN0aW9uPSJzYXZlZCIKICAgICAgc3RFdnQ6aW5zdGFuY2VJRD0iOTc3M2Q2ZDgtNTg0Mi00ZjdhLTBmYTAtZWIxZTAwMDAwMDc2IgogICAgICBzdEV2dDp3aGVuPSIyMDE0LTAzLTA1VDE5OjQ2OjExLTA1OjAwIgogICAgICBzdEV2dDpzb2Z0d2FyZUFnZW50PSJBZG9iZSBBZG9iZSBNZWRpYSBFbmNvZGVyIENDIChNYWNpbnRvc2gpIgogICAgICBzdEV2dDpjaGFuZ2VkPSIvIi8+CiAgICAgPHJkZjpsaQogICAgICBzdEV2dDphY3Rpb249InNhdmVkIgogICAgICBzdEV2dDppbnN0YW5jZUlEPSJ4bXAuaWlkOkJBQ0Q2NkE3OEYyMDY4MTE5MTA5QjNCMUQxRkI1RDE0IgogICAgICBzdEV2dDp3aGVuPSIyMDEzLTA0LTMwVDExOjAyOjM4LTA0OjAwIgogICAgICBzdEV2dDpzb2Z0d2FyZUFnZW50PSJBZG9iZSBBZG9iZSBNZWRpYSBFbmNvZGVyIDUuNS4wIgogICAgICBzdEV2dDpjaGFuZ2VkPSIvbWV0YWRhdGE7L2NvbnRlbnQiLz4KICAgICA8cmRmOmxpCiAgICAgIHN0RXZ0OmFjdGlvbj0ic2F2ZWQiCiAgICAgIHN0RXZ0Omluc3RhbmNlSUQ9InhtcC5paWQ6NDFDQkI4N0I5MTIwNjgxMTkxMDlCM0IxRDFGQjVEMTQiCiAgICAgIHN0RXZ0OndoZW49IjIwMTMtMDQtMzBUMTE6MTU6NDgtMDQ6MDAiCiAgICAgIHN0RXZ0OnNvZnR3YXJlQWdlbnQ9IkFkb2JlIEFkb2JlIE1lZGlhIEVuY29kZXIgNS41LjAiLz4KICAgICA8cmRmOmxpCiAgICAgIHN0RXZ0OmFjdGlvbj0ibW9kaWZpZWQiCiAgICAgIHN0RXZ0OnBhcmFtZXRlcnM9InVua25vd24gbW9kaWZpY2F0aW9ucyIvPgogICAgIDxyZGY6bGkKICAgICAgc3RFdnQ6YWN0aW9uPSJzYXZlZCIKICAgICAgc3RFdnQ6aW5zdGFuY2VJRD0iNTQxNDk3MzMtYjFhMC1mZDFkLTMwYWItZmUxOTAwMDAwMDc2IgogICAgICBzdEV2dDp3aGVuPSIyMDE0LTAzLTA1VDE4OjU1OjI5LTA1OjAwIgogICAgICBzdEV2dDpzb2Z0d2FyZUFnZW50PSJBZG9iZSBBZG9iZSBNZWRpYSBFbmNvZGVyIENDIChNYWNpbnRvc2gpIgogICAgICBzdEV2dDpjaGFuZ2VkPSIvIi8+CiAgICAgPHJkZjpsaQogICAgICBzdEV2dDphY3Rpb249InNhdmVkIgogICAgICBzdEV2dDppbnN0YW5jZUlEPSJ4bXAuaWlkOmU5ZDUzY2VjLTc0NjQtNGE3ZC04N2ZjLWMwYzM5MjYyYmYyNSIKICAgICAgc3RFdnQ6d2hlbj0iMjAxNC0wMy0wNVQxOTo0NjoxMS0wNTowMCIKICAgICAgc3RFdnQ6c29mdHdhcmVBZ2VudD0iQWRvYmUgQWRvYmUgTWVkaWEgRW5jb2RlciBDQyAoTWFjaW50b3NoKSIKICAgICAgc3RFdnQ6Y2hhbmdlZD0iLyIvPgogICAgIDxyZGY6bGkKICAgICAgc3RFdnQ6YWN0aW9uPSJzYXZlZCIKICAgICAgc3RFdnQ6aW5zdGFuY2VJRD0ieG1wLmlpZDplNGIxZWE1MC02ZGU0LTRkZGEtOTZkYy0xZGZhMDFlMzA1ZjEiCiAgICAgIHN0RXZ0OndoZW49IjIwMTQtMDMtMDVUMTk6NDY6MTEtMDU6MDAiCiAgICAgIHN0RXZ0OnNvZnR3YXJlQWdlbnQ9IkFkb2JlIEFkb2JlIE1lZGlhIEVuY29kZXIgQ0MgKE1hY2ludG9zaCkiCiAgICAgIHN0RXZ0OmNoYW5nZWQ9Ii9tZXRhZGF0YSIvPgogICAgIDxyZGY6bGkKICAgICAgc3RFdnQ6YWN0aW9uPSJzYXZlZCIKICAgICAgc3RFdnQ6aW5zdGFuY2VJRD0ieG1wLmlpZDowMGY5ZDIyMi03ZmM3LTQxZTQtYTc3ZS02MTFmMGUzM2JiN2EiCiAgICAgIHN0RXZ0OndoZW49IjIwMTQtMDMtMTJUMTM6NTUtMDQ6MDAiCiAgICAgIHN0RXZ0OnNvZnR3YXJlQWdlbnQ9IkFkb2JlIEFkb2JlIE1lZGlhIEVuY29kZXIgQ0MgKE1hY2ludG9zaCkiCiAgICAgIHN0RXZ0OmNoYW5nZWQ9Ii8iLz4KICAgICA8cmRmOmxpCiAgICAgIHN0RXZ0OmFjdGlvbj0ic2F2ZWQiCiAgICAgIHN0RXZ0Omluc3RhbmNlSUQ9InhtcC5paWQ6ZDBmZGRjMDUtM2M3NC00MzAwLTlhYjItMzU2YTMwM2VmNjEwIgogICAgICBzdEV2dDp3aGVuPSIyMDE0LTAzLTEyVDEzOjU1LTA0OjAwIgogICAgICBzdEV2dDpzb2Z0d2FyZUFnZW50PSJBZG9iZSBBZG9iZSBNZWRpYSBFbmNvZGVyIENDIChNYWNpbnRvc2gpIgogICAgICBzdEV2dDpjaGFuZ2VkPSIvbWV0YWRhdGEiLz4KICAgICA8cmRmOmxpCiAgICAgIHN0RXZ0OmFjdGlvbj0ic2F2ZWQiCiAgICAgIHN0RXZ0Omluc3RhbmNlSUQ9InhtcC5paWQ6MjEwYWI2NTAtNjkwZS00MzllLWI1NzktOWNkY2I1NjU3Y2JiIgogICAgICBzdEV2dDp3aGVuPSIyMDE0LTAzLTE0VDE3OjU0OjU4LTA0OjAwIgogICAgICBzdEV2dDpzb2Z0d2FyZUFnZW50PSJBZG9iZSBBZG9iZSBNZWRpYSBFbmNvZGVyIENDIChNYWNpbnRvc2gpIgogICAgICBzdEV2dDpjaGFuZ2VkPSIvIi8+CiAgICAgPHJkZjpsaQogICAgICBzdEV2dDphY3Rpb249InNhdmVkIgogICAgICBzdEV2dDppbnN0YW5jZUlEPSJ4bXAuaWlkOjJmMWY1ZDBlLWMyMjEtNDMyNC1hMDRlLTE3NDk5N2E0Y2U0ZSIKICAgICAgc3RFdnQ6d2hlbj0iMjAxNC0wMy0xNFQxNzo1NDo1OC0wNDowMCIKICAgICAgc3RFdnQ6c29mdHdhcmVBZ2VudD0iQWRvYmUgQWRvYmUgTWVkaWEgRW5jb2RlciBDQyAoTWFjaW50b3NoKSIKICAgICAgc3RFdnQ6Y2hhbmdlZD0iL21ldGFkYXRhIi8+CiAgICA8L3JkZjpTZXE+CiAgIDwveG1wTU06SGlzdG9yeT4KICAgPHhtcE1NOkRlcml2ZWRGcm9tCiAgICBzdFJlZjppbnN0YW5jZUlEPSJ4bXAuaWlkOmQwZmRkYzA1LTNjNzQtNDMwMC05YWIyLTM1NmEzMDNlZjYxMCIKICAgIHN0UmVmOmRvY3VtZW50SUQ9Ijc3ZjgyMzkxLWYyNjYtNzRlZS0wMTExLWFhZWUwMDAwMDA0OSIKICAgIHN0UmVmOm9yaWdpbmFsRG9jdW1lbnRJRD0ieG1wLmRpZDoyZTEzYzBhNC00ZDFjLTRmNDQtYjcwYi1lZDQyYmI5OTBhNTYiLz4KICAgPHhtcERNOnN0YXJ0VGltZWNvZGUKICAgIHhtcERNOnRpbWVGb3JtYXQ9IjI5OTdEcm9wVGltZWNvZGUiCiAgICB4bXBETTp0aW1lVmFsdWU9IjAwOzAwOzAwOzAwIi8+CiAgIDx4bXBETTphbHRUaW1lY29kZQogICAgeG1wRE06dGltZVZhbHVlPSIwMDswMDswMDswMCIKICAgIHhtcERNOnRpbWVGb3JtYXQ9IjI5OTdEcm9wVGltZWNvZGUiLz4KICAgPHhtcERNOmR1cmF0aW9uCiAgICB4bXBETTp2YWx1ZT0iMyIKICAgIHhtcERNOnNjYWxlPSIxMDAxLzMwMDAwIi8+CiAgPC9yZGY6RGVzY3JpcHRpb24+CiA8L3JkZjpSREY+CjwveDp4bXBtZXRhPgogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgCjw/eHBhY2tldCBlbmQ9InciPz4AVEJQTQAAAAcAAAAxMjEuOTdUWUVSAAAABQAAADIwMjFUSVQyAAAABAAAAHNtcwAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAD/+3BAAAAAAABLgAAACAAACXAAAAEBGAEYgAAAICGAY5AAAAQAggggYYkog6AAACkB+sPrD4CRVZUklKAIjen1HZOD0FgXYhAuCMU5byDkLVZ+AZw52k/FBVPqOQ0zrngPMsbPANM64+NQ2N/hXs9nkTL+PAQ9Rx8U974fx+CDviQ5rDDLX/qGJCQHgppuADxjGP/gFxcXd3d//d3/4rcuyAFwbnxUlnwLnwwXHA++TLn5eD/+U1EdsmPGQAQCDIhLwBH0lJKSAKYbGBhQaGMBoGMmuCWYA15pACGNg4BhIHA2ExekBbrpKqqIhxkF7bIVEaxIa4qhVwIjCjoSeanmu2IYyTvHrLCg1xbH8TdNf4rXWt//MLRTVw5pvKUf6E9Wd3LdSAqIIMiSyUTI3LwB9TVN+UsQ0T9B//twYIGAApYhS1U94AAwo3mqoKABDWidWvnHgBFBkSwrMpAC8JUUI3bFhS1rOPk7xpv/F2wJjEBnP3qEkb8k3/huTBPJUUoezeXVMN7/BD3HjsNhnVzzKG0oJdfv/F+TaASdtjt0AAF113qZVPrRBAFMIBszNhzjJ7AwBRxf6POtTTVoyWR5fb54/VsN7BnxFktw/x0q2tIUW94e5Pf4+t3xTN8Vvl/jX+P+mUJqbtolNySNyMIAfY3j+rXRkU/kQca4s1PVscbwyKNWXhgUpW7TuIob6lb4owt4hZupp9IiNP+/w7Br/8qoyy7ZXLYAAI+48pm5RL4ARPMWM0/+VgRT1+y2hRHaeV8JVTwnG8RuncY1NS0Qmot1skkk5qbIos7qVU9SkbO9d/WTWURRcbaUaBAEyI9nrf/7cGBsgAJ6JlVvceAKOeSrLeygAYh0l1OuPalg45KrtUSpLgCdEDGhQaZFUW2TRlmE4bfhb6lhtbAiOPOXQ4lJhWIh6WPPkLXpdfb4kv//UFRVqVQsGwuVlXnJ99FbzJysOhkYTUtytjeXNzKpIzsn94UR1AnsYLMQLBC003WpaK1utm1df/8xf/8ee6//9BzKcttm3owA/Ggt67quInJOfHUy2rumLy2x7Zpj6zvTs9BLBAx2Qw81GYxmbRW0v/Xml//5dpW/6pMB6YOgmbpYNuS8wHoMpKAwFd5QuSVfMLCjFlZfxXkZilgsUCNSO+hzkmDVh4ejVPYfEysW/6df0R////6FfaWNsIf21u9GAH4TX1JfDCc7BQ0cfX2WtBGNtWekgcrDk2pIA4UTIxVdbHNBa11I91r/+3BgdAAB+SXTS49qXDVkyq1p50sIeM1NLb1LcN4TKfWkNSwJqt/mRC//oEVkEWZnj/6gACIqgbx/qVgEPuKBYwo3AiUcGicSwhStakruJGnhbhbc4CkqYLI4lyUAI0uFtRw1MnOorKalpoJP/Rrov+XnSaATbn/CBhGcN4Q3SM/GFAswVhLKtisDLvTFGBDGMxKLAlCEYmKKaLmTWpOkipJ1srSZV9fkwj//yzsZLttkkAAAgxB1rDuu+sAw8uwBW4BiqVzFvFPxRlGuS3LpgP5XLbTYwmoaiuG6k2+o4Z7pytzPDLH79PS6u4jVX5P660VbdbZGGADhWNDDoAnALSAhVAREpSjisoq3CgNHpz2ftDc2MR+GCCRFwnqNkpsqig7qr7tqf/5ONv/5UHKyZrbJIgAAvov0//twYIaAAjgl0ntvklg6JMpcYG1LiHhpSa2/CTjykyn1NjUujlQJTiwQqcwIMMHPDhhFPQU8hscWFVgC0hyotVWRrRnytqxOLbFxScJUYjlq9K3zGjTLRQCoFj1uskpGTLbZJGAANV4ZkFPEIbYYIXA10Wey1RqjXP5FNWvJmSuHDdazIHSxcPqTszI9T1vU1G3V/Jy+uiOsk8AAEGgNE0tZhdstYWrNj4yWAPSiTGQBNUwkKGgFh0Cv9T5S25T13ChXfXgsuq2jWBglLYbC7roxZY+AADwaJ/5Yu9dipzFQy+WO0bXGjL7SGVWe1YatYzR6qtL/ypJoPHwgRUtRIEDr1YysCgENuqM3SAdZxC2orLsrc//////////////////////////////////////////////////7cGCQAAIrF9Brb3pMN0SqHWUtS8dATyOM7ecosInksY2g5P/////////////////////////////8gqMgAGF86WCXMNFAEwE10ke2e5D/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////+3BgqQACngfGoHrIqhPg+MQHOBVAAAEuAAAAIAAAJcAAAAT///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////twQP+ACKgAS4AAAAgAAAlwAAABAAABLgAAACAAACXAAAAE/////////////////////////////////////////////////////////wAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAP/7cED/gAioAEuAAAAIAAAJcAAAAQAAAS4AAAAgAAAlwAAABAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABUQUcAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAyMDE0AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA==""".strip())

class SoundPlayer:
    def __init__(self):
        pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
    def play_alert(self):
        try:
            sound = pygame.mixer.Sound(BytesIO(SOUND_ALERT_MP3))
            sound.play()
        except:
            pass

_sound_player = None

def play_alert_sound():
    global _sound_player
    if _sound_player is None:
        _sound_player = SoundPlayer()
    _sound_player.play_alert()

def send_packet(sock, packet: dict):
    data = json.dumps(packet).encode('utf-8')
    header = len(data).to_bytes(4, byteorder='big')
    sock.sendall(header + data)

class PacketReader:
    def __init__(self):
        self.buffer = b''
    def feed(self, chunk: bytes):
        self.buffer += chunk
    def pop_packets(self):
        packets = []
        while True:
            if len(self.buffer) < 4:
                break
            length = int.from_bytes(self.buffer[:4], byteorder='big')
            if len(self.buffer) < 4 + length:
                break
            raw = self.buffer[4:4 + length]
            self.buffer = self.buffer[4 + length:]
            try:
                packets.append(json.loads(raw.decode('utf-8')))
            except json.JSONDecodeError:
                pass
        return packets

class ScreenStream(QThread):
    def __init__(self, sock, transport, target='Director', fps=30):
        super().__init__()
        self.sock = sock
        self.transport = transport
        self.target = target
        self.running = False
        self.sct = mss.MSS()
        self.interval = 1.0 / fps

    def start_stream(self):
        if not self.running:
            self.running = True
            self.start()

    def stop_stream(self):
        self.running = False
        self.wait()

    def run(self):
        while self.running:
            try:
                monitor = self.sct.monitors[1]
                frame = self.sct.grab(monitor)
                img = np.array(frame)
                img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
                img_resized = cv2.resize(img, (800, 600), interpolation=cv2.INTER_LINEAR)
                ret, jpeg = cv2.imencode('.jpg', img_resized, [cv2.IMWRITE_JPEG_QUALITY, 75])
                if not ret:
                    time.sleep(self.interval)
                    continue
                img_str = base64.b64encode(jpeg.tobytes()).decode()
                if len(img_str) < 300000:
                    packet = {
                        'type': 'screen',
                        'to': self.target,
                        'data': self.transport.encrypt_text(img_str)
                    }
                    send_packet(self.sock, packet)
                time.sleep(self.interval)
            except:
                time.sleep(self.interval)

class USBMonitorThread(QThread):
    event_detected = pyqtSignal(str, str)

    def __init__(self):
        super().__init__()
        self.running = True
        self.monitor = None

    def get_current_devices(self):
        try:
            monitor = USBMonitor()
            devices = monitor.get_available_devices()
            result = []
            for device_id, device_info in devices.items():
                info = f"{device_info[ID_MODEL]} ({device_info[ID_MODEL_ID]} - {device_info[ID_VENDOR_ID]})"
                result.append(info)
            return result
        except Exception:
            return []

    def run(self):
        try:
            self.monitor = USBMonitor()

            def on_connect(device_id, device_info):
                if not self.running:
                    return
                info = f"{device_info[ID_MODEL]} ({device_info[ID_MODEL_ID]} - {device_info[ID_VENDOR_ID]})"
                self.event_detected.emit("Подключено", info)

            def on_disconnect(device_id, device_info):
                if not self.running:
                    return
                info = f"{device_info[ID_MODEL]} ({device_info[ID_MODEL_ID]} - {device_info[ID_VENDOR_ID]})"
                self.event_detected.emit("Отключено", info)

            self.monitor.start_monitoring(on_connect=on_connect, on_disconnect=on_disconnect)
            while self.running:
                time.sleep(0.5)
            self.monitor.stop_monitoring()
        except Exception:
            pass

    def stop(self):
        self.running = False

class AuthThread(QThread):
    auth_success = pyqtSignal(object, str, str, object, list)
    auth_failed = pyqtSignal(str)
    connection_error = pyqtSignal(str)
    pending_status = pyqtSignal()
    screen_request = pyqtSignal(object)

    def __init__(self, server_ip, username, password, port=5555):
        super().__init__()
        if ':' in server_ip:
            parts = server_ip.split(':')
            server_ip = parts[0]
            try:
                port = int(parts[1])
            except:
                port = 5555
        self.server_ip = server_ip
        self.username = username
        self.password = password
        self.port = port
        self.screen_stream = None
        self.transport = None

    def run(self):
        try:
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10.0)
            ssl_sock = context.wrap_socket(sock, server_hostname=self.server_ip)
            try:
                ssl_sock.connect((self.server_ip, self.port))
            except socket.error as e:
                self.connection_error.emit(f"Не удалось подключиться к {self.server_ip}:{self.port} - {str(e)}")
                return
            try:
                send_packet(ssl_sock, {
                    'username': self.username,
                    'password': hashlib.sha256(self.password.encode()).hexdigest()
                })
            except socket.error as e:
                self.connection_error.emit(f"Не удалось отправить данные авторизации - {str(e)}")
                ssl_sock.close()
                return
            self.transport = TransportCipher(self.password)
            reader = PacketReader()
            while True:
                try:
                    chunk = ssl_sock.recv(4096)
                    if not chunk:
                        break
                    reader.feed(chunk)
                    packets = reader.pop_packets()
                    approved_pkt = None
                    pending_packets = []
                    for pkt in packets:
                        ptype = pkt.get('type')
                        if ptype == 'approved':
                            approved_pkt = pkt
                        elif approved_pkt is not None:
                            pending_packets.append(pkt)
                        elif ptype == 'usb_info_request':
                            devices = []
                            try:
                                monitor = USBMonitor()
                                devs = monitor.get_available_devices()
                                devices.append("USB устройства:")
                                for device_id, device_info in devs.items():
                                    info = f"{device_info[ID_MODEL]} ({device_info[ID_MODEL_ID]} - {device_info[ID_VENDOR_ID]})"
                                    devices.append(info)
                                devices.append("Остальные параметры:")
                                devices.append(f"ОС: {platform.system()} {platform.release()}")
                                devices.append(f"Архитектура: {platform.machine()}")
                                devices.append(f"hostname: {socket.gethostname()}")
                            except Exception:
                                pass
                            try:
                                send_packet(ssl_sock, {
                                    'type': 'usb_info_response',
                                    'data': self.transport.encrypt_text(json.dumps(devices))
                                })
                            except:
                                pass
                        elif ptype == 'rejected':
                            if self.screen_stream:
                                self.screen_stream.stop_stream()
                            ssl_sock.close()
                            self.auth_failed.emit("Заявка отклонена администратором")
                            return
                        elif ptype == 'request_screen':
                            if self.screen_stream is None:
                                self.screen_stream = ScreenStream(ssl_sock, self.transport)
                            self.screen_stream.start_stream()
                            self.screen_request.emit(self.screen_stream)

                    if approved_pkt is not None:
                        blocker_hash = approved_pkt.get('blocker_hash', '')
                        path = os.path.join(process_blocker.CONFIG_DIR, "blocker_config.json")
                        process_blocker._atomic_write_json(path, {"password_hash": blocker_hash})
                        self.auth_success.emit(ssl_sock, self.username, self.password, self.screen_stream, pending_packets)
                        return

                except socket.timeout:
                    continue
                except Exception as e:
                    self.auth_failed.emit(f"Ошибка авторизации: {str(e)}")
                    ssl_sock.close()
                    return
        except Exception as e:
            self.connection_error.emit(f"Ошибка подключения: {str(e)}")

class ClientThread(QThread):
    message_received = pyqtSignal(str, str, str)
    notification_received = pyqtSignal(str)
    screen_requested = pyqtSignal()
    stop_screen_requested = pyqtSignal()
    history_received = pyqtSignal(list)
    file_notify_received = pyqtSignal(str, str, str, int, str)
    file_download_chunk_received = pyqtSignal(str, int, int, bytes)
    connection_error = pyqtSignal(str)
    block_access_received = pyqtSignal()

    def __init__(self, socket, username, password, usb_thread=None, initial_packets=None):
        super().__init__()
        self.socket = socket
        self.username = username
        self.password = password
        self.running = True
        self.download_buffers = {}
        self.reader = PacketReader()
        self.transport = TransportCipher(password)
        self.screen_stream = None
        self.usb_thread = usb_thread
        self._last_seen_lock = threading.Lock()
        self.last_seen = time.time()
        self._intentional_close = False
        self.initial_packets = initial_packets or []
        try:
            self.socket.settimeout(2.0)
        except Exception:
            pass

    def set_screen_stream(self, stream):
        if self.screen_stream:
            self.screen_stream.stop_stream()
        self.screen_stream = stream
        if stream:
            stream.sock = self.socket
            stream.transport = self.transport
            stream.start_stream()

    def _process_packet(self, packet):
        with self._last_seen_lock:
            self.last_seen = time.time()
        packet_type = packet.get('type')
        if packet_type == 'message':
            from_user = packet.get('from', 'Неизвестный')
            message = self.transport.decrypt_text(packet.get('message', ''))
            to_user = packet.get('to', 'general')
            self.message_received.emit(from_user, message, to_user)
        elif packet_type == 'notification':
            message = self.transport.decrypt_text(packet.get('message', ''))
            self.notification_received.emit(message)
        elif packet_type == 'request_screen':
            self.screen_requested.emit()
        elif packet_type == 'stop_screen':
            self.stop_screen_requested.emit()
        elif packet_type == 'history':
            messages = packet.get('messages', [])
            for msg in messages:
                if msg.get('type') == 'message':
                    msg['message'] = self.transport.decrypt_text(msg.get('message', ''))
            self.history_received.emit(messages)
        elif packet_type == 'file_notify':
            from_user = packet.get('from')
            filename = packet.get('filename')
            chat_type = packet.get('chat_type')
            filesize = packet.get('filesize')
            timestamp = packet.get('timestamp')
            self.file_notify_received.emit(from_user, filename, chat_type, filesize, timestamp)
        elif packet_type == 'file_download_chunk':
            file_id = packet.get('file_id')
            chunk_index = packet.get('chunk_index')
            total_chunks = packet.get('total_chunks')
            data_token = packet.get('data')
            chunk_data = self.transport.decrypt_bytes(data_token)
            self.file_download_chunk_received.emit(file_id, chunk_index, total_chunks, chunk_data)
        elif packet_type == 'usb_info_request':
            devices = []
            if self.usb_thread:
                devices = self.usb_thread.get_current_devices()
            try:
                send_packet(self.socket, {
                    'type': 'usb_info_response',
                    'data': self.transport.encrypt_text(json.dumps(devices))
                })
            except:
                pass
        elif packet_type == 'block_access':
            self.block_access_received.emit()
        elif packet_type == 'ping':
            try:
                send_packet(self.socket, {'type': 'pong'})
            except:
                pass

    def run(self):
        try:
            for packet in self.initial_packets:
                self._process_packet(packet)

            while self.running:
                try:
                    data = self.socket.recv(4096)
                    if not data:
                        break
                    self.reader.feed(data)
                    for packet in self.reader.pop_packets():
                        self._process_packet(packet)
                except socket.timeout:
                    continue
                except socket.error as e:
                    if not self._intentional_close:
                        self.connection_error.emit(f"Ошибка сокета: {str(e)}")
                    break
                except Exception as e:
                    if not self._intentional_close:
                        self.connection_error.emit(f"Ошибка: {str(e)}")
                    break
        except Exception as e:
            self.connection_error.emit(f"Ошибка: {str(e)}")
        finally:
            if self.socket:
                try:
                    self.socket.close()
                except:
                    pass

    def send_message(self, to_user, message):
        if self.socket:
            try:
                packet = {
                    'type': 'message',
                    'to': to_user,
                    'message': self.transport.encrypt_text(message)
                }
                send_packet(self.socket, packet)
                return True
            except:
                return False
        return False

    def send_screen(self, to_user, screen_data):
        if self.socket:
            try:
                packet = {
                    'type': 'screen',
                    'to': to_user,
                    'data': self.transport.encrypt_text(screen_data)
                }
                send_packet(self.socket, packet)
                return True
            except:
                return False
        return False

    def request_file(self, filename, from_user, chat_type, to_user):
        if self.socket:
            try:
                packet = {
                    'type': 'file_request',
                    'filename': filename,
                    'from_user': from_user,
                    'chat_type': chat_type,
                    'to_user': to_user
                }
                send_packet(self.socket, packet)
                return True
            except:
                return False
        return False

    def send_usb_event(self, action, device_info):
        if self.socket:
            try:
                payload = f"{action}: {device_info}"
                packet = {
                    'type': 'usb_event',
                    'data': self.transport.encrypt_text(payload)
                }
                send_packet(self.socket, packet)
                return True
            except:
                return False
        return False

    def stop(self):
        self.running = False
        if self.socket:
            try:
                self.socket.close()
            except:
                pass

class LoginDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.server_ip = ""
        self.username = ""
        self.password = ""
        self.auth_thread = None
        self.pending = False
        self.socket = None
        self.screen_stream = None
        self.pending_packets = []
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Asterion - Подключение")
        self.setFixedSize(450, 400)
        self.setStyleSheet("""
            QDialog {
                background-color: #2d2d3a;
            }
            QLabel {
                color: white;
                font-size: 15px;
                font-weight: 500;
            }
            QLineEdit {
                background-color: #3d3d4a;
                border: 1px solid #5a5a6a;
                border-radius: 6px;
                padding: 10px 12px;
                color: #e0e0e0;
                font-size: 15px;
            }
            QLineEdit:focus {
                border: 1px solid #4a6a8a;
            }
            QPushButton {
                background-color: #4a6a8a;
                border: none;
                border-radius: 6px;
                padding: 10px 25px;
                color: white;
                font-weight: bold;
                font-size: 15px;
            }
            QPushButton:hover {
                background-color: #5a7a9a;
            }
            QPushButton:pressed {
                background-color: #3a5a7a;
            }
        """)
        layout = QVBoxLayout()
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(15)
        title_label = QLabel("Asterion")
        title_label.setStyleSheet("font-size: 28px; font-weight: bold; color: #4a9a4a; margin-bottom: 10px;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        ip_label = QLabel("IP-адрес сервера:")
        layout.addWidget(ip_label)
        self.ip_input = QLineEdit()
        self.ip_input.setPlaceholderText("192.168.1.100")
        self.ip_input.setMinimumHeight(40)
        layout.addWidget(self.ip_input)
        name_label = QLabel("Ваше имя:")
        layout.addWidget(name_label)
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Иванов")
        self.name_input.setMinimumHeight(40)
        layout.addWidget(self.name_input)
        password_label = QLabel("Пароль сервера:")
        layout.addWidget(password_label)
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setPlaceholderText("Введите пароль")
        self.password_input.setMinimumHeight(40)
        layout.addWidget(self.password_input)
        layout.addSpacing(10)
        self.connect_btn = QPushButton("Подключиться")
        self.connect_btn.setMinimumHeight(45)
        self.connect_btn.clicked.connect(self.on_connect)
        layout.addWidget(self.connect_btn)
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #ffaa00; font-size: 14px;")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.hide()
        layout.addWidget(self.status_label)
        self.setLayout(layout)

    def on_connect(self):
        self.server_ip = self.ip_input.text().strip()
        self.username = self.name_input.text().strip()
        self.password = self.password_input.text().strip()
        if not self.server_ip or not self.username or not self.password:
            QMessageBox.warning(self, "Ошибка", "Заполните все поля")
            return
        self.connect_btn.setEnabled(False)
        self.connect_btn.setText("Подключение...")
        self.status_label.hide()
        self.auth_thread = AuthThread(self.server_ip, self.username, self.password)
        self.auth_thread.auth_success.connect(self.on_auth_success)
        self.auth_thread.auth_failed.connect(self.on_auth_failed)
        self.auth_thread.connection_error.connect(self.on_connection_error)
        self.auth_thread.pending_status.connect(self.on_pending)
        self.auth_thread.screen_request.connect(self.on_screen_request)
        self.auth_thread.start()

    def on_screen_request(self, stream):
        self.screen_stream = stream

    def on_pending(self):
        self.pending = True
        self.connect_btn.setText("Ожидание одобрения...")
        self.status_label.setText("Ожидание одобрения администратором...")
        self.status_label.show()

    def on_auth_success(self, sock, username, password, screen_stream, pending_packets):
        self.socket = sock
        self.username = username
        self.password = password
        self.screen_stream = screen_stream
        self.pending_packets = pending_packets
        self.accept()

    def on_auth_failed(self, error):
        self.connect_btn.setEnabled(True)
        self.connect_btn.setText("Подключиться")
        self.status_label.hide()
        QMessageBox.critical(self, "Ошибка авторизации", f"{error}")
        sys.exit(1)

    def on_connection_error(self, error):
        self.connect_btn.setEnabled(True)
        self.connect_btn.setText("Подключиться")
        self.status_label.hide()
        QMessageBox.critical(self, "Ошибка подключения", f"{error}")
        sys.exit(1)

    def get_socket_and_credentials(self):
        return self.socket, self.username, self.password, self.screen_stream, self.pending_packets

class MainWindow(QMainWindow):
    def __init__(self, sock, username, password, screen_stream=None, pending_packets=None):
        super().__init__()
        self.sock = sock
        self.username = username
        self.password = password
        self.client_thread = None
        self.screen_timer = None
        self.screen_active = False
        self.sct = mss.MSS()
        self.download_buffers = {}
        self.download_progress = None
        self.is_processing_download = False
        self.screen_stream = screen_stream
        if self.screen_stream:
            self.screen_stream.stop_stream()
            self.screen_stream = None
        self.pending_packets = pending_packets or []
        self.init_ui()
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowCloseButtonHint)
        self.usb_thread = USBMonitorThread()
        self.usb_thread.event_detected.connect(self.on_usb_event)
        self.usb_thread.start()
        self.start_client_thread()
        self._watchdog_timer = QTimer()
        self._watchdog_timer.timeout.connect(self._check_connection)
        self._watchdog_timer.start(5000)

    def _check_connection(self):
        if not self.client_thread:
            return
        with self.client_thread._last_seen_lock:
            last = self.client_thread.last_seen
        if time.time() - last > 30:
            self._watchdog_timer.stop()
            self.on_block_access()

    def init_ui(self):
        self.setWindowTitle(f"Asterion - {self.username}")
        self.setGeometry(100, 100, 1200, 700)
        self.setStyleSheet("""
            QMainWindow {
                background-color: #2d2d3a;
            }
            QTextBrowser {
                background-color: #3d3d4a;
                border: none;
                color: #e0e0e0;
                font-size: 14px;
            }
            QTextBrowser a {
                color: #4a9a4a;
                text-decoration: underline;
            }
            QLineEdit {
                background-color: #3d3d4a;
                border: 1px solid #5a5a6a;
                border-radius: 5px;
                padding: 8px;
                color: #e0e0e0;
                font-size: 14px;
            }
            QPushButton {
                background-color: #4a6a8a;
                border: none;
                border-radius: 5px;
                padding: 8px 15px;
                color: white;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #5a7a9a;
            }
            QPushButton:pressed {
                background-color: #3a5a7a;
            }
            QTabWidget::pane {
                background-color: #3d3d4a;
                border: none;
            }
            QTabBar::tab {
                background-color: #4a4a5a;
                color: #a0a0b0;
                padding: 10px 25px;
                border: none;
                font-size: 14px;
            }
            QTabBar::tab:selected {
                background-color: #5a6a8a;
                color: white;
            }
            QTabBar::tab:hover {
                background-color: #5a5a6a;
            }
        """)
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        central_widget.setLayout(layout)
        self.chat_tabs = QTabWidget()
        self.chat_tabs.setTabPosition(QTabWidget.TabPosition.North)
        self.general_chat = self.create_chat_widget()
        self.chat_tabs.addTab(self.general_chat, "Общий чат")
        self.private_chat = self.create_chat_widget()
        self.chat_tabs.addTab(self.private_chat, "Чат с Директором")
        layout.addWidget(self.chat_tabs)

    def create_chat_widget(self):
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(8)
        widget.setLayout(layout)
        chat_display = QTextBrowser()
        chat_display.setOpenExternalLinks(False)
        chat_display.setStyleSheet("""
            QTextBrowser {
                background-color: #3d3d4a;
                border: 1px solid #4a4a5a;
                border-radius: 6px;
                padding: 12px;
                color: #e0e0e0;
                font-size: 14px;
            }
            QTextBrowser a {
                color: #4a9a4a;
                text-decoration: underline;
            }
        """)
        chat_display.anchorClicked.connect(self.on_link_clicked)
        layout.addWidget(chat_display)
        input_layout = QHBoxLayout()
        input_layout.setSpacing(8)
        message_input = QLineEdit()
        message_input.setPlaceholderText("Введите сообщение...")
        message_input.setStyleSheet("""
            QLineEdit {
                background-color: #3d3d4a;
                border: 1px solid #5a5a6a;
                border-radius: 6px;
                padding: 10px 12px;
                color: #e0e0e0;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 1px solid #4a6a8a;
            }
        """)
        message_input.returnPressed.connect(lambda: self.send_message(message_input))
        attach_btn = QPushButton("📎")
        attach_btn.setFixedSize(38, 38)
        attach_btn.setStyleSheet("""
            QPushButton {
                background-color: #4a6a8a;
                border: none;
                border-radius: 6px;
                color: white;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #5a7a9a;
            }
            QPushButton:pressed {
                background-color: #3a5a7a;
            }
        """)
        attach_btn.clicked.connect(self.on_attach_clicked)
        send_btn = QPushButton("Тык")
        send_btn.setFixedSize(80, 38)
        send_btn.setStyleSheet("""
            QPushButton {
                background-color: #4a6a8a;
                border: none;
                border-radius: 6px;
                color: white;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #5a7a9a;
            }
            QPushButton:pressed {
                background-color: #3a5a7a;
            }
        """)
        send_btn.clicked.connect(lambda: self.send_message(message_input))
        input_layout.addWidget(message_input)
        input_layout.addWidget(attach_btn)
        input_layout.addWidget(send_btn)
        layout.addLayout(input_layout)
        widget.chat_display = chat_display
        widget.message_input = message_input
        return widget

    def append_chat_line(self, chat_display, line):
        chat_display.append(line)
        cursor = chat_display.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.setCharFormat(QTextCharFormat())
        chat_display.setTextCursor(cursor)

    def on_link_clicked(self, url):
        if self.is_processing_download:
            return
        self.is_processing_download = True
        try:
            if url.scheme() == "download":
                params = {}
                for part in url.query().split('&'):
                    if '=' in part:
                        k, v = part.split('=', 1)
                        params[k] = v
                filename = params.get('filename')
                from_user = params.get('from')
                chat_type = params.get('chat_type')
                to_user = params.get('to')
                if filename and from_user and chat_type and to_user:
                    current_widget = self.chat_tabs.currentWidget()
                    if current_widget:
                        chat_display = current_widget.chat_display
                        saved_html = chat_display.toHtml()
                        scrollbar = chat_display.verticalScrollBar()
                        saved_scroll = scrollbar.value() if scrollbar else None
                        chat_display.setUpdatesEnabled(False)
                        save_path, _ = QFileDialog.getSaveFileName(self, "Сохранить файл", filename)
                        chat_display.setHtml(saved_html)
                        if saved_scroll is not None:
                            scrollbar.setValue(saved_scroll)
                        chat_display.setUpdatesEnabled(True)
                        if not save_path:
                            return
                        self.download_file(filename, from_user, chat_type, to_user, save_path)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Произошла ошибка при скачивании: {str(e)}")
        finally:
            self.is_processing_download = False

    def download_file(self, filename, from_user, chat_type, to_user, save_path):
        self.download_buffers[save_path] = {
            'file_id': None,
            'chunks': {},
            'total_chunks': 0,
            'filename': filename
        }
        self.client_thread.request_file(filename, from_user, chat_type, to_user)
        self.download_progress = QProgressDialog(f"Скачивание {filename}...", "Отмена", 0, 100, self)
        self.download_progress.setWindowModality(Qt.WindowModality.WindowModal)
        self.download_progress.setMinimumDuration(0)
        self.download_progress.setValue(0)
        self.download_progress.canceled.connect(lambda: self.cancel_download(save_path))
        self.download_progress.show()

    def cancel_download(self, save_path):
        if save_path in self.download_buffers:
            del self.download_buffers[save_path]
        if self.download_progress:
            self.download_progress.close()

    def on_file_download_chunk(self, file_id, chunk_index, total_chunks, chunk_data):
        for save_path, info in list(self.download_buffers.items()):
            if info['file_id'] is None:
                info['file_id'] = file_id
                info['total_chunks'] = total_chunks
            if info['file_id'] == file_id:
                info['chunks'][chunk_index] = chunk_data
                progress = int((len(info['chunks']) / total_chunks) * 100)
                if self.download_progress:
                    self.download_progress.setValue(progress)
                if len(info['chunks']) == total_chunks:
                    if self.download_progress:
                        self.download_progress.setValue(100)
                    try:
                        raw_data = b"".join(info['chunks'][i] for i in range(total_chunks))
                        stego_data = self.embed_stego(raw_data)
                        with open(save_path, "wb") as f:
                            f.write(stego_data)
                        QMessageBox.information(self, "Успех", f"Файл {info['filename']} сохранён")
                    except Exception as e:
                        QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить файл: {str(e)}")
                    if self.download_progress:
                        self.download_progress.close()
                    if save_path in self.download_buffers:
                        del self.download_buffers[save_path]

    def embed_stego(self, data):
        chain = self.username
        try:
            old_enc = None
            if data.startswith(b'\x89PNG\r\n\x1a\n'):
                i = 8
                while i < len(data):
                    l = int.from_bytes(data[i:i+4], 'big')
                    t = data[i+4:i+8]
                    if t == b'tEXt':
                        c = data[i+8:i+8+l]
                        if c.startswith(b'asterion\x00'):
                            old_enc = c[9:].decode('utf-8')
                            break
                    i += 12 + l
            elif data.startswith(b'\xff\xd8\xff'):
                i = 2
                while i < len(data) - 1:
                    if data[i] == 0xFF and data[i+1] == 0xFE:
                        l = int.from_bytes(data[i+2:i+4], 'big')
                        c = data[i+4:i+4+l-2]
                        if c.startswith(b'asterion\x00'):
                            old_enc = c[9:].decode('utf-8')
                            break
                    elif data[i] == 0xFF and data[i+1] not in (0x00, 0xD9):
                        l = int.from_bytes(data[i+2:i+4], 'big')
                        i += 2 + l
                    else:
                        i += 1
            elif data.startswith(b'GIF8'):
                i = 0
                while i < len(data) - 1:
                    if data[i] == 0x21 and data[i+1] == 0xFE:
                        i += 2
                        p = []
                        while True:
                            if i >= len(data):
                                break
                            s = data[i]
                            i += 1
                            if s == 0:
                                break
                            p.append(data[i:i+s])
                            i += s
                        c = b''.join(p)
                        if c.startswith(b'asterion\x00'):
                            old_enc = c[9:].decode('utf-8')
                            break
                    i += 1
            else:
                try:
                    text = data.decode('utf-8')
                    bits = []
                    for ch in text:
                        if ch == '\u200b':
                            bits.append(0)
                        elif ch == '\u200c':
                            bits.append(1)
                    if len(bits) >= 32:
                        l = 0
                        for i in range(32):
                            l = (l << 1) | bits[i]
                        if 0 < l <= (len(bits) - 32) // 8:
                            eb = bits[32:32+l*8]
                            bb = bytearray(l)
                            for i in range(l):
                                b = 0
                                for j in range(8):
                                    b = (b << 1) | eb[i*8+j]
                                bb[i] = b
                            old_enc = bytes(bb).decode('utf-8')
                except:
                    try:
                        l = int.from_bytes(data[-4:], 'big')
                        if 0 < l <= len(data) - 4:
                            enc_data = data[-(4+l):-4]
                            test = self.client_thread.transport.decrypt_text(enc_data.decode('utf-8'))
                            if test and not test.startswith('['):
                                old_enc = enc_data.decode('utf-8')
                    except:
                        pass
            if old_enc:
                old = self.client_thread.transport.decrypt_text(old_enc)
                if old and not old.startswith('['):
                    chain = old + '_' + self.username
        except:
            pass
        try:
            enc = self.client_thread.transport.encrypt_text(chain).encode('utf-8')
            payload = len(enc).to_bytes(4, 'big') + enc
        except:
            return data
        if data.startswith(b'\x89PNG\r\n\x1a\n'):
            import zlib
            sig = data[:8]
            chunks = []
            i = 8
            while i < len(data):
                l = int.from_bytes(data[i:i+4], 'big')
                t = data[i+4:i+8]
                c = data[i+8:i+8+l]
                if t == b'tEXt' and c.startswith(b'asterion\x00'):
                    i += 12 + l
                    continue
                if t == b'IEND':
                    td = b'asterion\x00' + payload
                    tl = len(td)
                    tc = zlib.crc32(b'tEXt' + td) & 0xffffffff
                    chunks.append(tl.to_bytes(4, 'big') + b'tEXt' + td + tc.to_bytes(4, 'big'))
                chunks.append(data[i:i+12+l])
                i += 12 + l
            return sig + b''.join(chunks)
        elif data.startswith(b'\xff\xd8\xff'):
            marked = b'asterion\x00' + payload
            com = b'\xff\xfe' + (2 + len(marked)).to_bytes(2, 'big') + marked
            return data[:2] + com + data[2:]
        elif data.startswith(b'GIF8'):
            idx = data.rfind(b'\x3b')
            if idx == -1:
                return data
            marked = b'asterion\x00' + payload
            blocks = []
            o = 0
            while o < len(marked):
                ch = marked[o:o+255]
                blocks.append(bytes([len(ch)]) + ch)
                o += 255
            ext = b'\x21\xfe' + b''.join(blocks) + b'\x00'
            return data[:idx] + ext + data[idx:]
        else:
            try:
                text = data.decode('utf-8')
                clean = text.replace('\u200b', '').replace('\u200c', '')
                bits = []
                for b in payload:
                    for i in range(7, -1, -1):
                        bits.append((b >> i) & 1)
                stego = ''.join('\u200b' if b == 0 else '\u200c' for b in bits)
                prefix = None
                for line in clean.splitlines():
                    s = line.strip()
                    if s.startswith(('#', 'import ', 'from ', 'def ', 'class ', '@')):
                        prefix = '# '
                        break
                    if s.startswith(('// ', '/*', 'function ', 'const ', 'let ', 'var ')):
                        prefix = '// '
                        break
                    if s.startswith(('<!--', '<!DOCTYPE', '<?xml', '<html')):
                        prefix = None
                        break
                if prefix is None and any(line.strip().startswith('<') for line in clean.splitlines()):
                    if clean.endswith('\n'):
                        return (clean + '<!--' + stego + '-->\n').encode('utf-8')
                    else:
                        return (clean + '\n<!--' + stego + '-->\n').encode('utf-8')
                if prefix:
                    if clean.endswith('\n'):
                        return (clean + prefix + stego + '\n').encode('utf-8')
                    else:
                        return (clean + '\n' + prefix + stego + '\n').encode('utf-8')
                if '\n' in clean:
                    lines = clean.splitlines(keepends=True)
                    if lines[-1].endswith('\n'):
                        lines[-1] = lines[-1].rstrip('\n') + stego + '\n'
                    else:
                        lines[-1] = lines[-1] + stego
                    return ''.join(lines).encode('utf-8')
                return (clean + stego).encode('utf-8')
            except:
                try:
                    l = int.from_bytes(data[-4:], 'big')
                    if 0 < l < len(data) - 4:
                        enc_data = data[-(4+l):-4]
                        test = self.client_thread.transport.decrypt_text(enc_data.decode('utf-8'))
                        if test and not test.startswith('['):
                            data = data[:-(4+l)]
                except:
                    pass
                return data + enc + len(enc).to_bytes(4, 'big')
    def on_attach_clicked(self):
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getOpenFileName(self, "Выберите файл для отправки")
        if not file_path:
            return
        filename = os.path.basename(file_path)
        forbidden_extensions = ['.exe', '.appimage', '.bin', '.msi', '.dmg', '.pkg', '.deb', '.rpm']
        ext = os.path.splitext(filename)[1].lower()
        if ext in forbidden_extensions:
            QMessageBox.warning(self, "Ошибка", "Запрещённый тип файла")
            return
        filesize = os.path.getsize(file_path)
        if filesize > 500 * 1024 * 1024:
            QMessageBox.warning(self, "Ошибка", "Файл превышает 500 МБ")
            return
        current_tab = self.chat_tabs.currentWidget()
        tab_text = self.chat_tabs.tabText(self.chat_tabs.currentIndex())
        if tab_text == "Общий чат":
            chat_type = "general"
            to_user = "general"
        else:
            chat_type = "private"
            to_user = tab_text
        self.send_file(file_path, filename, chat_type, to_user)

    def send_file(self, file_path, filename, chat_type, to_user):
        chunk_size = 1024 * 1024
        filesize = os.path.getsize(file_path)
        total_chunks = (filesize + chunk_size - 1) // chunk_size
        file_id = f"{int(time.time())}_{self.username}_{filename}"
        progress = QProgressDialog(f"Отправка {filename}...", "Отмена", 0, total_chunks, self)
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.setMinimumDuration(0)
        progress.setValue(0)
        try:
            with open(file_path, "rb") as f:
                for i in range(total_chunks):
                    if progress.wasCanceled():
                        break
                    data = f.read(chunk_size)
                    data_token = self.client_thread.transport.encrypt_bytes(data)
                    packet = {
                        'type': 'file_chunk',
                        'file_id': file_id,
                        'chunk_index': i,
                        'data': data_token
                    }
                    if i == 0:
                        start_packet = {
                            'type': 'file_start',
                            'file_id': file_id,
                            'filename': filename,
                            'filesize': filesize,
                            'total_chunks': total_chunks,
                            'chat_type': chat_type,
                            'to': to_user
                        }
                        send_packet(self.client_thread.socket, start_packet)
                    send_packet(self.client_thread.socket, packet)
                    progress.setValue(i + 1)
                    QApplication.processEvents()
                if not progress.wasCanceled():
                    end_packet = {
                        'type': 'file_end',
                        'file_id': file_id,
                        'filename': filename,
                        'chat_type': chat_type,
                        'to': to_user
                    }
                    send_packet(self.client_thread.socket, end_packet)
                else:
                    QMessageBox.information(self, "Отмена", "Отправка файла отменена")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось отправить файл: {str(e)}")
        progress.close()

    def start_client_thread(self):
        self.client_thread = ClientThread(self.sock, self.username, self.password, self.usb_thread, self.pending_packets)
        if self.screen_stream:
            self.client_thread.set_screen_stream(self.screen_stream)
        self.client_thread.message_received.connect(self.on_message_received)
        self.client_thread.notification_received.connect(self.on_notification_received)
        self.client_thread.screen_requested.connect(self.on_screen_requested)
        self.client_thread.stop_screen_requested.connect(self.on_stop_screen_requested)
        self.client_thread.history_received.connect(self.on_history_received)
        self.client_thread.file_notify_received.connect(self.on_file_notify_received)
        self.client_thread.file_download_chunk_received.connect(self.on_file_download_chunk)
        self.client_thread.connection_error.connect(self.on_connection_error)
        self.client_thread.block_access_received.connect(self.on_block_access)
        self.client_thread.start()

    def on_block_access(self):
        if hasattr(self, 'usb_thread') and self.usb_thread:
            self.usb_thread.stop()
            self.usb_thread.wait()
        if self.client_thread:
            self.client_thread._intentional_close = True
        if self.sock:
            try:
                self.sock.shutdown(socket.SHUT_RDWR)
            except Exception:
                pass
            try:
                self.sock.close()
            except Exception:
                pass
        if self.client_thread:
            self.client_thread.stop()
            self.client_thread.wait(3000)
        if self.screen_timer:
            self.screen_timer.stop()
            self.screen_timer = None
        if self.screen_stream:
            self.screen_stream.stop_stream()
            self.screen_stream = None

        self.hide()

        process_blocker.run_blocker()

        self.show()
        self.reconnect()

    def reconnect(self):
        self.general_chat.chat_display.clear()
        self.private_chat.chat_display.clear()
        while self.chat_tabs.count() > 2:
            self.chat_tabs.removeTab(self.chat_tabs.count() - 1)
        if hasattr(self, 'download_progress') and self.download_progress:
            self.download_progress.close()
            self.download_progress = None
        self.download_buffers = {}
        self.screen_stream = None
        dialog = LoginDialog()
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.sock, self.username, self.password, screen_stream, pending_packets = dialog.get_socket_and_credentials()
            self.pending_packets = pending_packets
            self.start_client_thread()
            if screen_stream:
                self.client_thread.set_screen_stream(screen_stream)
        else:
            QApplication.quit()

    def on_file_notify_received(self, from_user, filename, chat_type, filesize, timestamp):
        play_alert_sound()
        safe_from_user = html.escape(from_user)
        safe_filename = html.escape(filename)
        safe_timestamp = html.escape(timestamp)
        safe_chat_type = html.escape(chat_type)
        if chat_type == "general":
            safe_to_user = "general"
        else:
            safe_to_user = html.escape(self.username)
        link = f'<a href="download://?filename={safe_filename}&from={safe_from_user}&chat_type={safe_chat_type}&to={safe_to_user}">Скачать</a>'
        msg = f"[{safe_timestamp}] {safe_from_user}: [Файл] {safe_filename} ({filesize} байт) {link}"
        if chat_type == "general":
            self.append_chat_line(self.general_chat.chat_display, msg)
        else:
            self.append_chat_line(self.private_chat.chat_display, msg)

    def on_connection_error(self, error):
        if hasattr(self, 'usb_thread') and self.usb_thread:
            self.usb_thread.stop()
            self.usb_thread.wait()
        self.close()
        QMessageBox.critical(None, "Ошибка подключения", f"Соединение потеряно: {error}")
        self.on_block_access()

    def on_history_received(self, messages):
        for msg in messages:
            if msg.get('type') == 'message':
                from_user = html.escape(msg.get('from', 'Неизвестный'))
                message = html.escape(msg.get('message', ''))
                timestamp = html.escape(msg.get('timestamp', ''))
                chat_type = msg.get('chat_type', 'general')
                if chat_type == 'general':
                    self.append_chat_line(self.general_chat.chat_display, f"[{timestamp}] {from_user}: {message}")
                else:
                    self.append_chat_line(self.private_chat.chat_display, f"[{timestamp}] {from_user}: {message}")
            elif msg.get('type') == 'file':
                from_user = html.escape(msg.get('from', 'Неизвестный'))
                filename = html.escape(msg.get('filename', ''))
                filesize = msg.get('filesize', 0)
                timestamp = html.escape(msg.get('timestamp', ''))
                chat_type = msg.get('chat_type', 'general')
                safe_chat_type = html.escape(chat_type)
                if chat_type == 'general':
                    safe_to_user = "general"
                else:
                    safe_to_user = html.escape(self.username)
                link = f'<a href="download://?filename={filename}&from={from_user}&chat_type={safe_chat_type}&to={safe_to_user}">Скачать</a>'
                line = f"[{timestamp}] {from_user}: [Файл] {filename} ({filesize} байт) {link}"
                if chat_type == 'general':
                    self.append_chat_line(self.general_chat.chat_display, line)
                else:
                    self.append_chat_line(self.private_chat.chat_display, line)

    def on_message_received(self, from_user, message, to_user):
        play_alert_sound()
        timestamp = datetime.now().strftime('%H:%M:%S')
        safe_from = html.escape(from_user)
        safe_msg = html.escape(message)
        line = f"[{timestamp}] {safe_from}: {safe_msg}"
        if to_user == "general":
            self.append_chat_line(self.general_chat.chat_display, line)
        else:
            self.append_chat_line(self.private_chat.chat_display, line)

    def on_notification_received(self, message):
        play_alert_sound()
        QMessageBox.information(self, "Уведомление от Директора", message)

    def on_screen_requested(self):
        self.screen_active = True
        self.start_screen_stream()

    def on_stop_screen_requested(self):
        self.screen_active = False
        if self.screen_timer:
            self.screen_timer.stop()
            self.screen_timer = None
        if self.screen_stream:
            self.screen_stream.stop_stream()
            self.screen_stream = None

    def start_screen_stream(self):
        if self.screen_timer is None:
            self.screen_timer = QTimer()
            self.screen_timer.timeout.connect(self.capture_and_send_screen)
            self.screen_timer.start(33)

    def capture_and_send_screen(self):
        if not self.screen_active:
            return
        try:
            monitor = self.sct.monitors[1]
            frame = self.sct.grab(monitor)
            img = np.array(frame)
            img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
            img_resized = cv2.resize(img, (800, 600), interpolation=cv2.INTER_LINEAR)
            ret, jpeg = cv2.imencode('.jpg', img_resized, [cv2.IMWRITE_JPEG_QUALITY, 75])
            if not ret:
                return
            img_str = base64.b64encode(jpeg.tobytes()).decode()
            if len(img_str) < 300000:
                self.client_thread.send_screen('Director', img_str)
        except Exception:
            pass

    def send_message(self, input_widget):
        message = input_widget.text().strip()
        if not message:
            return
        current_tab = self.chat_tabs.currentWidget()
        tab_text = self.chat_tabs.tabText(self.chat_tabs.currentIndex())
        timestamp = datetime.now().strftime('%H:%M:%S')
        safe_timestamp = html.escape(timestamp)
        safe_message = html.escape(message)
        if tab_text == "Общий чат":
            if self.client_thread.send_message('general', message):
                self.append_chat_line(self.general_chat.chat_display, f"[{safe_timestamp}] Я: {safe_message}")
                input_widget.clear()
        else:
            if self.client_thread.send_message('Director', message):
                self.append_chat_line(self.private_chat.chat_display, f"[{safe_timestamp}] Я: {safe_message}")
                input_widget.clear()

    def on_usb_event(self, action, device_info):
        if self.client_thread:
            self.client_thread.send_usb_event(action, device_info)

    def closeEvent(self, event):
        if hasattr(self, 'usb_thread') and self.usb_thread:
            self.usb_thread.stop()
            self.usb_thread.wait()
        event.ignore()
        self.hide()
        self.showMinimized()

def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    font = app.font()
    font.setFamily("Arial")
    font.setPointSize(10)
    app.setFont(font)
    login_dialog = LoginDialog()
    if login_dialog.exec() == QDialog.DialogCode.Accepted:
        sock, username, password, screen_stream, pending_packets = login_dialog.get_socket_and_credentials()
        main_window = MainWindow(sock, username, password, screen_stream, pending_packets)
        main_window.show()
        sys.exit(app.exec())
    else:
        sys.exit(0)

def _load_blocker_config():
    for path in [process_blocker.CONFIG_PATH, process_blocker.CONFIG_BACKUP_PATH]:
        if not os.path.exists(path):
            continue
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            continue
    return {}

is_from_plan = "--FromPlan" in sys.argv

if is_from_plan:
    config = _load_blocker_config()
    password_hash = config.get("password_hash", "")
    if password_hash:
        process_blocker.run_blocker(password_hash)
    sys.exit(0)
else:
    config = _load_blocker_config()
    password_hash = config.get("password_hash", "")
    if password_hash:
        process_blocker.run_blocker(password_hash)
        sys.exit()
    require_admin()
    setup_persistence()
    main()