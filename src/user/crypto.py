from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import os
from pathlib import Path


_TRANSPORT_SALT = b"asterion-transport-salt-v1"


def derive_transport_key(password: str) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=_TRANSPORT_SALT,
        iterations=390_000,
    )
    return base64.urlsafe_b64encode(kdf.derive(password.encode("utf-8")))


class TransportCipher:
    def __init__(self, password: str):
        self.key = derive_transport_key(password)
        self.cipher = Fernet(self.key)

    def encrypt_text(self, text: str) -> str:
        return self.cipher.encrypt(text.encode("utf-8")).decode("utf-8")

    def decrypt_text(self, token: str) -> str:
        try:
            return self.cipher.decrypt(token.encode("utf-8")).decode("utf-8")
        except (InvalidToken, Exception):
            return "[Decryption error]"

    def encrypt_bytes(self, data: bytes) -> str:
        return self.cipher.encrypt(data).decode("utf-8")

    def decrypt_bytes(self, token: str) -> bytes:
        return self.cipher.decrypt(token.encode("utf-8"))


class CryptoManager:
    def __init__(self):
        self.key_dir = Path("admin")
        self.key_dir.mkdir(exist_ok=True)
        self.key_file = self.key_dir / "secret.key"
        self.key = self._load_or_create_key()
        self.cipher = Fernet(self.key)
        self.clients = {}

    def _load_or_create_key(self):
        if self.key_file.exists():
            with open(self.key_file, 'rb') as f:
                return f.read()
        else:
            key = Fernet.generate_key()
            with open(self.key_file, 'wb') as f:
                f.write(key)
            return key

    def encrypt_message(self, message):
        return self.cipher.encrypt(message.encode()).decode()

    def decrypt_message(self, encrypted_message):
        try:
            return self.cipher.decrypt(encrypted_message.encode()).decode()
        except:
            return "[Decryption error]"

    def get_client_key(self, username):
        if username not in self.clients:
            client_key = Fernet.generate_key()
            self.clients[username] = client_key
        return self.clients[username]

    def decrypt_client_message(self, username, encrypted_message):
        if username in self.clients:
            cipher = Fernet(self.clients[username])
            try:
                return cipher.decrypt(encrypted_message.encode()).decode()
            except:
                return "[Decryption error]"
        return "[Key not found]"

    def encrypt_file_bytes(self, data):
        return self.cipher.encrypt(data)

    def decrypt_file_bytes(self, token):
        return self.cipher.decrypt(token)