from cryptography.fernet import Fernet
import base64
import hashlib

class MessageEncryption:
    def __init__(self, key=None):
        if key is None:
            # Default key for project simplicity
            # In production, use unique keys per session
            password = "network_chat_2024"
            key = hashlib.sha256(password.encode()).digest()
            self.key = base64.urlsafe_b64encode(key)
        else:
            self.key = key
        
        self.cipher = Fernet(self.key)
    
    def encrypt(self, message):
        # Encrypt message and return as string
        try:
            encrypted = self.cipher.encrypt(message.encode())
            return encrypted.decode()
        except Exception as e:
            print(f"Encryption error: {e}")
            return None
    
    def decrypt(self, encrypted_message):
        # Decrypt message and return as string
        try:
            decrypted = self.cipher.decrypt(encrypted_message.encode())
            return decrypted.decode()
        except Exception as e:
            # Silently fail for invalid/test connections
            return None
    
    def get_key(self):
        return self.key
