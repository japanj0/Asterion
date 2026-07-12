from cryptography.fernet import Fernet
import os
from pathlib import Path


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