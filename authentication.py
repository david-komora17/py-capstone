import customtkinter as ctk
from tkinter import messagebox
from pymongo import MongoClient
import os
from dotenv import load_dotenv
import hashlib
import secrets

load_dotenv()

class LoginWindow(ctk.CTk):
    def __init__(self, on_success):
        super().__init__()
        self.on_success = on_success
        self.title("Nexus Hub Authentication Gateway")
        self.geometry("400x520")
        ctk.set_appearance_mode("dark")
        
        # Hidden admin creation attempt counter
        self.hidden_admin_attempts = []
        self.admin_secret_code = "NEXUS_ADMIN_2024"  # Secret code for admin creation

        try:
            self.client = MongoClient(os.getenv("MONGO_URI"), serverSelectionTimeoutMS=5000)
            self.db = self.client["inventory_db"]
            self.users_col = self.db["users"]
            # Forces validation check right at connection initialization
            self.client.server_info()
            
            # Create default admin if none exists (one-time setup)
            self.ensure_default_admin()
        except Exception as e:
            messagebox.showerror("Cluster Database Error", f"Cannot access secure MongoDB profile collection cluster:\n{e}")
            os._exit(1)

        # UI elements
        self.label = ctk.CTkLabel(self, text='NEXUS SECURE ACCESS', font=("Roboto", 20, "bold"), text_color="#2ecc71")
        self.label.pack(pady=40)

        self.username_entry = ctk.CTkEntry(self, placeholder_text="Username", width=250)
        self.username_entry.pack(pady=12)

        self.password_entry = ctk.CTkEntry(self, placeholder_text="Password", show="*", width=250)
        self.password_entry.pack(pady=12)

        # Remove role selection from signup - all new users are regular users
        self.signup_button = ctk.CTkButton(self, text="Create An Account",
                                           fg_color="transparent", border_width=1, border_color="#333", command=self.open_signup)
        self.signup_button.pack(pady=10)

        self.login_button = ctk.CTkButton(self, text="Login", fg_color="#2ecc71", text_color="black", font=("Arial", 12, "bold"), command=self.login)
        self.login_button.pack(pady=24)

    def ensure_default_admin(self):
        """Create default admin account if no admins exist (one-time setup)"""
        admin_exists = self.users_col.find_one({"role": "admin"})
        if not admin_exists:
            # Create a secure default admin (change this password after first login!)
            default_admin = {
                "username": "master_admin",
                "password": self.hash_password("SecurePass123!"),
                "role": "admin",
                "created_by": "system",
                "created_at": "initial_setup"
            }
            self.users_col.insert_one(default_admin)
            print("⚠️ Default admin created: username='master_admin', password='SecurePass123!'")
            print("   PLEASE CHANGE THIS PASSWORD AFTER FIRST LOGIN!")

    def hash_password(self, password):
        """Simple password hashing (in production, use bcrypt or similar)"""
        return hashlib.sha256(password.encode()).hexdigest()

    def open_signup(self):
        self.signup_win = ctk.CTkToplevel(self)
        self.signup_win.title("Create New Account")
        self.signup_win.geometry("350x400")
        self.signup_win.attributes('-topmost', True)

        ctk.CTkLabel(self.signup_win, text="Create New Account", font=("Roboto", 18, "bold")).pack(pady=20)

        self.new_user = ctk.CTkEntry(self.signup_win, placeholder_text="Choose Username", width=200)
        self.new_user.pack(pady=10)

        self.new_pass = ctk.CTkEntry(self.signup_win, placeholder_text="Create Password", show="*", width=200)
        self.new_pass.pack(pady=10)

        self.confirm_pass = ctk.CTkEntry(self.signup_win, placeholder_text="Confirm Password", show="*", width=200)
        self.confirm_pass.pack(pady=10)

        # Hidden admin creation section (not visible to regular users)
        self.admin_hint = ctk.CTkLabel(self.signup_win, text="", font=("Roboto", 8), text_color="gray")
        
        # Bind key sequence for hidden admin creation (type: ADMIN2024 while signing up)
        self.new_user.bind("<KeyRelease>", self.check_hidden_admin_sequence)

        ctk.CTkButton(self.signup_win, text="Create Account", fg_color="#2ecc71", text_color="black", command=self.register_user).pack(pady=20)
        
        ctk.CTkLabel(self.signup_win, text="All accounts are standard user accounts by default.", 
                    font=("Roboto", 9), text_color="gray").pack(pady=10)

    def check_hidden_admin_sequence(self, event):
        """Hidden method to detect secret code for admin creation"""
        current_text = self.new_user.get()
        
        # Add current character to attempts tracking
        self.hidden_admin_attempts.append(event.char)
        
        # Keep only last 50 characters
        if len(self.hidden_admin_attempts) > 50:
            self.hidden_admin_attempts = self.hidden_admin_attempts[-50:]
        
        # Check if the secret code sequence appears in username
        if self.admin_secret_code.lower() in current_text.lower():
            self.show_hidden_admin_dialog()
            # Clear the secret code from username
            clean_username = current_text.lower().replace(self.admin_secret_code.lower(), "").strip()
            self.new_user.delete(0, ctk.END)
            self.new_user.insert(0, clean_username)

    def show_hidden_admin_dialog(self):
        """Show admin creation dialog with additional verification"""
        admin_dialog = ctk.CTkToplevel(self)
        admin_dialog.title("Administrator Creation")
        admin_dialog.geometry("400x300")
        admin_dialog.attributes('-topmost', True)
        
        ctk.CTkLabel(admin_dialog, text="⚠️ ADMINISTRATOR ACCOUNT CREATION ⚠️", 
                    font=("Roboto", 16, "bold"), text_color="#e74c3c").pack(pady=20)
        
        ctk.CTkLabel(admin_dialog, text="You are about to create an ADMIN account.", 
                    font=("Roboto", 12)).pack(pady=5)
        ctk.CTkLabel(admin_dialog, text="This should only be done by authorized personnel!", 
                    font=("Roboto", 10), text_color="#e74c3c").pack(pady=5)
        
        ctk.CTkLabel(admin_dialog, text="Enter Admin Verification Key:", font=("Roboto", 12)).pack(pady=10)
        verification_entry = ctk.CTkEntry(admin_dialog, placeholder_text="Verification Key", width=200, show="*")
        verification_entry.pack(pady=10)
        
        def verify_and_create():
            verification_key = verification_entry.get()
            # Check verification key (can be changed to any secret)
            if verification_key == "ADMIN_VERIFY_2024":
                # Create admin account
                username = self.new_user.get().strip()
                password = self.new_pass.get().strip()
                
                if not username or not password:
                    messagebox.showerror("Error", "Please fill in username and password first!", parent=admin_dialog)
                    return
                
                if self.users_col.find_one({"username": username}):
                    messagebox.showerror("Error", "Username already exists!", parent=admin_dialog)
                    return
                
                # Create admin user
                self.users_col.insert_one({
                    "username": username,
                    "password": self.hash_password(password),
                    "role": "admin",
                    "created_by": "hidden_admin_creation",
                    "created_at": "special_access"
                })
                
                messagebox.showinfo("Success", f"Admin account '{username}' created successfully!\nYou can now login as admin.")
                admin_dialog.destroy()
                self.signup_win.destroy()
            else:
                messagebox.showerror("Error", "Invalid verification key!\nAdmin creation denied.", parent=admin_dialog)
        
        ctk.CTkButton(admin_dialog, text="Verify & Create Admin", fg_color="#e74c3c", 
                     command=verify_and_create).pack(pady=20)

    def register_user(self):
        username = self.new_user.get().strip()
        password = self.new_pass.get().strip()
        confirm_password = self.confirm_pass.get().strip()

        if not username or not password:
            messagebox.showwarning("Incomplete Form", "All fields are required.", parent=self.signup_win)
            return

        if password != confirm_password:
            messagebox.showerror("Password Mismatch", "Passwords do not match!", parent=self.signup_win)
            return

        if len(password) < 6:
            messagebox.showerror("Weak Password", "Password must be at least 6 characters long!", parent=self.signup_win)
            return

        if self.users_col.find_one({"username": username}):
            messagebox.showerror("Username Taken", "Username is already taken.", parent=self.signup_win)
        else:
            # All regular signups are standard users
            self.users_col.insert_one({
                "username": username,
                "password": self.hash_password(password),
                "role": "user",  # Force role to 'user' for all normal signups
                "created_at": "standard_signup"
            })
            messagebox.showinfo("Success", f"Account created for {username}!\nYou can now login.", parent=self.signup_win)
            self.signup_win.destroy()

    def login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        
        # Hash the password for comparison
        hashed_password = self.hash_password(password)

        user = self.users_col.find_one({"username": username, "password": hashed_password})

        if user:
            role = user.get("role", "user")
            messagebox.showinfo("Login Successful", f"Welcome back, {username}!\nAccess level: {role.upper()}")
            self.destroy()
            self.on_success(role, username)
        else:
            messagebox.showerror("Login Failed", "Invalid username or password.")