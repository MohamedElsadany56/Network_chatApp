import socket
import threading
from datetime import datetime
from encryption import MessageEncryption
from db_manager import DBManager

class ChatServer:
    def __init__(self, host='0.0.0.0', port=5555):
        self.host = host
        self.port = port
        self.server_socket = None
        self.clients = {}  # username: socket
        self.clients_lock = threading.Lock()
        self.encryption = MessageEncryption()
        self.running = False
        
        # Initialize database manager
        self.db_manager = DBManager()
    
    # Database methods now delegated to DBManager
    def register_user(self, username, password):
        return self.db_manager.register_user(username, password)
    
    def authenticate_user(self, username, password):
        return self.db_manager.authenticate_user(username, password)
    
    def save_message(self, sender, receiver, message, timestamp):
        self.db_manager.save_message(sender, receiver, message, timestamp)
    
    def get_previous_messages(self, username):
        return self.db_manager.get_previous_messages(username)
    
    def broadcast_user_list(self):
        # Send updated user list to all clients
        with self.clients_lock:
            user_list = ','.join(self.clients.keys())
            message = f"USER_LIST|{user_list}"
            encrypted_msg = self.encryption.encrypt(message)
            
        """Send list of connected users to all clients"""
        with self.clients_lock:
            users = ",".join(self.clients.keys())
            message = f"USER_LIST|{users}"
            encrypted_message = self.encryption.encrypt(message)
            
            for client_socket in self.clients.values():
                try:
                    client_socket.send(encrypted_message.encode() + b'\n')
                except:
                    pass
    
    def broadcast_message(self, message, sender_username=None):
        """Broadcast message to all connected clients"""
        encrypted_message = self.encryption.encrypt(message)
        
        with self.clients_lock:
            for username, client_socket in self.clients.items():
                try:
                    client_socket.send(encrypted_message.encode() + b'\n')
                except Exception as e:
                    print(f"Error sending to {username}: {e}")
    
    def send_private_message(self, message, receiver_username):
        """Send message to specific client"""
        with self.clients_lock:
            if receiver_username in self.clients:
                try:
                    client_socket = self.clients[receiver_username]
                    encrypted_message = self.encryption.encrypt(message)
                    client_socket.send(encrypted_message.encode() + b'\n')
                    return True
                except Exception as e:
                    print(f"Error sending to {receiver_username}: {e}")
                    return False
            return False
    
    def handle_client(self, client_socket, address):
        # Handle individual client connection
        username = None
        authenticated = False
        
        try:
            # Set timeout for authentication
            client_socket.settimeout(10.0)
            
            # Authentication loop
            while not authenticated:
                # Receive authentication request
                try:
                    encrypted_auth = client_socket.recv(4096).decode()
                except socket.timeout:
                    # Test connection that doesn't send data - just close silently
                    client_socket.close()
                    return
                
                if not encrypted_auth:
                    client_socket.close()
                    return
                
                # Try to decrypt (might fail for test connections)
                try:
                    auth_data = self.encryption.decrypt(encrypted_auth)
                except:
                    # Invalid data (probably a test connection) - close silently
                    client_socket.close()
                    return
                
                if not auth_data:
                    client_socket.close()
                    return
                
                # Parse authentication request: AUTH|TYPE|USERNAME|PASSWORD
                parts = auth_data.split('|')
                if len(parts) < 3 or parts[0] != "AUTH":
                    client_socket.close()
                    return
                
                auth_type = parts[1]  # LOGIN or REGISTER
                
                # Process authentication
                if auth_type == "REGISTER":
                    if len(parts) < 4:
                        client_socket.close()
                        return
                    username = parts[2]
                    password = parts[3]
                    
                    success, message = self.register_user(username, password)
                    response = f"AUTH_RESPONSE|{'SUCCESS' if success else 'FAIL'}|{message}"
                    encrypted_response = self.encryption.encrypt(response)
                    client_socket.send(encrypted_response.encode())
                    
                    if success:
                        authenticated = True
                        print(f"[SERVER] User {username} registered from {address}")
                    
                elif auth_type == "LOGIN":
                    username = parts[2]
                    password = parts[3]
                    
                    # Check if user is already connected
                    is_already_connected = False
                    with self.clients_lock:
                        if username in self.clients:
                            is_already_connected = True
                            
                    if is_already_connected:
                        # Optional: You could reject the login here.
                        # For "force one session", we will kick the old user.
                        print(f"[SERVER] Kicking old session for {username}")
                        with self.clients_lock:
                            try:
                                old_socket = self.clients[username]
                                old_socket.close()
                                del self.clients[username]
                            except:
                                pass
                    
                    success, message = self.authenticate_user(username, password)
                    response = f"AUTH_RESPONSE|{'SUCCESS' if success else 'FAIL'}|{message}"
                    encrypted_response = self.encryption.encrypt(response)
                    client_socket.send(encrypted_response.encode())
                    
                    if success:
                        authenticated = True
                        print(f"[SERVER] User {username} logged in from {address}")
                
                else:
                    client_socket.close()
                    return
            
            if not username or not authenticated:
                client_socket.close()
                return
            
            # Reset timeout for persistent connection
            client_socket.settimeout(None)
            
            # Add client to dictionary
            with self.clients_lock:
                self.clients[username] = client_socket
            
            print(f"[SERVER] {username} connected from {address}")
            
            # Send previous messages to user
            previous_messages = self.get_previous_messages(username)
            for sender, receiver, message, timestamp in previous_messages:
                msg = f"MSG|{timestamp}|{sender}|{receiver}|{message}"
                encrypted_msg = self.encryption.encrypt(msg)
                client_socket.send(encrypted_msg.encode() + b'\n')
            
            # Notify all clients about new user
            timestamp = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
            join_message = f"SYSTEM|{timestamp}|SERVER|ALL|{username} joined the chat"
            self.broadcast_message(join_message, username)
            
            # Send user list to all clients
            self.broadcast_user_list()
            
            # Main message loop with buffering
            buffer = ""
            while self.running:
                try:
                    data_chunk = client_socket.recv(4096).decode()
                    if not data_chunk:
                        break
                    
                    buffer += data_chunk
                    
                    while '\n' in buffer:
                        encrypted_data, buffer = buffer.split('\n', 1)
                        if not encrypted_data:
                            continue
                            
                        # Process individual message
                        try:
                            data = self.encryption.decrypt(encrypted_data)
                            if not data:
                                continue
                            
                            # Parse message
                            parts = data.split('|', 4)
                            if len(parts) < 5:
                                continue
                            
                            msg_type, timestamp, sender, receiver, content = parts
                            
                            # Handle typing indicator
                            if msg_type == "TYPING":
                                typing_msg = f"TYPING|{sender}|{content}"
                                self.broadcast_message(typing_msg, sender)
                                continue
                            
                            # Handle regular message
                            if msg_type == "MSG":
                                # Save to database
                                self.save_message(sender, receiver, content, timestamp)
                                
                                # Route message
                                if receiver == "ALL":
                                    # Group message
                                    message = f"MSG|{timestamp}|{sender}|{receiver}|{content}"
                                    self.broadcast_message(message, sender)
                                else:
                                    # Private message
                                    message = f"MSG|{timestamp}|{sender}|{receiver}|{content}"
                                    success = self.send_private_message(message, receiver)
                                    
                                    # Send confirmation to sender
                                    if success:
                                        encrypted_msg = self.encryption.encrypt(message)
                                        client_socket.send(encrypted_msg.encode() + b'\n')
                        except Exception as e:
                            print(f"[SERVER] Error processing message: {e}")
                            
                except Exception as e:
                    print(f"[SERVER] Error handling message from {username}: {e}")
                    break
        
        except Exception as e:
            print(f"[SERVER] Error with client {address}: {e}")
        
        finally:
            # Remove client and notify others
            if username:
                with self.clients_lock:
                    if username in self.clients:
                        del self.clients[username]
                
                print(f"[SERVER] {username} disconnected")
                
                # Notify all clients
                timestamp = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
                leave_message = f"SYSTEM|{timestamp}|SERVER|ALL|{username} left the chat"
                self.broadcast_message(leave_message, username)
                
                # Update user list
                self.broadcast_user_list()
            
            client_socket.close()
    
    
    def monitor_terminal_input(self):
        # Monitor terminal for stop commands
        print("\n[SERVER] Type 'stop' or 'quit' to shutdown the server gracefully")
        print("[SERVER] Or press Ctrl+C to force stop\n")
        
        while self.running:
            try:
                user_input = input().strip().lower()
                if user_input in ['stop', 'quit', 'exit', 'q']:
                    print("\n[SERVER] Shutting down gracefully...")
                    self.stop()
                    break
            except (EOFError, KeyboardInterrupt):
                break
    
    def start(self):
        # Start the server
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(100)
            self.running = True
            
            print(f"[SERVER] ChatX Server started on {self.host}:{self.port}")
            print(f"[SERVER] Waiting for connections...")
            
            # Start terminal input monitoring thread
            input_thread = threading.Thread(target=self.monitor_terminal_input, daemon=True)
            input_thread.start()
            
            # Accept connections
            while self.running:
                try:
                    self.server_socket.settimeout(1.0)  # Timeout to check running flag
                    try:
                        client_socket, address = self.server_socket.accept()
                        client_thread = threading.Thread(
                            target=self.handle_client,
                            args=(client_socket, address),
                            daemon=True
                        )
                        client_thread.start()
                    except socket.timeout:
                        continue  # Check if still running
                except Exception as e:
                    if self.running:
                        print(f"[SERVER] Accept error: {e}")
                    break
        
        except Exception as e:
            print(f"[SERVER] Server error: {e}")
        
        finally:
            self.stop()
    
    def stop(self):
        # Stop the server
        if not self.running:
            return
            
        self.running = False
        
        # Notify all connected clients
        with self.clients_lock:
            print(f"\n[SERVER] Disconnecting {len(self.clients)} client(s)...")
            for username, client_socket in list(self.clients.items()):
                try:
                    client_socket.close()
                except:
                    pass
            self.clients.clear()
        
        # Close server socket
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
        
        print("[SERVER] Server stopped successfully")
        print("[SERVER] Goodbye!")

if __name__ == "__main__":
    # Get server configuration
    print("="*50)
    print("ChatX Server Configuration")
    print("="*50)
    
    # Default to 0.0.0.0 to listen on all interfaces
    try:
        host = input("Enter server host (press Enter for 0.0.0.0): ").strip()
        if not host:
            host = '0.0.0.0'
    except (EOFError, OSError):
        host = '0.0.0.0'
        print("Using default host: 0.0.0.0")
    
    try:
        port_str = input("Enter server port (press Enter for 5555): ").strip()
        if not port_str:
            port = 5555
        else:
            port = int(port_str)
    except (EOFError, OSError, ValueError):
        port = 5555
        print("Using default port: 5555")
    
    print("="*50)
    
    # Start server
    server = ChatServer(host, port)
    try:
        server.start()
    except KeyboardInterrupt:
        print("\n[SERVER] Keyboard interrupt received...")
        server.stop()
