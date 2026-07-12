import sys
import json
import threading
import socket
import time
from datetime import datetime
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from crypto import UserCrypto


class AuthThread(QThread):
    auth_success = pyqtSignal()
    auth_failed = pyqtSignal(str)
    connection_error = pyqtSignal(str)

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

    def run(self):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10.0)

            try:
                sock.connect((self.server_ip, self.port))
            except socket.error as e:
                self.connection_error.emit(f"Не удалось подключиться к {self.server_ip}:{self.port} - {str(e)}")
                return

            auth_data = json.dumps({
                'username': self.username,
                'password': self.password
            })

            try:
                sock.send(auth_data.encode())
            except socket.error as e:
                self.connection_error.emit(f"Не удалось отправить данные авторизации - {str(e)}")
                sock.close()
                return

            try:
                response = sock.recv(1024).decode()
                auth_response = json.loads(response)

                if auth_response.get('status') != 'success':
                    self.auth_failed.emit(auth_response.get('error', 'Неверный пароль'))
                    sock.close()
                    return
            except:
                self.auth_failed.emit("Ошибка авторизации")
                sock.close()
                return

            sock.close()
            self.auth_success.emit()

        except Exception as e:
            self.connection_error.emit(f"Ошибка подключения: {str(e)}")


class ClientThread(QThread):
    message_received = pyqtSignal(str, str, str)
    notification_received = pyqtSignal(str)
    screen_requested = pyqtSignal()
    history_received = pyqtSignal(list)
    connection_error = pyqtSignal(str)

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
        self.socket = None
        self.running = True
        self.crypto = UserCrypto(server_ip, port)

    def run(self):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(10.0)

            try:
                self.socket.connect((self.server_ip, self.port))
            except socket.error as e:
                self.connection_error.emit(f"Не удалось подключиться к {self.server_ip}:{self.port} - {str(e)}")
                return

            auth_data = json.dumps({
                'username': self.username,
                'password': self.password
            })

            try:
                self.socket.send(auth_data.encode())
            except socket.error as e:
                self.connection_error.emit(f"Не удалось отправить данные авторизации - {str(e)}")
                return

            try:
                response = self.socket.recv(1024).decode()
                auth_response = json.loads(response)

                if auth_response.get('status') != 'success':
                    self.connection_error.emit(auth_response.get('error', 'Неверный пароль'))
                    return
            except:
                self.connection_error.emit("Ошибка авторизации")
                return

            while self.running:
                try:
                    data = self.socket.recv(4096)
                    if not data:
                        break

                    packet = json.loads(data.decode())
                    packet_type = packet.get('type')

                    if packet_type == 'message':
                        from_user = packet.get('from', 'Неизвестный')
                        message = packet.get('message', '')
                        to_user = packet.get('to', 'all')

                        if from_user == 'Director':
                            decrypted = self.crypto.decrypt_message(message)
                            self.message_received.emit(from_user, decrypted, to_user)
                        else:
                            self.message_received.emit(from_user, message, to_user)

                    elif packet_type == 'notification':
                        message = packet.get('message', '')
                        self.notification_received.emit(message)

                    elif packet_type == 'request_screen':
                        self.screen_requested.emit()

                    elif packet_type == 'history':
                        messages = packet.get('messages', [])
                        self.history_received.emit(messages)

                except json.JSONDecodeError as e:
                    self.connection_error.emit(f"Ошибка декодирования JSON: {str(e)}")
                except socket.timeout:
                    continue
                except socket.error as e:
                    self.connection_error.emit(f"Ошибка сокета: {str(e)}")
                    break
                except Exception as e:
                    self.connection_error.emit(f"Ошибка: {str(e)}")
                    break

        except Exception as e:
            self.connection_error.emit(f"Ошибка подключения: {str(e)}")
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
                    'message': message
                }
                self.socket.send(json.dumps(packet).encode())
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
                    'data': screen_data
                }
                self.socket.send(json.dumps(packet).encode())
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

        self.auth_thread = AuthThread(self.server_ip, self.username, self.password)
        self.auth_thread.auth_success.connect(self.on_auth_success)
        self.auth_thread.auth_failed.connect(self.on_auth_failed)
        self.auth_thread.connection_error.connect(self.on_connection_error)
        self.auth_thread.start()

    def on_auth_success(self):
        self.accept()

    def on_auth_failed(self, error):
        self.connect_btn.setEnabled(True)
        self.connect_btn.setText("Подключиться")
        QMessageBox.critical(self, "Ошибка авторизации",
                             f"{error}\nУбедитесь, что вы ввели правильный пароль сервера.")
        sys.exit(1)

    def on_connection_error(self, error):
        self.connect_btn.setEnabled(True)
        self.connect_btn.setText("Подключиться")
        QMessageBox.critical(self, "Ошибка подключения",
                             f"Не удалось подключиться:\nПроверьте:\n1. Запущен ли сервер\n2. Правильный IP-адрес\n3. Отключен ли брандмауэр")


class MainWindow(QMainWindow):
    def __init__(self, server_ip, username, password):
        super().__init__()
        self.server_ip = server_ip
        self.username = username
        self.password = password
        self.client_thread = None
        self.screen_timer = None
        self.init_ui()
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowCloseButtonHint)
        self.connect_to_server()

    def init_ui(self):
        self.setWindowTitle(f"Asterion - {self.username}")
        self.setGeometry(100, 100, 1200, 700)
        self.setStyleSheet("""
            QMainWindow {
                background-color: #2d2d3a;
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

    def connect_to_server(self):
        self.client_thread = ClientThread(self.server_ip, self.username, self.password)
        self.client_thread.message_received.connect(self.on_message_received)
        self.client_thread.notification_received.connect(self.on_notification_received)
        self.client_thread.screen_requested.connect(self.on_screen_requested)
        self.client_thread.history_received.connect(self.on_history_received)
        self.client_thread.connection_error.connect(self.on_connection_error)
        self.client_thread.start()

    def on_connection_error(self, error):
        self.close()
        QMessageBox.critical(None, "Ошибка подключения",
                             f"Соединение потеряно:\nПроверьте статус сервера.")
        QApplication.quit()

    def on_history_received(self, messages):
        for msg in messages:
            from_user = msg.get('from', 'Неизвестный')
            message = msg.get('message', '')
            timestamp = msg.get('timestamp', '')

            if from_user == 'Director':
                self.private_chat.chat_display.append(f"[{timestamp}] {from_user}: {message}")
            else:
                self.general_chat.chat_display.append(f"[{timestamp}] {from_user}: {message}")

    def on_message_received(self, from_user, message, to_user):
        if to_user == "all":
            self.general_chat.chat_display.append(f"[{datetime.now().strftime('%H:%M:%S')}] {from_user}: {message}")
        else:
            self.private_chat.chat_display.append(f"[{datetime.now().strftime('%H:%M:%S')}] {from_user}: {message}")

    def on_notification_received(self, message):
        QMessageBox.information(self, "Уведомление от Директора", message)

    def on_screen_requested(self):
        self.start_screen_stream()

    def start_screen_stream(self):
        if self.screen_timer is None:
            self.screen_timer = QTimer()
            self.screen_timer.timeout.connect(self.capture_and_send_screen)
            self.screen_timer.start(50)

    def capture_and_send_screen(self):
        try:
            screen = QGuiApplication.primaryScreen()
            if screen is None:
                return

            screenshot = screen.grabWindow(0)
            if screenshot is None:
                return

            screenshot = screenshot.scaled(640, 480, Qt.AspectRatioMode.KeepAspectRatio,
                                           Qt.TransformationMode.SmoothTransformation)

            from io import BytesIO
            import base64

            byte_array = BytesIO()
            screenshot.save(byte_array, "JPEG", 30)
            img_str = base64.b64encode(byte_array.getvalue()).decode()

            if len(img_str) < 100000:
                self.client_thread.send_screen('Director', img_str)
        except:
            pass

    def send_message(self, input_widget):
        message = input_widget.text().strip()
        if not message:
            return

        current_tab = self.chat_tabs.currentWidget()
        tab_text = self.chat_tabs.tabText(self.chat_tabs.currentIndex())

        if tab_text == "Общий чат":
            if self.client_thread.send_message('all', message):
                self.general_chat.chat_display.append(f"[{datetime.now().strftime('%H:%M:%S')}] Я: {message}")
                input_widget.clear()
        else:
            if self.client_thread.send_message('Director', message):
                self.private_chat.chat_display.append(f"[{datetime.now().strftime('%H:%M:%S')}] Я: {message}")
                input_widget.clear()

    def closeEvent(self, event):
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
        main_window = MainWindow(login_dialog.server_ip, login_dialog.username, login_dialog.password)
        main_window.show()
        sys.exit(app.exec())
    else:
        sys.exit(0)


main()