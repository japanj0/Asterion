import sys
import json
import threading
import socket
import ssl
import time
import base64
import os
from datetime import datetime
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
import mss
import numpy as np
import cv2
from crypto import TransportCipher


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
            except json.JSONDecodeError as e:
                print(f"Повреждённый пакет отброшен: {e}")
        return packets


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
                    'password': self.password
                })
            except socket.error as e:
                self.connection_error.emit(f"Не удалось отправить данные авторизации - {str(e)}")
                ssl_sock.close()
                return

            try:
                reader = PacketReader()
                auth_response = None
                while auth_response is None:
                    chunk = ssl_sock.recv(4096)
                    if not chunk:
                        break
                    reader.feed(chunk)
                    pkts = reader.pop_packets()
                    if pkts:
                        auth_response = pkts[0]

                if auth_response is None or auth_response.get('status') != 'success':
                    error = auth_response.get('error', 'Неверный пароль') if auth_response else 'Ошибка авторизации'
                    self.auth_failed.emit(error)
                    ssl_sock.close()
                    return
            except:
                self.auth_failed.emit("Ошибка авторизации")
                ssl_sock.close()
                return

            ssl_sock.close()
            self.auth_success.emit()

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
        self.download_buffers = {}
        self.reader = PacketReader()
        self.transport = TransportCipher(password)

    def run(self):
        try:
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE

            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10.0)
            self.socket = context.wrap_socket(sock, server_hostname=self.server_ip)

            try:
                self.socket.connect((self.server_ip, self.port))
            except socket.error as e:
                self.connection_error.emit(f"Не удалось подключиться к {self.server_ip}:{self.port} - {str(e)}")
                return

            try:
                send_packet(self.socket, {
                    'username': self.username,
                    'password': self.password
                })
            except socket.error as e:
                self.connection_error.emit(f"Не удалось отправить данные авторизации - {str(e)}")
                return

            try:
                auth_reader = PacketReader()
                auth_response = None
                while auth_response is None:
                    chunk = self.socket.recv(4096)
                    if not chunk:
                        break
                    auth_reader.feed(chunk)
                    pkts = auth_reader.pop_packets()
                    if pkts:
                        auth_response = pkts[0]

                if auth_response is None or auth_response.get('status') != 'success':
                    error = auth_response.get('error', 'Неверный пароль') if auth_response else 'Ошибка авторизации'
                    self.connection_error.emit(error)
                    return
            except:
                self.connection_error.emit("Ошибка авторизации")
                return

            while self.running:
                try:
                    data = self.socket.recv(4096)
                    if not data:
                        break

                    self.reader.feed(data)

                    for packet in self.reader.pop_packets():
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
        self.screen_active = False
        self.sct = mss.MSS()
        self.download_buffers = {}
        self.is_processing_download = False
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
        self.download_progress.close()

    def on_file_download_chunk(self, file_id, chunk_index, total_chunks, chunk_data):
        for save_path, info in self.download_buffers.items():
            if info['file_id'] is None:
                info['file_id'] = file_id
                info['total_chunks'] = total_chunks
            if info['file_id'] == file_id:
                info['chunks'][chunk_index] = chunk_data
                progress = int((len(info['chunks']) / total_chunks) * 100)
                self.download_progress.setValue(progress)
                if len(info['chunks']) == total_chunks:
                    self.download_progress.setValue(100)
                    try:
                        with open(save_path, "wb") as f:
                            for i in range(total_chunks):
                                f.write(info['chunks'][i])
                        QMessageBox.information(self, "Успех", f"Файл {info['filename']} сохранён")
                    except Exception as e:
                        QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить файл: {str(e)}")
                    self.download_progress.close()
                    del self.download_buffers[save_path]

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

    def connect_to_server(self):
        self.client_thread = ClientThread(self.server_ip, self.username, self.password)
        self.client_thread.message_received.connect(self.on_message_received)
        self.client_thread.notification_received.connect(self.on_notification_received)
        self.client_thread.screen_requested.connect(self.on_screen_requested)
        self.client_thread.stop_screen_requested.connect(self.on_stop_screen_requested)
        self.client_thread.history_received.connect(self.on_history_received)
        self.client_thread.file_notify_received.connect(self.on_file_notify_received)
        self.client_thread.file_download_chunk_received.connect(self.on_file_download_chunk)
        self.client_thread.connection_error.connect(self.on_connection_error)
        self.client_thread.start()

    def on_file_notify_received(self, from_user, filename, chat_type, filesize, timestamp):
        link = f'<a href="download://?filename={filename}&from={from_user}&chat_type={chat_type}&to={self.username}">Скачать</a>&#8203;'
        msg = f"[{timestamp}] {from_user}: [Файл] {filename} ({filesize} байт) {link}"
        if chat_type == "general":
            self.append_chat_line(self.general_chat.chat_display, msg)
        else:
            self.append_chat_line(self.private_chat.chat_display, msg)

    def on_connection_error(self, error):
        self.close()
        QMessageBox.critical(None, "Ошибка подключения",
                             f"Соединение потеряно:\nПроверьте статус сервера.")
        QApplication.quit()

    def on_history_received(self, messages):
        for msg in messages:
            if msg.get('type') == 'message':
                from_user = msg.get('from', 'Неизвестный')
                to_user = msg.get('to', 'general')
                message = msg.get('message', '')
                timestamp = msg.get('timestamp', '')
                chat_type = msg.get('chat_type', 'general')
                if chat_type == 'general':
                    self.append_chat_line(self.general_chat.chat_display, f"[{timestamp}] {from_user}: {message}")
                else:
                    self.append_chat_line(self.private_chat.chat_display, f"[{timestamp}] {from_user}: {message}")
            elif msg.get('type') == 'file':
                from_user = msg.get('from', 'Неизвестный')
                filename = msg.get('filename', '')
                filesize = msg.get('filesize', 0)
                timestamp = msg.get('timestamp', '')
                chat_type = msg.get('chat_type', 'general')
                link = f'<a href="download://?filename={filename}&from={from_user}&chat_type={chat_type}&to={self.username}">Скачать</a>&#8203;'
                line = f"[{timestamp}] {from_user}: [Файл] {filename} ({filesize} байт) {link}"
                if chat_type == 'general':
                    self.append_chat_line(self.general_chat.chat_display, line)
                else:
                    self.append_chat_line(self.private_chat.chat_display, line)

    def on_message_received(self, from_user, message, to_user):
        if to_user == "general":
            self.append_chat_line(self.general_chat.chat_display, f"[{datetime.now().strftime('%H:%M:%S')}] {from_user}: {message}")
        else:
            self.append_chat_line(self.private_chat.chat_display, f"[{datetime.now().strftime('%H:%M:%S')}] {from_user}: {message}")

    def on_notification_received(self, message):
        QMessageBox.information(self, "Уведомление от Директора", message)

    def on_screen_requested(self):
        self.screen_active = True
        self.start_screen_stream()

    def on_stop_screen_requested(self):
        self.screen_active = False
        if self.screen_timer:
            self.screen_timer.stop()
            self.screen_timer = None
        print("Трансляция остановлена директором")

    def start_screen_stream(self):
        if self.screen_timer is None:
            self.screen_timer = QTimer()
            self.screen_timer.timeout.connect(self.capture_and_send_screen)
            self.screen_timer.start(33)
            print("Трансляция экрана запущена")

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
                print("Ошибка сжатия JPEG")
                return
            img_str = base64.b64encode(jpeg.tobytes()).decode()
            if len(img_str) < 300000:
                self.client_thread.send_screen('Director', img_str)
            else:
                print("Скриншот слишком большой:", len(img_str))
        except Exception as e:
            print("Ошибка захвата экрана:", e)

    def send_message(self, input_widget):
        message = input_widget.text().strip()
        if not message:
            return

        current_tab = self.chat_tabs.currentWidget()
        tab_text = self.chat_tabs.tabText(self.chat_tabs.currentIndex())

        if tab_text == "Общий чат":
            if self.client_thread.send_message('general', message):
                self.append_chat_line(self.general_chat.chat_display, f"[{datetime.now().strftime('%H:%M:%S')}] Я: {message}")
                input_widget.clear()
        else:
            if self.client_thread.send_message('Director', message):
                self.append_chat_line(self.private_chat.chat_display, f"[{datetime.now().strftime('%H:%M:%S')}] Я: {message}")
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
