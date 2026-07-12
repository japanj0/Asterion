import sys
import os

os.makedirs("admin", exist_ok=True)
os.makedirs("database", exist_ok=True)
import json
import sqlite3
import threading
import socket
import time
import hashlib
from datetime import datetime
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from crypto import CryptoManager


def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        try:
            hostname = socket.gethostname()
            return socket.gethostbyname(hostname)
        except:
            return "127.0.0.1"


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


crypto = CryptoManager()


class DatabaseManager:
    def __init__(self):
        self.conn = sqlite3.connect("database/messages.db", check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                from_user TEXT,
                to_user TEXT,
                message TEXT,
                timestamp TEXT
            )
        ''')
        self.conn.commit()

    def save_message(self, from_user, to_user, message):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        encrypted = crypto.encrypt_message(message)
        self.cursor.execute(
            "INSERT INTO messages (from_user, to_user, message, timestamp) VALUES (?, ?, ?, ?)",
            (from_user, to_user, encrypted, timestamp)
        )
        self.conn.commit()
        return timestamp

    def get_messages(self, to_user=None):
        if to_user:
            self.cursor.execute(
                "SELECT from_user, message, timestamp FROM messages WHERE to_user=? OR to_user='all' ORDER BY timestamp",
                (to_user,)
            )
        else:
            self.cursor.execute(
                "SELECT from_user, message, timestamp FROM messages WHERE to_user='all' ORDER BY timestamp")
        return self.cursor.fetchall()

    def get_private_messages(self, user1, user2):
        self.cursor.execute(
            """SELECT from_user, message, timestamp FROM messages 
               WHERE (to_user=? AND from_user=?) OR (to_user=? AND from_user=?) 
               ORDER BY timestamp""",
            (user2, user1, user1, user2)
        )
        return self.cursor.fetchall()

    def get_all_messages_for_user(self, username):
        self.cursor.execute(
            """SELECT from_user, message, timestamp FROM messages 
               WHERE to_user=? OR to_user='all' OR from_user=?
               ORDER BY timestamp""",
            (username, username)
        )
        return self.cursor.fetchall()

    def get_all_messages(self):
        self.cursor.execute(
            "SELECT from_user, message, timestamp FROM messages ORDER BY timestamp"
        )
        return self.cursor.fetchall()


db = DatabaseManager()


class ServerThread(QThread):
    message_received = pyqtSignal(str, str, str)
    screen_received = pyqtSignal(str, str)
    user_connected = pyqtSignal(str)
    user_disconnected = pyqtSignal(str)
    auth_failed = pyqtSignal(str)

    def __init__(self, server_password, port=5555):
        super().__init__()
        self.port = port
        self.clients = {}
        self.running = True
        self.server_password_hash = hash_password(server_password)

    def run(self):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind(('0.0.0.0', self.port))
        self.server.listen(10)
        self.server.settimeout(1.0)

        while self.running:
            try:
                client_socket, addr = self.server.accept()

                auth_data = client_socket.recv(1024).decode()
                try:
                    auth_packet = json.loads(auth_data)
                    username = auth_packet.get('username')
                    password = auth_packet.get('password')

                    if not username or not password:
                        client_socket.send(json.dumps({'status': 'failed', 'error': 'Пустые учетные данные'}).encode())
                        client_socket.close()
                        continue

                    password_hash = hash_password(password)

                    if password_hash == self.server_password_hash:
                        client_socket.send(json.dumps({'status': 'success'}).encode())
                        self.clients[username] = {'socket': client_socket, 'addr': addr}
                        self.user_connected.emit(username)
                        client_thread = threading.Thread(target=self.handle_client, args=(client_socket, username))
                        client_thread.daemon = True
                        client_thread.start()
                    else:
                        client_socket.send(json.dumps({'status': 'failed', 'error': 'Неверный пароль'}).encode())
                        client_socket.close()
                        self.auth_failed.emit(username)
                except Exception as e:
                    client_socket.send(json.dumps({'status': 'failed', 'error': str(e)}).encode())
                    client_socket.close()

            except socket.timeout:
                continue
            except Exception as e:
                break

    def handle_client(self, client_socket, username):
        try:
            while self.running:
                data = client_socket.recv(4096)
                if not data:
                    break

                try:
                    decoded = data.decode()
                    packet = json.loads(decoded)
                    packet_type = packet.get('type')

                    if packet_type == 'message':
                        to_user = packet.get('to')
                        message = packet.get('message')
                        db.save_message(username, to_user, message)
                        self.message_received.emit(username, message, to_user)

                        if to_user == 'all':
                            for user, info in self.clients.items():
                                if user != username:
                                    try:
                                        info['socket'].send(json.dumps({
                                            'type': 'message',
                                            'from': username,
                                            'message': message,
                                            'to': 'all'
                                        }).encode())
                                    except:
                                        pass
                        else:
                            if to_user in self.clients:
                                try:
                                    self.clients[to_user]['socket'].send(json.dumps({
                                        'type': 'message',
                                        'from': username,
                                        'message': message,
                                        'to': to_user
                                    }).encode())
                                except:
                                    pass

                    elif packet_type == 'screen':
                        to_user = packet.get('to')
                        screen_data = packet.get('data')
                        self.screen_received.emit(username, screen_data)

                    elif packet_type == 'decrypt_request':
                        encrypted_msg = packet.get('message')
                        decrypted = crypto.decrypt_message(encrypted_msg)
                        client_socket.send(json.dumps({
                            'type': 'decrypt_response',
                            'message': decrypted
                        }).encode())

                except json.JSONDecodeError:
                    pass

        except:
            pass
        finally:
            client_socket.close()
            self.user_disconnected.emit(username)
            if username in self.clients:
                del self.clients[username]

    def send_notification(self, to_user, message):
        if to_user in self.clients:
            try:
                self.clients[to_user]['socket'].send(json.dumps({
                    'type': 'notification',
                    'from': 'Director',
                    'message': message
                }).encode())
                return True
            except:
                return False
        return False

    def send_history(self, username):
        if username in self.clients:
            try:
                history = db.get_all_messages_for_user(username)
                history_data = []
                for from_user, msg, ts in history:
                    if from_user == 'Director' or from_user == username:
                        try:
                            decrypted = crypto.decrypt_message(msg)
                            history_data.append({
                                'from': from_user,
                                'message': decrypted,
                                'timestamp': ts
                            })
                        except:
                            history_data.append({
                                'from': from_user,
                                'message': '[Зашифровано]',
                                'timestamp': ts
                            })

                if history_data:
                    self.clients[username]['socket'].send(json.dumps({
                        'type': 'history',
                        'messages': history_data
                    }).encode())
            except:
                pass

    def stop(self):
        self.running = False
        for client in self.clients.values():
            try:
                client['socket'].close()
            except:
                pass
        self.server.close()


class ScreenWindow(QWidget):
    def __init__(self, username, parent=None):
        super().__init__(parent)
        self.username = username
        self.setWindowTitle(f"Экран - {username}")
        self.setGeometry(200, 200, 800, 600)
        self.setStyleSheet("background-color: #1d1d2a;")

        layout = QVBoxLayout()
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setStyleSheet("background-color: #1d1d2a; color: #6a6a7a; font-size: 18px;")
        self.image_label.setText("Ожидание данных экрана...")
        layout.addWidget(self.image_label)
        self.setLayout(layout)

    def update_screen(self, img_data):
        try:
            from io import BytesIO
            import base64
            from PyQt6.QtGui import QPixmap

            img_bytes = base64.b64decode(img_data)
            pixmap = QPixmap()
            pixmap.loadFromData(img_bytes, "JPEG")

            if not pixmap.isNull():
                scaled = pixmap.scaled(
                    self.image_label.width() - 20,
                    self.image_label.height() - 20,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                self.image_label.setPixmap(scaled)
                self.image_label.setText("")
            else:
                self.image_label.setText("Не удалось загрузить изображение")
        except Exception as e:
            self.image_label.setText(f"Ошибка: {str(e)}")


class IpDisplayWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        self.update_ip()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 5, 10, 5)
        layout.setSpacing(8)

        self.ip_label = QLabel("0.0.0.0")
        self.ip_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.ip_label.setStyleSheet("""
            color: #4a9a4a;
            font-size: 22px;
            font-weight: bold;
            background-color: #2d2d3a;
            padding: 12px;
            border-radius: 8px;
            border: 2px solid #4a6a8a;
        """)
        layout.addWidget(self.ip_label)

        self.setLayout(layout)
        self.setStyleSheet("background-color: #2d2d3a; border: none;")

    def update_ip(self):
        ip = get_local_ip()
        self.ip_label.setText(ip)


class ServerPasswordDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Asterion - Пароль сервера")
        self.setFixedSize(450, 280)
        self.setStyleSheet("""
            QDialog {
                background-color: #2d2d3a;
            }
            QLabel {
                color: white;
                font-size: 15px;
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

        sub_label = QLabel("Установите пароль сервера")
        sub_label.setStyleSheet("font-size: 16px; color: #8a8a9a; margin-bottom: 10px;")
        sub_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(sub_label)

        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setPlaceholderText("Введите пароль")
        self.password_input.setMinimumHeight(40)
        self.password_input.returnPressed.connect(self.accept)
        layout.addWidget(self.password_input)

        self.confirm_input = QLineEdit()
        self.confirm_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm_input.setPlaceholderText("Подтвердите пароль")
        self.confirm_input.setMinimumHeight(40)
        self.confirm_input.returnPressed.connect(self.accept)
        layout.addWidget(self.confirm_input)

        layout.addSpacing(10)

        start_btn = QPushButton("Запустить сервер")
        start_btn.setMinimumHeight(45)
        start_btn.clicked.connect(self.accept)
        layout.addWidget(start_btn)

        self.setLayout(layout)

    def get_password(self):
        pwd1 = self.password_input.text().strip()
        pwd2 = self.confirm_input.text().strip()
        if pwd1 and pwd2 and pwd1 == pwd2:
            return pwd1
        return None


class MainWindow(QMainWindow):
    def __init__(self, server_password):
        super().__init__()
        self.server_password = server_password
        self.server_thread = None
        self.current_chat = "all"
        self.screen_windows = {}
        self.init_ui()
        self.load_all_history()
        self.start_server()

    def init_ui(self):
        self.setWindowTitle("Asterion - Директор")
        self.setGeometry(100, 100, 1400, 800)

        font = self.font()
        font.setPointSize(10)
        self.setFont(font)

        self.setStyleSheet("""
            QMainWindow {
                background-color: #2d2d3a;
            }
            QListWidget {
                background-color: #3d3d4a;
                border: none;
                color: #e0e0e0;
                font-size: 14px;
            }
            QListWidget::item {
                padding: 12px;
                border-bottom: 1px solid #4a4a5a;
            }
            QListWidget::item:selected {
                background-color: #4a6a8a;
            }
            QListWidget::item:hover {
                background-color: #4a4a5a;
            }
            QTextEdit {
                background-color: #3d3d4a;
                border: none;
                color: #e0e0e0;
                font-size: 14px;
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
        main_layout = QHBoxLayout()
        central_widget.setLayout(main_layout)

        left_panel = QWidget()
        left_panel.setFixedWidth(300)
        left_layout = QVBoxLayout()
        left_panel.setLayout(left_layout)

        self.ip_display = IpDisplayWidget()
        left_layout.addWidget(self.ip_display)

        employees_label = QLabel("Сотрудники")
        employees_label.setStyleSheet("color: white; font-size: 16px; font-weight: bold; padding: 10px;")
        left_layout.addWidget(employees_label)

        self.user_list = QListWidget()
        self.user_list.itemClicked.connect(self.on_user_clicked)
        left_layout.addWidget(self.user_list)

        main_layout.addWidget(left_panel)

        right_panel = QWidget()
        right_layout = QVBoxLayout()
        right_panel.setLayout(right_layout)

        self.chat_tabs = QTabWidget()
        self.chat_tabs.setTabPosition(QTabWidget.TabPosition.North)

        self.general_chat = self.create_chat_widget()
        self.chat_tabs.addTab(self.general_chat, "Общий чат")

        right_layout.addWidget(self.chat_tabs)
        main_layout.addWidget(right_panel)

        self.private_chats = {}

    def load_all_history(self):
        all_messages = db.get_all_messages()
        for from_user, msg, ts in all_messages:
            try:
                decrypted = crypto.decrypt_message(msg)
                if from_user == "Director":
                    self.general_chat.chat_display.append(f"[{ts}] Я: {decrypted}")
                else:
                    self.general_chat.chat_display.append(f"[{ts}] {from_user}: {decrypted}")
            except:
                self.general_chat.chat_display.append(f"[{ts}] {from_user}: [Зашифровано]")

    def create_chat_widget(self):
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(8)
        widget.setLayout(layout)

        chat_display = QTextEdit()
        chat_display.setReadOnly(True)
        chat_display.setStyleSheet("""
            QTextEdit {
                background-color: #3d3d4a;
                border: 1px solid #4a4a5a;
                border-radius: 6px;
                padding: 12px;
                color: #e0e0e0;
                font-size: 14px;
            }
        """)
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
        input_layout.addWidget(send_btn)
        layout.addLayout(input_layout)

        widget.chat_display = chat_display
        widget.message_input = message_input
        return widget

    def start_server(self):
        self.server_thread = ServerThread(self.server_password)
        self.server_thread.message_received.connect(self.on_message_received)
        self.server_thread.user_connected.connect(self.on_user_connected)
        self.server_thread.user_disconnected.connect(self.on_user_disconnected)
        self.server_thread.auth_failed.connect(self.on_auth_failed)
        self.server_thread.screen_received.connect(self.on_screen_received)
        self.server_thread.start()

    def on_screen_received(self, username, screen_data):
        if username not in self.screen_windows:
            self.screen_windows[username] = ScreenWindow(username)
            self.screen_windows[username].show()
        self.screen_windows[username].update_screen(screen_data)

    def on_auth_failed(self, username):
        pass

    def on_user_connected(self, username):
        self.user_list.addItem(username)

        if username not in self.private_chats:
            chat_widget = self.create_chat_widget()
            self.chat_tabs.addTab(chat_widget, username)
            self.private_chats[username] = chat_widget

            history = db.get_private_messages("Director", username)
            for from_user, msg, ts in history:
                try:
                    decrypted = crypto.decrypt_message(msg)
                    display_name = "Я" if from_user == "Director" else from_user
                    chat_widget.chat_display.append(f"[{ts}] {display_name}: {decrypted}")
                except:
                    chat_widget.chat_display.append(f"[{ts}] {from_user}: [Зашифровано]")

        self.server_thread.send_history(username)

    def on_user_disconnected(self, username):
        items = self.user_list.findItems(username, Qt.MatchFlag.MatchExactly)
        for item in items:
            self.user_list.takeItem(self.user_list.row(item))

        if username in self.screen_windows:
            self.screen_windows[username].close()
            del self.screen_windows[username]

    def on_message_received(self, from_user, message, to_user):
        try:
            decrypted = crypto.decrypt_message(message)
        except:
            decrypted = "[Зашифровано]"

        if to_user == "all":
            self.general_chat.chat_display.append(f"[{datetime.now().strftime('%H:%M:%S')}] {from_user}: {decrypted}")
        else:
            if from_user in self.private_chats:
                self.private_chats[from_user].chat_display.append(
                    f"[{datetime.now().strftime('%H:%M:%S')}] {from_user}: {decrypted}")

    def send_message(self, input_widget):
        message = input_widget.text().strip()
        if not message:
            return

        current_tab = self.chat_tabs.currentWidget()
        tab_text = self.chat_tabs.tabText(self.chat_tabs.currentIndex())

        if tab_text == "Общий чат":
            to_user = "all"
            db.save_message("Director", "all", message)
            self.general_chat.chat_display.append(f"[{datetime.now().strftime('%H:%M:%S')}] Я: {message}")

            for user, info in self.server_thread.clients.items():
                try:
                    info['socket'].send(json.dumps({
                        'type': 'message',
                        'from': 'Director',
                        'message': message,
                        'to': 'all'
                    }).encode())
                except:
                    pass
        else:
            to_user = tab_text
            if to_user in self.private_chats:
                db.save_message("Director", to_user, message)
                self.private_chats[to_user].chat_display.append(
                    f"[{datetime.now().strftime('%H:%M:%S')}] Я: {message}")

                if to_user in self.server_thread.clients:
                    try:
                        self.server_thread.clients[to_user]['socket'].send(json.dumps({
                            'type': 'message',
                            'from': 'Director',
                            'message': message,
                            'to': to_user
                        }).encode())
                    except:
                        pass

        input_widget.clear()

    def on_user_clicked(self, item):
        username = item.text()
        menu = QMenu()
        menu.setStyleSheet("background-color: #3d3d4a; color: white; font-size: 13px;")

        view_screen = menu.addAction("Просмотр экрана")
        send_notification = menu.addAction("Отправить уведомление")

        action = menu.exec(QCursor.pos())

        if action == view_screen:
            if username in self.server_thread.clients:
                try:
                    self.server_thread.clients[username]['socket'].send(json.dumps({
                        'type': 'request_screen',
                        'from': 'Director'
                    }).encode())
                except:
                    QMessageBox.warning(self, "Ошибка", f"Не удалось отправить запрос {username}")
            else:
                QMessageBox.warning(self, "Ошибка", f"Пользователь {username} не в сети")

        elif action == send_notification:
            dialog = QDialog(self)
            dialog.setWindowTitle("Отправить уведомление")
            dialog.setFixedSize(450, 250)
            dialog.setStyleSheet("""
                QDialog {
                    background-color: #3d3d4a;
                }
                QLabel {
                    color: white;
                    font-size: 14px;
                }
                QTextEdit {
                    background-color: #4a4a5a;
                    border: 1px solid #5a5a6a;
                    border-radius: 6px;
                    color: #e0e0e0;
                    font-size: 14px;
                    padding: 10px;
                }
                QTextEdit:focus {
                    border: 1px solid #4a6a8a;
                }
                QPushButton {
                    background-color: #4a6a8a;
                    border: none;
                    border-radius: 6px;
                    padding: 8px 20px;
                    color: white;
                    font-weight: bold;
                    font-size: 14px;
                }
                QPushButton:hover {
                    background-color: #5a7a9a;
                }
            """)

            layout = QVBoxLayout()
            layout.setContentsMargins(30, 30, 30, 30)
            layout.setSpacing(12)

            label = QLabel(f"Уведомление для {username}:")
            layout.addWidget(label)

            text_input = QTextEdit()
            text_input.setMinimumHeight(80)
            layout.addWidget(text_input)

            btn_layout = QHBoxLayout()
            btn_layout.setSpacing(10)
            send_btn = QPushButton("Отправить")
            send_btn.setMinimumHeight(40)
            cancel_btn = QPushButton("Отмена")
            cancel_btn.setMinimumHeight(40)
            cancel_btn.setStyleSheet("""
                QPushButton {
                    background-color: #5a4a4a;
                    border: none;
                    border-radius: 6px;
                    padding: 8px 20px;
                    color: white;
                    font-weight: bold;
                    font-size: 14px;
                }
                QPushButton:hover {
                    background-color: #6a5a5a;
                }
            """)

            btn_layout.addWidget(send_btn)
            btn_layout.addWidget(cancel_btn)
            layout.addLayout(btn_layout)

            dialog.setLayout(layout)

            send_btn.clicked.connect(lambda: self.send_notification_action(dialog, username, text_input.toPlainText()))
            cancel_btn.clicked.connect(dialog.reject)

            dialog.exec()

    def send_notification_action(self, dialog, username, message):
        if not message.strip():
            QMessageBox.warning(self, "Ошибка", "Введите текст уведомления")
            return

        if self.server_thread.send_notification(username, message):
            dialog.accept()
        else:
            QMessageBox.warning(self, "Ошибка", f"Не удалось отправить уведомление {username}")

    def closeEvent(self, event):
        if self.server_thread:
            self.server_thread.stop()
            self.server_thread.wait()
        event.accept()


def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')

    font = app.font()
    font.setFamily("Arial")
    font.setPointSize(10)
    app.setFont(font)

    password_dialog = ServerPasswordDialog()

    while True:
        if password_dialog.exec() == QDialog.DialogCode.Accepted:
            password = password_dialog.get_password()
            if password:
                break
            else:
                QMessageBox.warning(None, "Ошибка", "Пароли не совпадают или пустые")
        else:
            sys.exit(0)

    window = MainWindow(password)
    window.show()
    sys.exit(app.exec())


main()