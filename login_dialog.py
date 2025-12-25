import tkinter as tk
from tkinter import messagebox

class BaseDialog:
    def __init__(self, parent, title, height=300):
        self.result = False
        self.username = None
        self.password = None
        self.action = None
        self.next_action = None  # To switch screens
        
        # Create dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(f"ChatX - {title}")
        self.dialog.geometry(f"450x{height}")
        self.dialog.configure(bg='#ECE5DD')
        self.dialog.resizable(False, False)
        
        # Center the dialog
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Header with WhatsApp-style colors
        header_frame = tk.Frame(self.dialog, bg='#075E54', height=80)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)
        
        # Title
        title_label = tk.Label(
            header_frame,
            text="ChatX",
            bg='#075E54',
            fg='white',
            font=('Segoe UI', 24, 'bold')
        )
        title_label.pack(pady=20)
        
        # Main content frame
        self.content_frame = tk.Frame(self.dialog, bg='#ECE5DD', padx=30, pady=20)
        self.content_frame.pack(fill=tk.BOTH, expand=True)

    def close(self):
        self.dialog.destroy()

    def show(self):
        self.dialog.wait_window()
        return self.result, self.username, self.password, self.action, self.next_action

class LoginDialog(BaseDialog):
    def __init__(self, parent):
        super().__init__(parent, "Login", height=400)
        
        # Subtitle
        tk.Label(
            self.content_frame,
            text="Welcome back! Please login.",
            bg='#ECE5DD',
            fg='#075E54',
            font=('Segoe UI', 11)
        ).pack(pady=(0, 20))
        
        # Input frame
        input_frame = tk.Frame(self.content_frame, bg='#ECE5DD')
        input_frame.pack()
        
        # Username
        tk.Label(
            input_frame,
            text="Username:",
            bg='#ECE5DD',
            fg='#075E54',
            font=('Segoe UI', 10, 'bold')
        ).grid(row=0, column=0, sticky='w', pady=8)
        
        self.username_entry = tk.Entry(
            input_frame,
            font=('Segoe UI', 10),
            width=30,
            bg='white',
            relief=tk.SOLID,
            borderwidth=1
        )
        self.username_entry.grid(row=0, column=1, pady=8, padx=10)
        self.username_entry.focus()
        
        # Password
        tk.Label(
            input_frame,
            text="Password:",
            bg='#ECE5DD',
            fg='#075E54',
            font=('Segoe UI', 10, 'bold')
        ).grid(row=1, column=0, sticky='w', pady=8)
        
        self.password_entry = tk.Entry(
            input_frame,
            font=('Segoe UI', 10),
            width=30,
            show='●',
            bg='white',
            relief=tk.SOLID,
            borderwidth=1
        )
        self.password_entry.grid(row=1, column=1, pady=8, padx=10)
        
        # Bind Enter key
        self.username_entry.bind('<Return>', lambda e: self.password_entry.focus())
        self.password_entry.bind('<Return>', lambda e: self.login())
        
        # Button frame
        button_frame = tk.Frame(self.content_frame, bg='#ECE5DD')
        button_frame.pack(pady=20)
        
        # Login button
        tk.Button(
            button_frame,
            text="Login",
            command=self.login,
            bg='#25D366',
            fg='white',
            font=('Segoe UI', 11, 'bold'),
            width=12,
            relief=tk.FLAT,
            cursor='hand2'
        ).pack(side=tk.LEFT, padx=5)
        
        # Create Account Section
        link_frame = tk.Frame(self.content_frame, bg='#ECE5DD')
        link_frame.pack(pady=(10, 0))
        
        lbl_question = tk.Label(
            link_frame,
            text="Don't have an account?",
            bg='#ECE5DD',
            fg='#666',
            font=('Segoe UI', 9),
            cursor='hand2'
        )
        lbl_question.pack()
        lbl_question.bind('<Button-1>', lambda e: self.go_to_register())
        
        btn_create = tk.Button(
            self.content_frame,
            text="Create Account",
            command=self.go_to_register,
            bg='#ECE5DD',
            fg='#075E54',
            font=('Segoe UI', 9, 'bold', 'underline'),
            relief=tk.FLAT,
            cursor='hand2',
            activebackground='#ECE5DD'
        )
        btn_create.pack()

    def login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        
        if not username or not password:
            messagebox.showerror("Error", "Please enter both username and password", parent=self.dialog)
            return
            
        self.username = username
        self.password = password
        self.action = "LOGIN"
        self.result = True
        self.close()

    def go_to_register(self):
        print("Switching to REGISTER mode")
        self.next_action = "SWITCH_TO_REGISTER"
        self.close()

class RegisterDialog(BaseDialog):
    def __init__(self, parent):
        super().__init__(parent, "Register", height=450)
        
        # Subtitle
        tk.Label(
            self.content_frame,
            text="Create a new account",
            bg='#ECE5DD',
            fg='#075E54',
            font=('Segoe UI', 11)
        ).pack(pady=(0, 20))
        
        # Input frame
        input_frame = tk.Frame(self.content_frame, bg='#ECE5DD')
        input_frame.pack()
        
        # Username
        tk.Label(
            input_frame,
            text="Username:",
            bg='#ECE5DD',
            fg='#075E54',
            font=('Segoe UI', 10, 'bold')
        ).grid(row=0, column=0, sticky='w', pady=8)
        
        self.username_entry = tk.Entry(
            input_frame,
            font=('Segoe UI', 10),
            width=30,
            bg='white',
            relief=tk.SOLID,
            borderwidth=1
        )
        self.username_entry.grid(row=0, column=1, pady=8, padx=10)
        self.username_entry.focus()
        
        # Password
        tk.Label(
            input_frame,
            text="Password:",
            bg='#ECE5DD',
            fg='#075E54',
            font=('Segoe UI', 10, 'bold')
        ).grid(row=1, column=0, sticky='w', pady=8)
        
        self.password_entry = tk.Entry(
            input_frame,
            font=('Segoe UI', 10),
            width=30,
            show='●',
            bg='white',
            relief=tk.SOLID,
            borderwidth=1
        )
        self.password_entry.grid(row=1, column=1, pady=8, padx=10)
        
        # Confirm Password
        tk.Label(
            input_frame,
            text="Confirm:",
            bg='#ECE5DD',
            fg='#075E54',
            font=('Segoe UI', 10, 'bold')
        ).grid(row=2, column=0, sticky='w', pady=8)
        
        self.confirm_entry = tk.Entry(
            input_frame,
            font=('Segoe UI', 10),
            width=30,
            show='●',
            bg='white',
            relief=tk.SOLID,
            borderwidth=1
        )
        self.confirm_entry.grid(row=2, column=1, pady=8, padx=10)
        
        # Button frame
        button_frame = tk.Frame(self.content_frame, bg='#ECE5DD')
        button_frame.pack(pady=20)
        
        # Register button
        tk.Button(
            button_frame,
            text="Register",
            command=self.register,
            bg='#128C7E',
            fg='white',
            font=('Segoe UI', 11, 'bold'),
            width=12,
            relief=tk.FLAT,
            cursor='hand2'
        ).pack(side=tk.LEFT, padx=5)
        
        # Login link Section
        link_frame = tk.Frame(self.content_frame, bg='#ECE5DD')
        link_frame.pack(pady=(10, 0))
        
        lbl_question = tk.Label(
            link_frame,
            text="Already have an account?",
            bg='#ECE5DD',
            fg='#666',
            font=('Segoe UI', 9),
            cursor='hand2'
        )
        lbl_question.pack()
        lbl_question.bind('<Button-1>', lambda e: self.go_to_login())
        
        btn_login = tk.Button(
            self.content_frame,
            text="Back to Login",
            command=self.go_to_login,
            bg='#ECE5DD',
            fg='#075E54',
            font=('Segoe UI', 9, 'bold', 'underline'),
            relief=tk.FLAT,
            cursor='hand2',
            activebackground='#ECE5DD'
        )
        btn_login.pack()

    def register(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        confirm = self.confirm_entry.get().strip()
        
        if not username or not password or not confirm:
            messagebox.showerror("Error", "Please fill all fields", parent=self.dialog)
            return
            
        if len(username) < 3:
            messagebox.showerror("Error", "Username must be at least 3 characters", parent=self.dialog)
            return

        if len(password) < 4:
            messagebox.showerror("Error", "Password must be at least 4 characters", parent=self.dialog)
            return
            
        if password != confirm:
            messagebox.showerror("Error", "Passwords do not match", parent=self.dialog)
            return
            
        self.username = username
        self.password = password
        self.action = "REGISTER"
        self.result = True
        self.close()

    def go_to_login(self):
        print("Switching to LOGIN mode")
        self.next_action = "SWITCH_TO_LOGIN"
        self.close()
