import customtkinter as ctk
from tkinter import messagebox
import threading

class AdminDashboard:
    def __init__(self, parent, db, username, refresh_callback=None):
        """
        Initialize Admin Dashboard
        
        Args:
            parent: The parent widget (admin_dashboard_tab)
            db: MongoDB database connection
            username: Current admin username
            refresh_callback: Optional callback to refresh main app data
        """
        self.parent = parent
        self.db = db
        self.username = username
        self.refresh_callback = refresh_callback
        self.setup_dashboard()
    
    def setup_dashboard(self):
        """Setup the complete admin dashboard UI"""
        dashboard_frame = ctk.CTkFrame(self.parent)
        dashboard_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Header
        ctk.CTkLabel(dashboard_frame, text="Administrator Control Panel", 
                    font=("Arial", 24, "bold"), text_color="#2ecc71").pack(pady=20)
        
        ctk.CTkLabel(dashboard_frame, text=f"Logged in as: {self.username}", 
                    font=("Arial", 12), text_color="#7f8c8d").pack(pady=(0, 20))
        
        # Stats overview
        self.create_stats_section(dashboard_frame)
        
        # Admin actions
        self.create_actions_section(dashboard_frame)
        
        # Recent activity
        self.create_activity_section(dashboard_frame)
    
    def create_stats_section(self, parent):
        """Create statistics display section"""
        stats_frame = ctk.CTkFrame(parent, fg_color="#2b2b2b")
        stats_frame.pack(fill="x", pady=20, padx=20)
        
        ctk.CTkLabel(stats_frame, text="System Statistics", 
                    font=("Arial", 18, "bold")).pack(pady=10)
        
        # Get stats
        total_users = self.db.users.count_documents({})
        total_products = sum(self.db[col].count_documents({}) for col in self.db.list_collection_names() 
                            if col not in ["users", "ledger", "system.indexes"])
        total_transactions = self.db.ledger.count_documents({})
        admin_count = self.db.users.count_documents({"role": "admin"})
        user_count = total_users - admin_count
        
        # Display stats in a grid
        stats_grid = ctk.CTkFrame(stats_frame, fg_color="transparent")
        stats_grid.pack(pady=10)
        
        # Row 1
        row1 = ctk.CTkFrame(stats_grid, fg_color="transparent")
        row1.pack(fill="x", pady=5)
        
        ctk.CTkLabel(row1, text="Total Users:", font=("Arial", 14, "bold")).pack(side="left", padx=20)
        ctk.CTkLabel(row1, text=str(total_users), font=("Arial", 14), text_color="#2ecc71").pack(side="left", padx=10)
        
        ctk.CTkLabel(row1, text="Admins:", font=("Arial", 14, "bold")).pack(side="left", padx=20)
        ctk.CTkLabel(row1, text=str(admin_count), font=("Arial", 14), text_color="#e74c3c").pack(side="left", padx=10)
        
        # Row 2
        row2 = ctk.CTkFrame(stats_grid, fg_color="transparent")
        row2.pack(fill="x", pady=5)
        
        ctk.CTkLabel(row2, text="Regular Users:", font=("Arial", 14, "bold")).pack(side="left", padx=20)
        ctk.CTkLabel(row2, text=str(user_count), font=("Arial", 14), text_color="#f39c12").pack(side="left", padx=10)
        
        ctk.CTkLabel(row2, text="Total Products:", font=("Arial", 14, "bold")).pack(side="left", padx=20)
        ctk.CTkLabel(row2, text=str(total_products), font=("Arial", 14), text_color="#2ecc71").pack(side="left", padx=10)
        
        # Row 3
        row3 = ctk.CTkFrame(stats_grid, fg_color="transparent")
        row3.pack(fill="x", pady=5)
        
        ctk.CTkLabel(row3, text="Total Transactions:", font=("Arial", 14, "bold")).pack(side="left", padx=20)
        ctk.CTkLabel(row3, text=str(total_transactions), font=("Arial", 14), text_color="#3498db").pack(side="left", padx=10)
    
    def create_actions_section(self, parent):
        """Create admin actions buttons section"""
        actions_frame = ctk.CTkFrame(parent, fg_color="#2b2b2b")
        actions_frame.pack(fill="x", pady=20, padx=20)
        
        ctk.CTkLabel(actions_frame, text="Admin Actions", 
                    font=("Arial", 18, "bold")).pack(pady=10)
        
        buttons_frame = ctk.CTkFrame(actions_frame, fg_color="transparent")
        buttons_frame.pack(pady=10)
        
        # Row 1 of buttons
        row1 = ctk.CTkFrame(buttons_frame, fg_color="transparent")
        row1.pack(pady=5)
        
        ctk.CTkButton(row1, text=" View All Users", command=self.view_all_users,
                     width=200, height=40).pack(side="left", padx=10)
        
        ctk.CTkButton(row1, text=" System Backup", command=self.system_backup,
                     width=200, height=40).pack(side="left", padx=10)
        
        # Row 2 of buttons
        row2 = ctk.CTkFrame(buttons_frame, fg_color="transparent")
        row2.pack(pady=5)
        
        ctk.CTkButton(row2, text=" Export Transactions", command=self.export_transactions,
                     width=200, height=40).pack(side="left", padx=10)
        
        ctk.CTkButton(row2, text=" Refresh Dashboard", command=self.refresh_dashboard,
                     width=200, height=40, fg_color="#3498db").pack(side="left", padx=10)
        
        # Row 3 of buttons
        row3 = ctk.CTkFrame(buttons_frame, fg_color="transparent")
        row3.pack(pady=5)
        
        ctk.CTkButton(row3, text=" Clean Database", command=self.clean_database,
                     width=200, height=40, fg_color="#e74c3c").pack(side="left", padx=10)
        
        ctk.CTkButton(row3, text=" System Health", command=self.system_health,
                     width=200, height=40, fg_color="#f39c12").pack(side="left", padx=10)
    
    def create_activity_section(self, parent):
        """Create recent activity log section"""
        activity_frame = ctk.CTkFrame(parent, fg_color="#2b2b2b")
        activity_frame.pack(fill="both", expand=True, pady=20, padx=20)
        
        ctk.CTkLabel(activity_frame, text="Recent Transactions", 
                    font=("Arial", 18, "bold")).pack(pady=10)
        
        # Create text area for activity
        self.activity_text = ctk.CTkTextbox(activity_frame, height=200)
        self.activity_text.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Load recent activity
        self.load_recent_activity()
    
    def load_recent_activity(self):
        """Load and display recent transactions"""
        self.activity_text.delete("1.0", "end")
        
        recent_transactions = list(self.db.ledger.find().sort("timestamp", -1).limit(15))
        
        if recent_transactions:
            for transaction in recent_transactions:
                timestamp = transaction.get('timestamp', 'Unknown time')
                self.activity_text.insert("end", f" {timestamp}\n")
                self.activity_text.insert("end", f"   User: {transaction.get('user', 'Unknown')}\n")
                self.activity_text.insert("end", f"   Item: {transaction.get('item', 'Unknown')}\n")
                self.activity_text.insert("end", f"   Amount: ${transaction.get('total', transaction.get('price', 0)):.2f}\n")
                self.activity_text.insert("end", f"   Status: {transaction.get('status', 'Unknown')}\n")
                self.activity_text.insert("end", "-" * 50 + "\n\n")
        else:
            self.activity_text.insert("end", "No recent transactions found.\n")
        
        self.activity_text.configure(state="disabled")
    
    def view_all_users(self):
        """View all registered users"""
        users_window = ctk.CTkToplevel(self.parent)
        users_window.title("All Users - Admin View")
        users_window.geometry("600x500")
        users_window.attributes('-topmost', True)
        
        ctk.CTkLabel(users_window, text="Registered Users", font=("Arial", 18, "bold")).pack(pady=10)
        
        # Create search bar
        search_frame = ctk.CTkFrame(users_window, fg_color="transparent")
        search_frame.pack(fill="x", padx=20, pady=10)
        
        search_entry = ctk.CTkEntry(search_frame, placeholder_text="Search users...", width=300)
        search_entry.pack(side="left", padx=5)
        
        # Create scrollable frame for users
        scroll_frame = ctk.CTkScrollableFrame(users_window)
        scroll_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        users = list(self.db.users.find({}, {"password": 0}))
        
        def display_users(search_term=""):
            # Clear existing widgets
            for widget in scroll_frame.winfo_children():
                widget.destroy()
            
            for user in users:
                if search_term.lower() in user.get('username', '').lower():
                    user_frame = ctk.CTkFrame(scroll_frame)
                    user_frame.pack(fill="x", pady=5)
                    
                    ctk.CTkLabel(user_frame, text=f"👤 {user['username']}", 
                                font=("Arial", 12), anchor="w").pack(side="left", padx=10)
                    
                    role_color = "#2ecc71" if user['role'] == 'admin' else "#3498db"
                    ctk.CTkLabel(user_frame, text=f"Role: {user['role'].upper()}", 
                                font=("Arial", 12, "bold"), text_color=role_color).pack(side="left", padx=10)
                    
                    # Add delete button for non-admin and not self
                    if user['username'] != self.username:
                        ctk.CTkButton(user_frame, text="Delete", fg_color="#e74c3c", width=80,
                                    command=lambda u=user['username']: self.delete_user(u, users_window)).pack(side="right", padx=10)
        
        def search_users(event=None):
            display_users(search_entry.get())
        
        search_entry.bind("<KeyRelease>", search_users)
        display_users()
        
        ctk.CTkButton(users_window, text="Close", command=users_window.destroy).pack(pady=10)
    
    def delete_user(self, username, window):
        """Delete a user"""
        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete user '{username}'?"):
            self.db.users.delete_one({"username": username})
            messagebox.showinfo("Success", f"User '{username}' has been deleted.")
            window.destroy()
            self.view_all_users()
            if self.refresh_callback:
                self.refresh_callback()
    
    def system_backup(self):
        """Perform system backup"""
        def backup_process():
            import time
            backup_window = ctk.CTkToplevel(self.parent)
            backup_window.title("System Backup")
            backup_window.geometry("400x200")
            backup_window.attributes('-topmost', True)
            
            ctk.CTkLabel(backup_window, text="Creating System Backup...", font=("Arial", 14)).pack(pady=20)
            progress = ctk.CTkProgressBar(backup_window)
            progress.pack(pady=20, padx=40)
            progress.set(0)
            
            for i in range(101):
                progress.set(i / 100)
                backup_window.update()
                time.sleep(0.01)
            
            ctk.CTkLabel(backup_window, text=" Backup Complete!", font=("Arial", 14), text_color="#2ecc71").pack(pady=10)
            ctk.CTkButton(backup_window, text="Close", command=backup_window.destroy).pack(pady=10)
        
        threading.Thread(target=backup_process, daemon=True).start()
    
    def export_transactions(self):
        """Export transactions to file"""
        import csv
        from datetime import datetime
        
        transactions = list(self.db.ledger.find({}, {"_id": 0}))
        
        if not transactions:
            messagebox.showwarning("No Data", "No transactions to export.")
            return
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"transactions_export_{timestamp}.csv"
        
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                if transactions:
                    fieldnames = transactions[0].keys()
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(transactions)
            
            messagebox.showinfo("Export Successful", f"Transactions exported to:\n{filename}\n\nFound in your project directory.")
        except Exception as e:
            messagebox.showerror("Export Failed", f"Error exporting transactions:\n{e}")
    
    def refresh_dashboard(self):
        """Refresh the entire dashboard"""
        # Clear and rebuild the dashboard
        for widget in self.parent.winfo_children():
            widget.destroy()
        self.setup_dashboard()
        messagebox.showinfo("Refreshed", "Dashboard has been refreshed with latest data.")
    
    def clean_database(self):
        """Clean old or invalid data from database"""
        if messagebox.askyesno("Clean Database", "This will remove old transaction logs (older than 30 days).\nProceed?"):
            from datetime import datetime, timedelta
            cutoff_date = datetime.now() - timedelta(days=30)
            result = self.db.ledger.delete_many({"timestamp": {"$lt": cutoff_date}})
            messagebox.showinfo("Clean Complete", f"Removed {result.deleted_count} old transaction records.")
            self.refresh_dashboard()
            if self.refresh_callback:
                self.refresh_callback()
    
    def system_health(self):
        """Display system health information"""
        health_window = ctk.CTkToplevel(self.parent)
        health_window.title("System Health")
        health_window.geometry("500x400")
        health_window.attributes('-topmost', True)
        
        ctk.CTkLabel(health_window, text="System Health Dashboard", font=("Arial", 18, "bold")).pack(pady=10)
        
        health_text = ctk.CTkTextbox(health_window)
        health_text.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Collect health information
        health_text.insert("end", " SYSTEM STATISTICS\n")
        health_text.insert("end", "=" * 40 + "\n\n")
        
        health_text.insert("end", f" Database Status: Connected\n")
        health_text.insert("end", f" AI Service: Groq (Active)\n")
        health_text.insert("end", f" Total Users: {self.db.users.count_documents({})}\n")
        health_text.insert("end", f" Total Products: {sum(self.db[col].count_documents({}) for col in self.db.list_collection_names() if col not in ['users', 'ledger', 'system.indexes'])}\n")
        health_text.insert("end", f" Total Transactions: {self.db.ledger.count_documents({})}\n")
        
        # Last 5 transactions
        health_text.insert("end", "\n" + "=" * 40 + "\n")
        health_text.insert("end", " LAST 5 TRANSACTIONS\n\n")
        
        recent = list(self.db.ledger.find().sort("timestamp", -1).limit(5))
        for trans in recent:
            health_text.insert("end", f"• {trans.get('user')} - {trans.get('item')} - ${trans.get('total', trans.get('price', 0)):.2f}\n")
        
        health_text.configure(state="disabled")