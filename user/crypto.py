import json
import socket


class UserCrypto:
    def __init__(self, server_ip, server_port=5555):
        self.server_ip = server_ip
        self.server_port = server_port

    def decrypt_message(self, encrypted_message):
        try:
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.settimeout(5.0)
            client.connect((self.server_ip, self.server_port))

            request = json.dumps({
                'type': 'decrypt_request',
                'msg_id': 'temp',
                'message': encrypted_message
            })
            client.send(request.encode())

            response = client.recv(4096).decode()
            data = json.loads(response)

            if data.get('type') == 'decrypt_response':
                return data.get('message', encrypted_message)
            return encrypted_message
        except Exception as e:
            return f"[Decryption error: {str(e)}]"
        finally:
            try:
                client.close()
            except:
                pass

    def encrypt_message(self, message):
        return message