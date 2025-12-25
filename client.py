import socket
import threading
import tkinter as tk
from tkinter import scrolledtext, messagebox, simpledialog
from datetime import datetime
from encryption import MessageEncryption
import netifaces
import ipaddress
import hashlib
from login_dialog import LoginDialog, RegisterDialog

class ChatClient:
    def __init__(self):
        self.client_socket = None
        self.encryption = MessageEncryption()
        self.username = None
        self.password = None
        self.authenticated = False
        self.connected = False
        self.receive_thread = None
        self.typing_timer = None
        self.is_typing = False
        self.server_ip = None
        self.server_port = 5555
        self.selected_user = None  # For private messaging
        self.current_chat = "ALL"
        self.chat_history = {"ALL": []}
        self.online_users = set()
        self.all_chat_users = set()
        
        # Create GUI
        self.create_gui()
        
        # Start automatic server detection in background
        self.auto_detect_thread = threading.Thread(target=self.background_server_detection, daemon=True)
        self.auto_detect_thread.start()
    
    def background_server_detection(self):
        # Automatically detect server in background
        while True:
            if not self.connected and not self.server_ip:
                server_ip = self.scan_lan_for_server(self.server_port)
                if server_ip:
                    self.server_ip = server_ip
                    self.window.after(0, lambda: self.status_label.config(
                        text=f"Server found at {server_ip}",
                        fg='#25D366'
                    ))
            threading.Event().wait(10)  # Check every 10 seconds
    
    def get_local_ip(self):
        # Get local IP address
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
            return local_ip
        except:
            return "127.0.0.1"
    
    def scan_lan_for_server(self, port=5555, timeout=0.5):
        # Scan local network for available server
        local_ip = self.get_local_ip()
        ip_parts = local_ip.split('.')
        network_prefix = '.'.join(ip_parts[:3])
        
        # Try localhost first
        if self.test_server_connection('127.0.0.1', port, timeout=1):
            return '127.0.0.1'
        
        # Try local IP
        if self.test_server_connection(local_ip, port, timeout=1):
            return local_ip
        
        # Scan common LAN IPs
        for i in [1, 2, 100, 101, 254]:
            test_ip = f"{network_prefix}.{i}"
            if test_ip != local_ip:
                if self.test_server_connection(test_ip, port, timeout):
                    return test_ip
        
        return None
    
    def test_server_connection(self, host, port, timeout=0.5):
        # Test if server is available at given address
        try:
            test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            test_socket.settimeout(timeout)
            test_socket.connect((host, port))
            test_socket.close()
            return True
        except:
            return False
    
    def create_gui(self):
        # Main window with WhatsApp style
        self.window = tk.Tk()
        self.window.title("ChatX")
        self.window.geometry("1000x650")
        self.window.configure(bg='#ECE5DD')
        
        # Top header bar (WhatsApp green)
        header_frame = tk.Frame(self.window, bg='#075E54', height=60)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)
        
        # ChatX logo/title
        tk.Label(
            header_frame,
            text="ChatX",
            bg='#075E54',
            fg='white',
            font=('Segoe UI', 20, 'bold')
        ).pack(side=tk.LEFT, padx=20, pady=10)
        
        # Connection controls
        control_frame = tk.Frame(header_frame, bg='#075E54')
        control_frame.pack(side=tk.RIGHT, padx=20)
        
        self.connect_button = tk.Button(
            control_frame,
            text="Connect",
            command=self.connect_to_server,
            bg='#25D366',
            fg='white',
            font=('Segoe UI', 10, 'bold'),
            width=10,
            relief=tk.FLAT,
            cursor='hand2'
        )
        self.connect_button.pack(side=tk.LEFT, padx=5)
        
        self.disconnect_button = tk.Button(
            control_frame,
            text="Disconnect",
            command=self.disconnect_from_server,
            bg='#DC3545',
            fg='white',
            font=('Segoe UI', 10, 'bold'),
            width=10,
            relief=tk.FLAT,
            cursor='hand2',
            state=tk.DISABLED
        )
        self.disconnect_button.pack(side=tk.LEFT, padx=5)
        
        # Status label
        self.status_label = tk.Label(
            header_frame,
            text="Searching for server...",
            bg='#075E54',
            fg='#FFD700',
            font=('Segoe UI', 10, 'italic')
        )
        self.status_label.pack(side=tk.RIGHT, padx=20)
        
        # Main content area
        content_frame = tk.Frame(self.window, bg='#ECE5DD')
        content_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Left sidebar - Online users (WhatsApp style)
        users_frame = tk.Frame(content_frame, bg='white', width=280, relief=tk.SOLID, borderwidth=1)
        users_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 5))
        users_frame.pack_propagate(False)
        
        # Users header
        users_header = tk.Frame(users_frame, bg='#EDEDED', height=50)
        users_header.pack(fill=tk.X)
        users_header.pack_propagate(False)
        
        tk.Label(
            users_header,
            text="Chats",
            bg='#EDEDED',
            fg='#075E54',
            font=('Segoe UI', 14, 'bold')
        ).pack(side=tk.LEFT, pady=15, padx=15)
        
        # New Chat Button
        tk.Button(
            users_header,
            text="+",
            command=self.open_new_chat_window,
            bg='#25D366',
            fg='white',
            font=('Segoe UI', 12, 'bold'),
            relief=tk.FLAT,
            width=3
        ).pack(side=tk.RIGHT, pady=10, padx=10)
        
        # Public chat option
        group_chat_frame = tk.Frame(users_frame, bg='white', height=60)
        group_chat_frame.pack(fill=tk.X)
        
        def on_public_click(e):
            self.select_group_chat()
            
        group_chat_frame.bind('<Button-1>', on_public_click)
        
        lbl = tk.Label(
            group_chat_frame,
            text="👥 Public Chat",
            bg='white',
            fg='#075E54',
            font=('Segoe UI', 12, 'bold'),
            cursor='hand2'
        )
        lbl.pack(side=tk.LEFT, pady=15, padx=15)
        lbl.bind('<Button-1>', on_public_click)

        # Separator
        tk.Frame(users_frame, bg='#D3D3D3', height=1).pack(fill=tk.X)
        
        # Chats label (Recent)
        tk.Label(
            users_frame,
            text="Direct Messages",
            bg='#EDEDED',
            fg='#666',
            font=('Segoe UI', 10)
        ).pack(fill=tk.X, pady=5, padx=15)
        
        # Users list
        users_scroll_frame = tk.Frame(users_frame, bg='white')
        users_scroll_frame.pack(fill=tk.BOTH, expand=True)
        
        self.users_listbox = tk.Listbox(
            users_scroll_frame,
            bg='white',
            fg='#075E54',
            font=('Segoe UI', 11),
            selectbackground='#D3F8E2',
            selectforeground='#075E54',
            relief=tk.FLAT,
            highlightthickness=0
        )
        self.users_listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.users_listbox.bind('<<ListboxSelect>>', self.on_user_select)
        
        # Right area - Chat
        chat_container = tk.Frame(content_frame, bg='white', relief=tk.SOLID, borderwidth=1)
        chat_container.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Chat header
        chat_header = tk.Frame(chat_container, bg='#EDEDED', height=50)
        chat_header.pack(fill=tk.X)
        chat_header.pack_propagate(False)
        
        self.chat_header_label = tk.Label(
            chat_header,
            text="Public Chat",
            bg='#EDEDED',
            fg='#075E54',
            font=('Segoe UI', 14, 'bold')
        )
        self.chat_header_label.pack(side=tk.LEFT, pady=12, padx=15)
        
        # Chat display area (WhatsApp background pattern)
        self.chat_display = scrolledtext.ScrolledText(
            chat_container,
            state=tk.DISABLED,
            bg='#E5DDD5',
            font=('Segoe UI', 10),
            wrap=tk.WORD,
            relief=tk.FLAT
        )
        self.chat_display.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Configure chat text tags (WhatsApp colors)
        # Configure chat text tags (WhatsApp-like)
        self.chat_display.tag_config('system', foreground='#667781', font=('Segoe UI', 9, 'italic'), justify=tk.CENTER, spacing1=5, spacing3=5)
        self.chat_display.tag_config('sent', background='#DCF8C6', foreground='#000', font=('Segoe UI', 10), lmargin1=50, lmargin2=50, rmargin=10, spacing1=5, spacing3=5, justify=tk.RIGHT)
        self.chat_display.tag_config('received', background='white', foreground='#000', font=('Segoe UI', 10), lmargin1=10, lmargin2=10, rmargin=50, spacing1=5, spacing3=5, justify=tk.LEFT)
        self.chat_display.tag_config('private', background='#FFF4CC', foreground='#000', font=('Segoe UI', 10), lmargin1=10, lmargin2=10, rmargin=10, spacing1=5, spacing3=5)
        self.chat_display.tag_config('timestamp', foreground='#999999', font=('Segoe UI', 8))
        self.chat_display.tag_config('typing', foreground='#667781', font=('Segoe UI', 9, 'italic'), justify=tk.LEFT)
        
        # Clickable username tag
        self.chat_display.tag_config('clickable_user', foreground='blue', font=('Segoe UI', 10, 'bold'))
        self.chat_display.tag_bind('clickable_user', '<Button-1>', self.on_chat_username_click)
        self.chat_display.tag_bind('clickable_user', '<Enter>', lambda e: self.chat_display.config(cursor="hand2"))
        self.chat_display.tag_bind('clickable_user', '<Leave>', lambda e: self.chat_display.config(cursor=""))
        
        # Typing indicator
        self.typing_label = tk.Label(
            chat_container,
            text="",
            bg='white',
            fg='#667781',
            font=('Segoe UI', 9, 'italic')
        )
        self.typing_label.pack(pady=2)
        
        # Message input frame
        input_frame = tk.Frame(chat_container, bg='#F0F0F0', height=60)
        input_frame.pack(fill=tk.X, padx=10, pady=10)
        input_frame.pack_propagate(False)
        
        # Message entry
        self.message_entry = tk.Entry(
            input_frame,
            font=('Segoe UI', 11),
            bg='white',
            relief=tk.SOLID,
            borderwidth=1
        )
        self.message_entry.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5, 10), pady=10)
        self.message_entry.bind('<Return>', lambda e: self.send_message())
        self.message_entry.bind('<KeyPress>', self.on_key_press)
        self.message_entry.bind('<KeyRelease>', self.on_key_release)
        
        # Send button (WhatsApp style)
        self.send_button = tk.Button(
            input_frame,
            text="➤",
            command=self.send_message,
            bg='#25D366',
            fg='white',
            font=('Segoe UI', 16, 'bold'),
            width=4,
            relief=tk.FLAT,
            cursor='hand2',
            state=tk.DISABLED
        )
        self.send_button.pack(side=tk.RIGHT, padx=5, pady=10)
    
    def open_new_chat_window(self):
        # Open window to select a user from online users
        top = tk.Toplevel(self.window)
        top.title("New Chat")
        top.geometry("300x400")
        top.configure(bg='white')
        
        tk.Label(top, text="Select User", font=('Segoe UI', 12, 'bold'), bg='white').pack(pady=10)
        
        listbox = tk.Listbox(top, font=('Segoe UI', 11), relief=tk.FLAT, bg='#F0F0F0', selectbackground='#D3F8E2', selectforeground='#075E54')
        listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Populate with online users NOT in current chats
        available_users = sorted(list(self.online_users))
        for user in available_users:
            if user != self.username and user not in self.all_chat_users:
                listbox.insert(tk.END, user)
                
        def start_chat():
            selection = listbox.curselection()
            if selection:
                username = listbox.get(selection[0])
                self.all_chat_users.add(username)
                self.refresh_user_listbox()
                
                # Close and select
                top.destroy()
                
                # Trigger selection
                self.selected_user = username
                self.current_chat = username
                if username not in self.chat_history:
                    self.chat_history[username] = []
                self.chat_header_label.config(text=f"Private Chat with {username}")
                self.message_entry.focus()
                self.refresh_chat_display()
                
        tk.Button(top, text="Start Chat", command=start_chat, bg='#25D366', fg='white', relief=tk.FLAT).pack(pady=10)

    def select_group_chat(self):
        # Select public chat
        self.selected_user = None
        self.current_chat = "ALL"
        self.chat_header_label.config(text="Public Chat")
        self.users_listbox.selection_clear(0, tk.END)
        self.refresh_chat_display()
    
    def on_user_select(self, event):
        # Handle user selection for private chat
        selection = self.users_listbox.curselection()
        if selection:
            raw_text = self.users_listbox.get(selection[0])
            # Extract username from "🟢 User" or "⚪ User (Offline)"
            username = raw_text.split(' ', 1)[1]
            if username.endswith(" (Offline)"):
                username = username.rsplit(' ', 2)[0]
                
            username = username.strip()
            self.selected_user = username
            self.current_chat = username
            
            if username not in self.chat_history:
                self.chat_history[username] = []
                
            self.chat_header_label.config(text=f"Private Chat with {username}")
            self.message_entry.focus()
            self.refresh_chat_display()
    
    def connect_to_server(self):
        # Connect to chat server with authentication
        if self.connected:
            messagebox.showwarning("Already Connected", "You are already connected to the server")
            return
        
        if not self.server_ip:
            messagebox.showerror("No Server", "No server found. Please wait for automatic detection or check if server is running.")
            return
        
        try:
            current_mode = "LOGIN"
            
            while True:
                if current_mode == "LOGIN":
                    dialog = LoginDialog(self.window)
                    result, username, password, action, next_action = dialog.show()
                    
                    if next_action == "SWITCH_TO_REGISTER":
                        current_mode = "REGISTER"
                        continue
                        
                elif current_mode == "REGISTER":
                    dialog = RegisterDialog(self.window)
                    result, username, password, action, next_action = dialog.show()
                    
                    if next_action == "SWITCH_TO_LOGIN":
                        current_mode = "LOGIN"
                        continue

                # If we have a result (user clicked Login or Register successfully)
                if result and username and password:
                    break
                
                # If dialog was closed without action and no next_action
                if not next_action:
                    return

            # Proceed with authentication
            from auth_service import AuthService
            auth_service = AuthService()
            
            if action == "REGISTER":
                success, sock, message = auth_service.register(self.server_ip, self.server_port, username, password)
            else:
                success, sock, message = auth_service.login(self.server_ip, self.server_port, username, password)
                
            if success:
                self.client_socket = sock
                self.username = username
                self.password = password
                self.authenticated = True
                self.connected = True
                
                # Update window title
                self.window.title(f"ChatX - {self.username}")
                
                # Update UI
                self.status_label.config(text=f"Connected as {self.username}", fg='#25D366')
                self.connect_button.config(state=tk.DISABLED)
                self.disconnect_button.config(state=tk.NORMAL)
                self.send_button.config(state=tk.NORMAL)
                
                # Start receive thread
                self.receive_thread = threading.Thread(target=self.receive_messages, daemon=True)
                self.receive_thread.start()
                
                if action == "REGISTER":
                    self.display_message(f"✓ Account created! Welcome {self.username}!", 'system')
                else:
                    self.display_message(f"✓ Welcome back {self.username}!", 'system')
            else:
                self.connected = False
                if sock:
                    sock.close()
                messagebox.showerror("Authentication Failed", message, parent=self.window)
        
        except Exception as e:
            messagebox.showerror("Connection Error", f"Failed to connect: {e}", parent=self.window)
            self.connected = False
            if self.client_socket:
                self.client_socket.close()
                self.client_socket = None
    
    def disconnect_from_server(self):
        # Manually disconnect from server
        if not self.connected:
            return
        
        try:
            self.connected = False
            if self.client_socket:
                self.client_socket.close()
            
            # Update UI
            self.window.title("ChatX")
            self.status_label.config(text="Disconnected", fg='#DC3545')
            self.connect_button.config(state=tk.NORMAL)
            self.disconnect_button.config(state=tk.DISABLED)
            self.send_button.config(state=tk.DISABLED)
            
            self.display_message("✗ Disconnected from server", 'system')
            
        except Exception as e:
            print(f"Disconnect error: {e}")
    
    def receive_messages(self):
        # Receive messages from server
        buffer = ""
        while self.connected:
            try:
                data_chunk = self.client_socket.recv(4096).decode()
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
                        parts = data.split('|', 1)
                        
                        if parts[0] == "USER_LIST":
                            users = parts[1].split(',') if len(parts) > 1 and parts[1] else []
                            self.update_user_list(users)
                        
                        elif parts[0] == "TYPING":
                            if len(parts) > 1:
                                typing_parts = parts[1].split('|', 1)
                                if len(typing_parts) >= 2:
                                    username = typing_parts[0]
                                    status = typing_parts[1]
                                    if username != self.username:
                                        if status == "ON":
                                            self.typing_label.config(text=f"{username} is typing...")
                                        else:
                                            self.typing_label.config(text="")
                        
                        elif parts[0] == "SYSTEM":
                            if len(parts) > 1:
                                msg_parts = parts[1].split('|', 3)
                                if len(msg_parts) >= 4:
                                    timestamp, sender, receiver, content = msg_parts
                                    self.add_message_to_history("ALL", f"{content}", 'system')
                        
                        elif parts[0] == "MSG":
                            if len(parts) > 1:
                                msg_parts = parts[1].split('|', 3)
                                if len(msg_parts) >= 4:
                                    timestamp, sender, receiver, content = msg_parts
                                    if receiver == "ALL":
                                        # Group message
                                        if sender == self.username:
                                            self.add_message_to_history("ALL", content, 'sent', sender="You", timestamp=timestamp)
                                        else:
                                            self.add_message_to_history("ALL", content, 'received', sender=sender, timestamp=timestamp)
                                    else:
                                        # Private message logic
                                        chat_partner = receiver if sender == self.username else sender
                                        
                                        if sender == self.username:
                                            self.add_message_to_history(chat_partner, content, 'sent', sender="You", timestamp=timestamp)
                                        else:
                                            self.add_message_to_history(chat_partner, content, 'received', sender=sender, timestamp=timestamp)
                    except Exception as e:
                        print(f"Error processing message: {e}")
            
            except Exception as e:
                print(f"Receive error: {e}")
                break
        
        # Connection lost
        if self.connected:
            self.handle_disconnect()
    
    def send_message(self):
        # Send message to server
        if not self.connected:
            messagebox.showwarning("Not Connected", "Please connect to server first")
            return
        
        message = self.message_entry.get().strip()
        if not message:
            return
        
        try:
            timestamp = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
            
            # Check if private message mode
            if self.selected_user:
                # Send private message
                receiver = self.selected_user
                msg = f"MSG|{timestamp}|{self.username}|{receiver}|{message}"
            else:
                # Send group message
                msg = f"MSG|{timestamp}|{self.username}|ALL|{message}"
            
            encrypted_msg = self.encryption.encrypt(msg)
            self.client_socket.send(encrypted_msg.encode() + b'\n')
            
            # Clear input
            self.message_entry.delete(0, tk.END)
            
            # Stop typing indicator
            self.send_typing_status("OFF")
        
        except Exception as e:
            messagebox.showerror("Send Error", f"Failed to send message: {e}")
    
    def on_key_press(self, event):
        # Handle key press for typing indicator
        if not self.is_typing and event.char.isprintable():
            self.is_typing = True
            self.send_typing_status("ON")
    
    def on_key_release(self, event):
        # Reset typing timer on key release
        if self.typing_timer:
            self.typing_timer.cancel()
        
        self.typing_timer = threading.Timer(2.0, self.stop_typing)
        self.typing_timer.start()
    
    def stop_typing(self):
        # Stop typing indicator after timeout
        if self.is_typing:
            self.is_typing = False
            self.send_typing_status("OFF")
    
    def send_typing_status(self, status):
        # Send typing status to server
        if not self.connected:
            return
        
        try:
            timestamp = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
            msg = f"TYPING|{timestamp}|{self.username}|ALL|{status}"
            encrypted_msg = self.encryption.encrypt(msg)
            self.client_socket.send(encrypted_msg.encode() + b'\n')
        except:
            pass
    
    def update_user_list(self, users):
        # Update online users set
        self.online_users = set(users)
        self.refresh_user_listbox()
        
    def refresh_user_listbox(self):
        # Redraw user list (Only show Active Chats)
        self.users_listbox.delete(0, tk.END)
        
        # Only show users in all_chat_users (History/Active)
        display_users = self.all_chat_users
        
        # Sort users (Online first, then alphabetical)
        sorted_users = sorted(list(display_users), key=lambda x: (0 if x in self.online_users else 1, x.lower()))
        
        for user in sorted_users:
            if user and user != self.username:
                if user in self.online_users:
                    self.users_listbox.insert(tk.END, f"🟢 {user}")
                    self.users_listbox.itemconfig(tk.END, {'fg': '#075E54'})
                else:
                    self.users_listbox.insert(tk.END, f"⚪ {user}")
                    self.users_listbox.itemconfig(tk.END, {'fg': '#999999'})
    
    def add_message_to_history(self, chat_id, message, tag, sender=None, timestamp=None):
        # Add message to specific chat history
        if chat_id not in self.chat_history:
            self.chat_history[chat_id] = []
            
        # Track user if it's a private chat
        if chat_id != "ALL" and chat_id != self.username:
            if chat_id not in self.all_chat_users:
                self.all_chat_users.add(chat_id)
                self.window.after(0, self.refresh_user_listbox)
            
        self.chat_history[chat_id].append({
            'message': message,
            'tag': tag,
            'sender': sender,
            'timestamp': timestamp
        })
        
        # If currently view this chat, display it immediately
        if self.current_chat == chat_id:
            self.display_message(message, tag, sender, timestamp)

    def refresh_chat_display(self):
        # Clear and redraw chat for current selection
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.delete('1.0', tk.END)
        self.chat_display.config(state=tk.DISABLED)
        
        if self.current_chat in self.chat_history:
            for msg_data in self.chat_history[self.current_chat]:
                # Handle both old format (tuple) and new format (dict) for compatibility if needed
                if isinstance(msg_data, tuple):
                    self.display_message(msg_data[0], msg_data[1])
                else:
                    self.display_message(
                        msg_data['message'], 
                        msg_data['tag'], 
                        msg_data['sender'], 
                        msg_data['timestamp']
                    )

    def display_message(self, message, tag=None, sender=None, timestamp=None):
        # Display message in chat window
        self.chat_display.config(state=tk.NORMAL)
        
        if sender and timestamp and sender != "You":
            # For messages from others, make sender clickable
            self.chat_display.insert(tk.END, f"{sender}", 'clickable_user')
            self.chat_display.insert(tk.END, f" ({timestamp}):\n{message}\n\n", tag)
        elif sender == "You" and timestamp:
             self.chat_display.insert(tk.END, f"You ({timestamp}):\n{message}\n\n", tag)
        else:
            # Fallback for system messages or simple formatted strings
             self.chat_display.insert(tk.END, message + '\n\n', tag)
            
        self.chat_display.see(tk.END)
        self.chat_display.config(state=tk.DISABLED)
        
    def on_chat_username_click(self, event):
        # Handle click on username in chat
        try:
            # Get the index of the click
            index = self.chat_display.index(f"@{event.x},{event.y}")
            # Get the range of the tag 'clickable_user' at this index
            tags = self.chat_display.tag_names(index)
            if 'clickable_user' in tags:
                # Find the boundaries of the text with this tag
                start = self.chat_display.index(f"{index} wordstart")
                end = self.chat_display.index(f"{index} wordend")
                username = self.chat_display.get(start, end).strip()
                
                if username and username != self.username:
                    self.start_private_chat(username)
        except Exception as e:
            print(f"Error handling username click: {e}")
            
    def start_private_chat(self, username):
        # Switch to private chat with user
        self.selected_user = username
        self.current_chat = username
        
        if username not in self.all_chat_users:
            self.all_chat_users.add(username)
            self.refresh_user_listbox()
            
        if username not in self.chat_history:
            self.chat_history[username] = []
            
        self.chat_header_label.config(text=f"Private Chat with {username}")
        self.message_entry.focus()
        self.refresh_chat_display()
    
    def handle_disconnect(self):
        # Handle connection loss
        self.connected = False
        
        # Update UI
        self.window.title(f"ChatX - {self.username} (Disconnected)")
        self.status_label.config(text="Connection lost", fg='#DC3545')
        self.connect_button.config(state=tk.NORMAL)
        self.disconnect_button.config(state=tk.DISABLED)
        self.send_button.config(state=tk.DISABLED)
        
        self.display_message("✗ Connection lost", 'system')
        
        messagebox.showwarning("Connection Lost", "Your connection to the server was lost.")
    
    def on_closing(self):
        # Handle window close
        if self.connected:
            self.disconnect_from_server()
        
        self.window.destroy()
    
    def run(self):
        # Start GUI
        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.window.mainloop()

if __name__ == "__main__":
    client = ChatClient()
    client.run()
