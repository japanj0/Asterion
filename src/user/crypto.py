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


_KEY_WRAP_ITERATIONS = 390_000


class CryptoManager:
    def __init__(self, password):
        self.key_dir = Path("admin")
        self.key_dir.mkdir(exist_ok=True)
        self.key_file = self.key_dir / "secret.key"
        self.key = self._load_or_create_key(password)
        self.cipher = Fernet(self.key)
        self.clients = {}

    def _derive_wrapping_key(self, password, salt):
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=_KEY_WRAP_ITERATIONS,
        )
        return base64.urlsafe_b64encode(kdf.derive(password.encode("utf-8")))

    def _load_or_create_key(self, password):
        if self.key_file.exists():
            with open(self.key_file, 'rb') as f:
                raw = f.read()
            salt, encrypted_key = raw[:16], raw[16:]
            wrapping_key = self._derive_wrapping_key(password, salt)
            wrapper = Fernet(wrapping_key)
            try:
                return wrapper.decrypt(encrypted_key)
            except InvalidToken:
                raise ValueError("Неверный пароль сервера: не удалось расшифровать secret.key")
        else:
            salt = os.urandom(16)
            data_key = Fernet.generate_key()
            wrapping_key = self._derive_wrapping_key(password, salt)
            wrapper = Fernet(wrapping_key)
            encrypted_key = wrapper.encrypt(data_key)
            with open(self.key_file, 'wb') as f:
                f.write(salt + encrypted_key)
            return data_key

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

    def read_encrypted_file(self, filepath):
        chunks = []
        with open(filepath, "rb") as f:
            while True:
                length_prefix = f.read(4)
                if not length_prefix:
                    break
                chunk_len = int.from_bytes(length_prefix, "big")
                encrypted_chunk = f.read(chunk_len)
                chunks.append(self.cipher.decrypt(encrypted_chunk))
        return b"".join(chunks)

    def write_encrypted_file(self, filepath, data, chunk_size=1024 * 1024):
        with open(filepath, "wb") as f:
            for i in range(0, len(data), chunk_size):
                encrypted_chunk = self.cipher.encrypt(data[i:i + chunk_size])
                f.write(len(encrypted_chunk).to_bytes(4, "big") + encrypted_chunk)