import socket
from encryption import MessageEncryption

class AuthService:
    def __init__(self):
        self.encryption = MessageEncryption()

    def connect_server(self, ip, port):
        """Establish connection to the server"""
        try:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.settimeout(10)  # 10s timeout for connection
            client_socket.connect((ip, port))
            client_socket.settimeout(None)  # Reset timeout
            return client_socket
        except Exception as e:
            raise Exception(f"Connection failed: {e}")

    def authenticate(self, client_socket, username, password, action):
        """Handle the authentication handshake"""
        try:
            # Send authentication request
            auth_request = f"AUTH|{action}|{username}|{password}"
            encrypted_auth = self.encryption.encrypt(auth_request)
            client_socket.send(encrypted_auth.encode())
            
            # Receive authentication response
            client_socket.settimeout(10) # Wait at most 10s for auth response
            encrypted_response = client_socket.recv(4096).decode()
            client_socket.settimeout(None)
            
            if not encrypted_response:
                raise Exception("Server closed connection")
                
            response = self.encryption.decrypt(encrypted_response)
            
            if not response:
                raise Exception("Failed to decrypt server response")
            
            # Parse response
            parts = response.split('|', 2)
            if len(parts) < 3 or parts[0] != "AUTH_RESPONSE":
                raise Exception("Invalid server response format")
            
            status = parts[1]
            message = parts[2]
            
            if status == "SUCCESS":
                return True, message
            else:
                return False, message
                
        except socket.timeout:
            return False, "Authentication timed out"
        except Exception as e:
            return False, str(e)

    def login(self, ip, port, username, password):
        """Complete login flow: Connect -> Auth"""
        try:
            sock = self.connect_server(ip, port)
            success, message = self.authenticate(sock, username, password, "LOGIN")
            
            if success:
                return True, sock, message
            else:
                sock.close()
                return False, None, message
        except Exception as e:
            return False, None, str(e)
            
    def register(self, ip, port, username, password):
        """Complete registration flow: Connect -> Auth"""
        try:
            sock = self.connect_server(ip, port)
            success, message = self.authenticate(sock, username, password, "REGISTER")
            
            if success:
                return True, sock, message
            else:
                sock.close()
                return False, None, message
        except Exception as e:
            return False, None, str(e)
