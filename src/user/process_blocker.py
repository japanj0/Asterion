import sys
import os
import json
import hashlib
import platform
import subprocess
import tempfile
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton
from PyQt6.QtCore import Qt, QEventLoop
from PyQt6.QtGui import QKeyEvent

CONFIG_PATH = os.path.join(tempfile.gettempdir(), "asterion_blocker_config.json")

class BlockerWindow(QWidget):
    def __init__(self, password_hash):
        super().__init__()
        self.password_hash = password_hash
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
        if hashlib.sha256(entered.encode('utf-8')).hexdigest() == self.password_hash:
            self.remove_persistence()
            if os.path.exists(CONFIG_PATH):
                try:
                    os.remove(CONFIG_PATH)
                except:
                    pass
            if self.loop and self.loop.isRunning():
                self.loop.quit()
            self.close()
            sys.exit()
        else:
            self.pass_input.clear()
            self.pass_input.setPlaceholderText("Неверный пароль")
            self.pass_input.setFocus()

    def remove_persistence(self):
        system = platform.system()
        if system == "Windows":
            try:
                subprocess.run(["schtasks", "/delete", "/tn", "AsterionBlocker", "/f"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except:
                pass
            try:
                import winreg
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_SET_VALUE)
                winreg.DeleteValue(key, "AsterionBlocker")
                winreg.CloseKey(key)
            except:
                pass
        elif system == "Linux":
            autostart_path = os.path.expanduser("~/.config/autostart/asterion-blocker.desktop")
            if os.path.exists(autostart_path):
                try:
                    os.remove(autostart_path)
                except:
                    pass
            systemd_path = os.path.expanduser("~/.config/systemd/user/asterion-blocker.service")
            if os.path.exists(systemd_path):
                try:
                    subprocess.run(["systemctl", "--user", "disable", "asterion-blocker"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    os.remove(systemd_path)
                except:
                    pass
        elif system == "Darwin":
            plist_path = os.path.expanduser("~/Library/LaunchAgents/com.asterion.blocker.plist")
            if os.path.exists(plist_path):
                try:
                    subprocess.run(["launchctl", "unload", plist_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    os.remove(plist_path)
                except:
                    pass

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

def setup_persistence():
    system = platform.system()
    script_path = os.path.abspath(sys.argv[0])
    if system == "Windows":
        try:
            subprocess.run([
                "schtasks", "/create", "/tn", "AsterionBlocker", "/tr", f'"{sys.executable}" "{script_path}"',
                "/sc", "onlogon", "/rl", "highest", "/f"
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            return
        except:
            pass
        try:
            import winreg
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_SET_VALUE)
            winreg.SetValueEx(key, "AsterionBlocker", 0, winreg.REG_SZ, f'"{sys.executable}" "{script_path}"')
            winreg.CloseKey(key)
        except:
            pass
    elif system == "Linux":
        os.makedirs(os.path.expanduser("~/.config/autostart"), exist_ok=True)
        desktop_content = f"""[Desktop Entry]
Type=Application
Name=AsterionBlocker
Exec={sys.executable} {script_path}
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
"""
        with open(os.path.expanduser("~/.config/autostart/asterion-blocker.desktop"), "w") as f:
            f.write(desktop_content)
        os.chmod(os.path.expanduser("~/.config/autostart/asterion-blocker.desktop"), 0o755)
        systemd_dir = os.path.expanduser("~/.config/systemd/user")
        os.makedirs(systemd_dir, exist_ok=True)
        service_content = f"""[Unit]
Description=Asterion Blocker
After=graphical-session.target

[Service]
Type=simple
ExecStart={sys.executable} {script_path}
Restart=always
RestartSec=5

[Install]
WantedBy=default.target
"""
        with open(os.path.join(systemd_dir, "asterion-blocker.service"), "w") as f:
            f.write(service_content)
        try:
            subprocess.run(["systemctl", "--user", "daemon-reload"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.run(["systemctl", "--user", "enable", "asterion-blocker"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except:
            pass
    elif system == "Darwin":
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
    <true/>
</dict>
</plist>"""
        plist_path = os.path.expanduser("~/Library/LaunchAgents/com.asterion.blocker.plist")
        with open(plist_path, "w") as f:
            f.write(plist_content)
        try:
            subprocess.run(["launchctl", "load", plist_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except:
            pass

def run_blocker(password_hash):
    with open(CONFIG_PATH, "w") as f:
        json.dump({"password_hash": password_hash}, f)
    setup_persistence()
    app = QApplication.instance() or QApplication(sys.argv)
    window = BlockerWindow(password_hash)
    window.showFullScreen()
    window.raise_()
    window.activateWindow()
    window.pass_input.setFocus()

    loop = QEventLoop()
    window.loop = loop
    loop.exec()

    window.deleteLater()


if os.path.exists(CONFIG_PATH):
    with open(CONFIG_PATH, "r") as f:
        config = json.load(f)
    password_hash = config.get("password_hash", "")
    if password_hash:
        run_blocker(password_hash)
