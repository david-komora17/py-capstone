import customtkinter as ctk
from tkinter import messagebox
from pymongo import MongoClient
import os
from dotenv import load_dotenv
import hashlib

load_dotenv()

class LoginWindow(ctk.CTk):
    def __init__(self, on_success):
        super().__init__()
        self.on_success = on_success
        self.title("Nexus Hub Authentication Gateway")
        self.geometry("400x520")
        ctk.set_appearance_mode("dark")
        
        # Admin secret key verification configuration
        self.admin_verification_key = "ADMIN_VERIFY_2024"

        try:
            self.client = MongoClient(os.getenv("MONGO_URI"), serverSelectionTimeoutMS=5000)
            self.db = self.client["inventory_db"]
            self.users_col = self.db["users"]
            
            # Verify database connection explicitly
            self.client.server_info()
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

        self.signup_button = ctk.CTkButton(self, text="Create An Account",
                                           fg_color="transparent", border_width=1, border_color="#333", command=self.open_signup)
        self.signup_button.pack(pady=10)

        self.login_button = ctk.CTkButton(self, text="Login", fg_color="#2ecc71", text_color="black", font=("Arial", 12, "bold"), command=self.login)
        self.login_button.pack(pady=24)

    def ensure_default_admin(self):
        """Create default admin account if no admins exist (one-time backup setup)"""
        admin_exists = self.users_col.find_one({"role": "admin"})
        if not admin_exists:
            default_admin = {
                "username": "master_admin",
                "password": self.hash_password("SecurePass123!"),
                "role": "admin",
                "created_by": "system",
                "created_at": "initial_setup"
            }
            self.users_col.insert_one(default_admin)
            print("⚠️ Default admin created: username='master_admin', password='SecurePass123!'")

    def hash_password(self, password):
        """Simple password hashing using SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()

    def open_signup(self):
        self.signup_win = ctk.CTkToplevel(self)
        self.signup_win.title("Create New Account")
        self.signup_win.geometry("350x460")  # Slightly larger to clean up field spacing
        self.signup_win.attributes('-topmost', True)

        ctk.CTkLabel(self.signup_win, text="Create New Account", font=("Roboto", 18, "bold")).pack(pady=20)

        self.new_user = ctk.CTkEntry(self.signup_win, placeholder_text="Choose Username", width=200)
        self.new_user.pack(pady=10)

        self.new_pass = ctk.CTkEntry(self.signup_win, placeholder_text="Create Password", show="*", width=200)
        self.new_pass.pack(pady=10)

        self.confirm_pass = ctk.CTkEntry(self.signup_win, placeholder_text="Confirm Password", show="*", width=200)
        self.confirm_pass.pack(pady=10)

        # Visible token entry. If blank -> regular user. If valid token -> admin account.
        self.admin_key_entry = ctk.CTkEntry(self.signup_win, placeholder_text="Admin Registration Key (Optional)", show="*", width=200)
        self.admin_key_entry.pack(pady=10)

        ctk.CTkButton(self.signup_win, text="Create Account", fg_color="#2ecc71", text_color="black", command=self.register_user).pack(pady=20)
        
        ctk.CTkLabel(self.signup_win, text="Leave Admin Key blank for a standard account.", 
                    font=("Roboto", 9), text_color="gray").pack(pady=5)

    def register_user(self):
        username = self.new_user.get().strip()
        password = self.new_pass.get().strip()
        confirm_password = self.confirm_pass.get().strip()
        admin_key_provided = self.admin_key_entry.get().strip()

        if not username or not password:
            messagebox.showwarning("Incomplete Form", "All main fields are required.", parent=self.signup_win)
            return

        if password != confirm_password:
            messagebox.showerror("Password Mismatch", "Passwords do not match!", parent=self.signup_win)
            return

        if len(password) < 6:
            messagebox.showerror("Weak Password", "Password must be at least 6 characters long!", parent=self.signup_win)
            return

        if self.users_col.find_one({"username": username}):
            messagebox.showerror("Username Taken", "Username is already taken.", parent=self.signup_win)
            return

        # Determine structural role profile context dynamically
        assigned_role = "user"
        creation_meta = "standard_signup"

        if admin_key_provided:
            if admin_key_provided == self.admin_verification_key:
                assigned_role = "admin"
                creation_meta = "authorized_admin_signup"
            else:
                messagebox.showerror("Invalid Token", "The Admin Key provided is incorrect!\nAccount registration canceled.", parent=self.signup_win)
                return

        # Save record cleanly
        self.users_col.insert_one({
            "username": username,
            "password": self.hash_password(password),
            "role": assigned_role,
            "created_at": creation_meta
        })
        
        account_type_str = "an Administrator" if assigned_role == "admin" else "a Standard User"
        messagebox.showinfo("Success", f"Registered successfully as {account_type_str}!\nYou can now log in.", parent=self.signup_win)
        self.signup_win.destroy()

    def login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        
        hashed_password = self.hash_password(password)
        user = self.users_col.find_one({"username": username, "password": hashed_password})

        if user:
            role = user.get("role", "user")
            messagebox.showinfo("Login Successful", f"Welcome back, {username}!\nAccess level: {role.upper()}")
            self.destroy()
            self.on_success(role, username)
        else:
            messagebox.showerror("Login Failed", "Invalid username or password.")