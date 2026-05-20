import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox, ttk
from pymongo import MongoClient
import os
import threading
from authentication import LoginWindow
from dotenv import load_dotenv
from admin_dash import AdminDashboard
from PIL import Image
from io import BytesIO
import requests
import json
from datetime import datetime
from groq import Groq


load_dotenv()

# --- Configs ---
MONGO_URI = os.getenv("MONGO_URI")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
groq_client = Groq(api_key=GROQ_API_KEY)

try:
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    db = client["inventory_db"]
    client.server_info()
except Exception as e:
    root = tk.Tk()
    root.withdraw()
    messagebox.showerror("Database Error", f"Failed to connect to MongoDB Atlas:\n{e}")
    os._exit(1)

    

class ShoppingCart:
    def __init__(self):
        self.items = []  # Each item: {product, category, quantity, price}
    
    def add_item(self, product, category, quantity, price):
        self.items.append({
            "product": product,
            "category": category,
            "quantity": quantity,
            "price": price,
            "total": quantity * price
        })
    
    def remove_item(self, index):
        if 0 <= index < len(self.items):
            del self.items[index]
    
    def get_total(self):
        return sum(item["total"] for item in self.items)
    
    def clear(self):
        self.items = []
    
    def get_items(self):
        return self.items

class NexusApp(ctk.CTk):
    def __init__(self, role, username):
        super().__init__()
        self.title("Nexus Smart Inventory Manager")
        self.geometry("1200x850")
        self.role = role
        self.username = username
        self.img_refs = {}
        self.cart = ShoppingCart()
        self.current_category_filter = "All"

        # Configure custom modern styles for the Treeview widget
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", background="#2b2b2b", foreground="white", fieldbackground="#2b2b2b", rowheight=30, borderwidth=0)
        style.map("Treeview", background=[("selected", "#2ecc71")], foreground=[("selected", "black")])
        style.configure("Treeview.Heading", background="#1a1a1a", foreground="#2ecc71", borderwidth=0, font=("Arial", 12, "bold"))

        # --- Navbar ---
        self.nav = ctk.CTkFrame(self, height=80, corner_radius=0, fg_color="#1a1a1a")
        self.nav.pack(fill="x", side="top")
        
        ctk.CTkLabel(self.nav, text="NEXUS SMART INVENTORY", font=("Helvetica", 24, "bold"), text_color="#2ecc71").pack(side="left", padx=30)
        
        # Cart button with count
        self.cart_btn = ctk.CTkButton(
            self.nav, text=" Cart (0)", fg_color="#2ecc71", text_color="black",
            command=self.open_cart_window, width=100
        )
        self.cart_btn.pack(side="right", padx=10)
        
        self.acc_menu = ctk.CTkOptionMenu(
            self.nav, values=[f"Hi, {username} ({role.upper()})", "Logout"],
            command=self.handle_account, fg_color="#2b2b2b"
        )
        self.acc_menu.pack(side="right", padx=30)

        # --- Tabs ---
        self.tabs = ctk.CTkTabview(self, segmented_button_selected_color="#2ecc71")
        self.tabs.pack(fill="both", expand=True, padx=20, pady=10)
        self.market_tab = self.tabs.add("Marketplace")
        self.admin_tab = self.tabs.add("Inventory Control Center")
        self.chat_tab = self.tabs.add("AI Assistant")
        self.ledger_tab = self.tabs.add("Transactions")

        if role == "admin":
            # Remove the marketplace tab for admins
            self.tabs.delete("Marketplace")
            # Optionally add an admin dashboard tab
            self.admin_dash_tab = self.tabs.add("Admin Dashboard")
            self.admin_dash = AdminDashboard(self.admin_dash_tab, db, self.username, refresh_callback=self.refresh_all)
        else:
            # Regular users don't see the admin tab
            self.tabs.delete("Inventory Control Center")

        # Layout placeholders
        self.setup_crud_tab()
        self.setup_ai_chat() 
        self.refresh_all()

    def handle_account(self, choice):
        if "Logout" in choice:
            self.destroy()
            LoginWindow(on_success=launch_main_app).mainloop()

    def update_cart_button(self):
        total_items = len(self.cart.items)
        self.cart_btn.configure(text=f"🛒 Cart ({total_items})")

    # --- ASYNC DATABASE PIPELINE ---
    def refresh_all(self):
        threading.Thread(target=self.fetch_data_async, daemon=True).start()

    def fetch_data_async(self):
        try:
            search_query = self.search_entry.get().strip() if hasattr(self, 'search_entry') else ""
            data_payload = {}
            
            all_collections = db.list_collection_names()
            excluded_tables = ["users", "ledger", "system.indexes"]
            inventory_categories = [col for col in all_collections if col not in excluded_tables]
            
            for cat in inventory_categories:
                if self.current_category_filter != "All" and cat != self.current_category_filter:
                    continue
                    
                if search_query:
                    data_payload[cat] = list(db[cat].find({"name": {"$regex": search_query, "$options": "i"}}))
                else:
                    data_payload[cat] = list(db[cat].find())
            
            ledger_data = list(db["ledger"].find({} if self.role == "admin" else {"user": self.username}))
            
            self.after(0, lambda: self.render_ui_with_data(data_payload, ledger_data))
        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Database Pipeline Error", f"Data synchronization failed:\n{e}"))

    def render_ui_with_data(self, catalog_data, ledger_data):
        self.render_marketplace(catalog_data)
        self.update_treeview(catalog_data)
        self.render_ledger(ledger_data)
        # This updates the inventory value when data is updated.
        if self.role == "admin":
            self.update_inventory_value()

    # --- CRUD DASHBOARD (TREEVIEW IMPLEMENTATION) ---
    def setup_crud_tab(self):
        if self.role != "admin":
            ctk.CTkLabel(self.admin_tab, text="Access Restricted to System Administrators.", font=("Arial", 20)).pack(pady=100)
            return

        # Toolbar
        tools = ctk.CTkFrame(self.admin_tab, fg_color="transparent")
        tools.pack(fill="x", padx=20, pady=10)

        self.search_entry = ctk.CTkEntry(tools, placeholder_text="Search inventory by name...", width=300)
        self.search_entry.pack(side="left", padx=(0, 10))
        self.search_entry.bind("<KeyRelease>", lambda e: self.refresh_all())

        # Category filter for admin view
        ctk.CTkLabel(tools, text="Filter Category:", font=("Arial", 12)).pack(side="left", padx=(10, 5))
        self.admin_category_filter = ctk.CTkOptionMenu(
            tools, values=["All", "electronics", "furniture", "clothing", "books", "sports"],
            command=self.filter_by_category, width=150
        )
        self.admin_category_filter.pack(side="left", padx=5)

        ctk.CTkButton(tools, text="+ Add Product", fg_color="#2ecc71", text_color="black", font=("Arial", 12, "bold"), command=self.add_product_window).pack(side="right", padx=5)
        ctk.CTkButton(tools, text="Edit Selected", fg_color="#f39c12", text_color="black", font=("Arial", 12, "bold"), command=self.open_edit_window).pack(side="right", padx=5)
        ctk.CTkButton(tools, text="Delete Selected", fg_color="#e74c3c", font=("Arial", 12, "bold"), command=self.delete_logic).pack(side="right", padx=5)

        # Treeview setup
        self.tree = ttk.Treeview(self.admin_tab, columns=("ID", "Name", "Category", "Price", "Stock"), show="headings")
        self.tree.heading("ID", text="Database ID")
        self.tree.heading("Name", text="Product Name")
        self.tree.heading("Category", text="Category")
        self.tree.heading("Price", text="Price ($)")
        self.tree.heading("Stock", text="Stock Level")
        
        self.tree.column("ID", width=200, anchor="center")
        self.tree.column("Name", width=250, anchor="w")
        self.tree.column("Category", width=150, anchor="center")
        self.tree.column("Price", width=120, anchor="center")
        self.tree.column("Stock", width=120, anchor="center")
        self.tree.pack(fill="both", expand=True, padx=20, pady=10)
        # Add inventory value display at the bottom
        self.update_inventory_value()

    def filter_by_category(self, choice):
        self.current_category_filter = choice if choice != "All" else "All"
        self.refresh_all()

    def update_treeview(self, catalog_data):
        if self.role != "admin": 
            return    
        self.tree.delete(*self.tree.get_children())
        
        for cat, items in catalog_data.items():
            for item in items:
                self.tree.insert(
                    "", "end", 
                    values=(
                        str(item["_id"]), 
                        item.get("name", "N/A"), 
                        cat.upper(),
                        f"{item.get('price', 0):.2f}", 
                        item.get("stock", 0)
                    )
                )

    def update_inventory_value(self):
        """Calculate and display total inventory value at the bottom of admin tab"""
        try:
            # Get all inventory collections
            all_collections = db.list_collection_names()
            excluded_tables = ["users", "ledger", "system.indexes"]
            inventory_categories = [col for col in all_collections if col not in excluded_tables]
            
            total_value = 0
            category_breakdown = {}
            
            # Calculate total value from all products
            for cat in inventory_categories:
                category_total = 0
                products = db[cat].find({})
                for product in products:
                    product_value = product.get('price', 0) * product.get('stock', 0)
                    category_total += product_value
                    total_value += product_value
                
                if category_total > 0:
                    category_breakdown[cat] = category_total
            
            # Check if value frame already exists
            if hasattr(self, 'value_frame') and self.value_frame.winfo_exists():
                # Update existing frame
                for widget in self.value_frame.winfo_children():
                    widget.destroy()
            else:
                # Create new frame at the bottom
                self.value_frame = ctk.CTkFrame(self.admin_tab, fg_color="#1a1a1a", corner_radius=10)
                self.value_frame.pack(fill="x", side="bottom", padx=20, pady=10)
            
            # Display total inventory value
            title_label = ctk.CTkLabel(
                self.value_frame, 
                text="INVENTORY VALUATION SUMMARY", 
                font=("Arial", 16, "bold"), 
                text_color="#2ecc71"
            )
            title_label.pack(pady=(10, 5))
            
            # Total value
            total_frame = ctk.CTkFrame(self.value_frame, fg_color="#2b2b2b", corner_radius=8)
            total_frame.pack(fill="x", padx=20, pady=5)
            
            ctk.CTkLabel(
                total_frame, 
                text="Total Inventory Value:", 
                font=("Arial", 14, "bold")
            ).pack(side="left", padx=20, pady=10)
            
            ctk.CTkLabel(
                total_frame, 
                text=f"${total_value:,.2f}", 
                font=("Arial", 18, "bold"), 
                text_color="#2ecc71"
            ).pack(side="right", padx=20, pady=10)
            
            # Category breakdown
            if category_breakdown:
                breakdown_frame = ctk.CTkFrame(self.value_frame, fg_color="#2b2b2b", corner_radius=8)
                breakdown_frame.pack(fill="x", padx=20, pady=5)
                
                ctk.CTkLabel(
                    breakdown_frame, 
                    text="Category Breakdown:", 
                    font=("Arial", 12, "bold")
                ).pack(anchor="w", padx=20, pady=(10, 5))
                
                # Create a grid for categories
                categories_frame = ctk.CTkFrame(breakdown_frame, fg_color="transparent")
                categories_frame.pack(fill="x", padx=20, pady=(0, 10))
                
                # Display up to 3 categories per row
                row_frame = None
                for i, (cat, value) in enumerate(category_breakdown.items()):
                    if i % 3 == 0:
                        row_frame = ctk.CTkFrame(categories_frame, fg_color="transparent")
                        row_frame.pack(fill="x", pady=2)
                    
                    cat_frame = ctk.CTkFrame(row_frame, fg_color="#1a1a1a", corner_radius=5)
                    cat_frame.pack(side="left", expand=True, fill="x", padx=5)
                    
                    ctk.CTkLabel(
                        cat_frame, 
                        text=f"{cat.upper()}:", 
                        font=("Arial", 11, "bold")
                    ).pack(side="left", padx=10, pady=5)
                    
                    ctk.CTkLabel(
                        cat_frame, 
                        text=f"${value:,.2f}", 
                        font=("Arial", 11), 
                        text_color="#f39c12"
                    ).pack(side="right", padx=10, pady=5)
            
            # Number of unique products
            products_frame = ctk.CTkFrame(self.value_frame, fg_color="#2b2b2b", corner_radius=8)
            products_frame.pack(fill="x", padx=20, pady=5)
            
            total_products = sum(db[cat].count_documents({}) for cat in inventory_categories)
            
            ctk.CTkLabel(
                products_frame, 
                text="Total Unique Products:", 
                font=("Arial", 12, "bold")
            ).pack(side="left", padx=20, pady=8)
            
            ctk.CTkLabel(
                products_frame, 
                text=str(total_products), 
                font=("Arial", 14, "bold"), 
                text_color="#3498db"
            ).pack(side="right", padx=20, pady=8)
            
        except Exception as e:
            print(f"Error calculating inventory value: {e}")
        
    # --- CRUD: CREATE ---
    def add_product_window(self):
        popup = ctk.CTkToplevel(self)
        popup.title("Create New Product Entry")
        popup.geometry("400x500")
        popup.attributes('-topmost', True)

        ctk.CTkLabel(popup, text="New Product Details", font=("Arial", 18, "bold")).pack(pady=15)
        name_ent = ctk.CTkEntry(popup, placeholder_text="Product Name", width=250)
        name_ent.pack(pady=10)
        
        cat_var = ctk.StringVar(value="electronics")
        ctk.CTkOptionMenu(popup, variable=cat_var, values=["electronics", "furniture", "clothing", "books", "sports"], width=250).pack(pady=10)
        
        price_ent = ctk.CTkEntry(popup, placeholder_text="Price ($)", width=250)
        price_ent.pack(pady=10)
        stock_ent = ctk.CTkEntry(popup, placeholder_text="Initial Stock Level", width=250)
        stock_ent.pack(pady=10)

        def save():
            name = name_ent.get().strip()
            cat = cat_var.get()
            try:
                price = float(price_ent.get())
                stock = int(stock_ent.get())
                if not name: 
                    raise ValueError("Name required.")
                
                # Auto generation using Groq
                desc = "Standard dynamic system stock unit item description."
                if groq_client:
                    try:
                        response = groq_client.chat.completions.create(
                            model="llama-3.1-8b-instant",
                            messages=[
                                {"role": "user", "content": f"Write a short sentence technical description for {name}."}
                            ],
                            max_tokens=100,
                            temperature=0.7
                        )
                        desc = response.choices[0].message.content
                    except Exception as e:
                        print(f"Groq API error: {e}")
                        desc = "Standard dynamic system stock unit item description."

                # Insert into database
                db[cat].insert_one({
                    "name": name, 
                    "price": price, 
                    "stock": stock, 
                    "description": desc,
                    "image": "https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=400"
                })
                popup.destroy()
                self.refresh_all()
                messagebox.showinfo("Success", f"Product '{name}' added successfully!")
                
            except ValueError as e:
                messagebox.showerror("Validation Error", f"Please input valid values:\n{e}", parent=popup)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to add product:\n{e}", parent=popup)

        ctk.CTkButton(popup, text="Commit to Cluster", fg_color="#2ecc71", text_color="black", command=save).pack(pady=20)
          
            # --- CRUD: UPDATE ---
    def open_edit_window(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Selection Required", "Select a product row from the table map to edit.")
            return
        
        values = self.tree.item(selected[0], "values")
        item_id_str, current_name, category, current_price, current_stock = values
        category = category.lower()

        popup = ctk.CTkToplevel(self)
        popup.title(f"Modify {current_name}")
        popup.geometry("400x350")
        popup.attributes('-topmost', True)

        ctk.CTkLabel(popup, text=f"Updating Profile: {current_name}", font=("Arial", 16, "bold")).pack(pady=15)
        
        price_entry = ctk.CTkEntry(popup, placeholder_text="New Price")
        price_entry.insert(0, current_price)
        price_entry.pack(pady=10)

        stock_entry = ctk.CTkEntry(popup, placeholder_text="Modify Stock")
        stock_entry.insert(0, current_stock)
        stock_entry.pack(pady=10)

        def save_changes():
            try:
                new_price = float(price_entry.get())
                new_stock = int(stock_entry.get())
                from bson import ObjectId
                
                db[category].update_one(
                    {"_id": ObjectId(item_id_str)},
                    {"$set": {"price": new_price, "stock": new_stock}}
                )
                popup.destroy()
                self.refresh_all()
                messagebox.showinfo("Success", "MongoDB cluster item state synchronized successfully.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to modify record payload: {e}", parent=popup)

        ctk.CTkButton(popup, text="Save Structural Changes", fg_color="#2ecc71", text_color="black", command=save_changes).pack(pady=25)

    # --- CRUD: DELETE ---
    def delete_logic(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Selection Required", "Select a target dataset row to delete.")
            return
        
        values = self.tree.item(selected[0], "values")
        item_id_str, name, category, _, _ = values
        
        if messagebox.askyesno("Confirm Purge", f"Permanently drop database record {name}?"):
            from bson import ObjectId
            db[category.lower()].delete_one({"_id": ObjectId(item_id_str)})
            self.refresh_all()

    # --- DYNAMIC MARKETPLACE VIEW WITH QUANTITY SELECTOR ---
    def render_marketplace(self, catalog_data):
        for widget in self.market_tab.winfo_children(): 
            widget.destroy()
        
        # Add category filter bar at top
        filter_frame = ctk.CTkFrame(self.market_tab, fg_color="transparent")
        filter_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(filter_frame, text="Filter by Category:", font=("Arial", 14, "bold")).pack(side="left", padx=10)
        
        categories = ["All"] + [cat for cat in catalog_data.keys()]
        category_filter = ctk.CTkOptionMenu(
            filter_frame, values=categories,
            command=self.filter_marketplace, width=200
        )
        category_filter.pack(side="left", padx=10)
        
        self.loaded_images_cache = {}
        
        scroll = ctk.CTkScrollableFrame(self.market_tab, fg_color="transparent")
        scroll.pack(fill="both", expand=True)
        scroll.grid_columnconfigure((0, 1, 2), weight=1)

        row, col = 0, 0
        
        for cat, items in catalog_data.items():
            for item in items:
                product_uid = str(item["_id"])

                card = ctk.CTkFrame(scroll, corner_radius=15, fg_color="#2b2b2b", border_width=1, border_color="#333")
                card.grid(row=row, column=col, padx=15, pady=15, sticky="nsew")

                img_label = ctk.CTkLabel(card, text="Fetching Asset...", width=260, height=160)
                img_label.pack(pady=10)
                
                img_url = item.get('image')
                if img_url:
                    threading.Thread(
                        target=self.load_image_async_with_cache, 
                        args=(img_url, img_label, product_uid), 
                        daemon=True
                    ).start()
                
                product_name = item.get('name', 'Unknown Stock').upper()
                product_price = item.get('price', 0.00)
                stock_count = item.get('stock', 0)
                
                ctk.CTkLabel(card, text=product_name, font=("Arial", 16, "bold")).pack(anchor="w", padx=20)
                ctk.CTkLabel(card, text=f"${product_price:.2f}", text_color="#2ecc71", font=("Arial", 18, "bold")).pack(anchor="w", padx=20)
                
                stock_color = "#e74c3c" if stock_count == 0 else "#f39c12" if stock_count < 5 else "#7f8c8d"
                ctk.CTkLabel(card, text=f"Stock Level: {stock_count} units", text_color=stock_color, font=("Arial", 11, "italic")).pack(anchor="w", padx=20, pady=(0, 5))

                # Quantity selector
                quantity_frame = ctk.CTkFrame(card, fg_color="transparent")
                quantity_frame.pack(fill="x", padx=20, pady=10)
                
                ctk.CTkLabel(quantity_frame, text="Qty:", font=("Arial", 12)).pack(side="left", padx=5)
                quantity_var = ctk.IntVar(value=1)
                quantity_spin = ctk.CTkEntry(quantity_frame, textvariable=quantity_var, width=60)
                quantity_spin.pack(side="left", padx=5)
                
                def increment(q_var=quantity_var, stock=stock_count):
                    if q_var.get() < stock:
                        q_var.set(q_var.get() + 1)
                
                def decrement(q_var=quantity_var):
                    if q_var.get() > 1:
                        q_var.set(q_var.get() - 1)
                
                ctk.CTkButton(quantity_frame, text="+", width=30, command=increment).pack(side="left", padx=2)
                ctk.CTkButton(quantity_frame, text="-", width=30, command=decrement).pack(side="left", padx=2)

                buy_btn_state = "normal" if stock_count > 0 else "disabled"
                
                ctk.CTkButton(
                    card, text="ADD TO CART", state=buy_btn_state,
                    fg_color="#2ecc71" if stock_count > 0 else "#444", 
                    text_color="black" if stock_count > 0 else "#888",
                    command=lambda i=item, c=cat, q=quantity_var: self.add_to_cart(i, c, q.get())
                ).pack(fill="x", padx=15, pady=5)
                
                col += 1
                if col > 2: 
                    col = 0
                    row += 1

    def filter_marketplace(self, choice):
        self.current_category_filter = choice if choice != "All" else "All"
        self.refresh_all()

    def add_to_cart(self, item, category, quantity):
        if quantity > item.get('stock', 0):
            messagebox.showerror("Error", f"Only {item.get('stock')} units available!")
            return
        
        self.cart.add_item(item['name'], category, quantity, item['price'])
        self.update_cart_button()
        messagebox.showinfo("Success", f"Added {quantity} x {item['name']} to cart!")

    def open_cart_window(self):
        if not self.cart.items:
            messagebox.showinfo("Cart Empty", "Your cart is empty!")
            return
        
        cart_window = ctk.CTkToplevel(self)
        cart_window.title("Shopping Cart")
        cart_window.geometry("600x500")
        cart_window.attributes('-topmost', True)
        
        # Cart items display
        scroll = ctk.CTkScrollableFrame(cart_window)
        scroll.pack(fill="both", expand=True, padx=20, pady=20)
        
        total = 0
        for idx, item in enumerate(self.cart.items):
            frame = ctk.CTkFrame(scroll)
            frame.pack(fill="x", pady=5)
            
            item_total = item['quantity'] * item['price']
            total += item_total
            
            ctk.CTkLabel(frame, text=f"{item['product']} - Qty: {item['quantity']} x ${item['price']:.2f} = ${item_total:.2f}", 
                        font=("Arial", 12)).pack(side="left", padx=10, pady=10)
            
            ctk.CTkButton(frame, text="Remove", fg_color="#e74c3c", width=80,
                         command=lambda i=idx: self.remove_from_cart(i, cart_window)).pack(side="right", padx=10)
        
        # Total and checkout
        total_label = ctk.CTkLabel(cart_window, text=f"Total: ${total:.2f}", font=("Arial", 18, "bold"), text_color="#2ecc71")
        total_label.pack(pady=10)
        
        button_frame = ctk.CTkFrame(cart_window, fg_color="transparent")
        button_frame.pack(pady=10)
        
        ctk.CTkButton(button_frame, text="Clear Cart", fg_color="#e74c3c", 
                     command=lambda: self.clear_cart(cart_window)).pack(side="left", padx=10)
        
        ctk.CTkButton(button_frame, text="Proceed to Payment", fg_color="#2ecc71", text_color="black",
                     command=lambda: self.process_mpesa_payment(cart_window)).pack(side="left", padx=10)

    def remove_from_cart(self, index, window):
        self.cart.remove_item(index)
        self.update_cart_button()
        window.destroy()
        self.open_cart_window()

    def clear_cart(self, window):
        self.cart.clear()
        self.update_cart_button()
        window.destroy()

    def process_mpesa_payment(self, cart_window):
        total = self.cart.get_total()
        
        # Payment popup
        payment_window = ctk.CTkToplevel(self)
        payment_window.title("M-Pesa Payment")
        payment_window.geometry("400x400")
        payment_window.attributes('-topmost', True)
        
        ctk.CTkLabel(payment_window, text="M-Pesa Payment", font=("Arial", 20, "bold")).pack(pady=20)
        ctk.CTkLabel(payment_window, text=f"Total Amount: KES {total:.2f}", font=("Arial", 16), text_color="#2ecc71").pack(pady=10)
        
        ctk.CTkLabel(payment_window, text="Enter M-Pesa Phone Number:", font=("Arial", 12)).pack(pady=10)
        phone_entry = ctk.CTkEntry(payment_window, placeholder_text="0712345678", width=250)
        phone_entry.pack(pady=10)
        
        def simulate_mpesa():
            phone = phone_entry.get().strip()
            if not phone or len(phone) < 10:
                messagebox.showerror("Error", "Please enter a valid phone number!", parent=payment_window)
                return
            
            # Simulate STK Push
            messagebox.showinfo("M-Pesa STK Push", f"Payment request sent to {phone}\nEnter PIN to complete transaction.", parent=payment_window)
            
            # Process actual payment and update inventory
            try:
                for item in self.cart.items:
                    # Update stock
                    db[item['category']].update_one(
                        {"name": item['product']},
                        {"$inc": {"stock": -item['quantity']}}
                    )
                    # Record transaction
                    db["ledger"].insert_one({
                        "user": self.username,
                        "item": item['product'],
                        "price": item['price'],
                        "quantity": item['quantity'],
                        "total": item['quantity'] * item['price'],
                        "cat": item['category'],
                        "status": "Paid via M-Pesa",
                        "phone": phone,
                        "timestamp": datetime.now()
                    })
                
                messagebox.showinfo("Success", f"Payment of KES {total:.2f} completed successfully!\nCheck your Transactions tab.", parent=payment_window)
                self.cart.clear()
                self.update_cart_button()
                payment_window.destroy()
                cart_window.destroy()
                self.refresh_all()
            except Exception as e:
                messagebox.showerror("Error", f"Payment processing failed: {e}", parent=payment_window)
        
        ctk.CTkButton(payment_window, text="Pay with M-Pesa", fg_color="#2ecc71", text_color="black", 
                     command=simulate_mpesa).pack(pady=20)
        
        ctk.CTkLabel(payment_window, text="Demo Mode: This simulates M-Pesa payment", font=("Arial", 10), text_color="gray").pack(pady=10)

    # --- UPGRADED ASYNC THREAD WORKER ---
    def load_image_async_with_cache(self, url, label, product_uid):
        try:
            res = requests.get(url, timeout=6, headers={'User-Agent': 'Mozilla/5.0'})
            if res.status_code == 200:
                p_img = Image.open(BytesIO(res.content))
                ctk_img = ctk.CTkImage(p_img, size=(240, 150))
                self.after(0, lambda: self.finalize_ui_image(label, ctk_img, product_uid))
        except Exception as e:
            self.after(0, lambda: label.configure(text="Image Offline"))

    def finalize_ui_image(self, label, ctk_img, product_uid):
        if not hasattr(self, "loaded_images_cache") or not isinstance(self.loaded_images_cache, dict):
            self.loaded_images_cache = {}
        self.loaded_images_cache[product_uid] = ctk_img
        try:
            if label.winfo_exists():
                label.configure(image=ctk_img, text="")
                label.image = ctk_img
        except Exception:
            pass
    
    # --- INTERACTIVE NATURAL LANGUAGE AI BOT LOOP (Enhanced with all categories)---
    def setup_ai_chat(self):
        self.chat_display = ctk.CTkTextbox(self.chat_tab, state="disabled", wrap="word")
        self.chat_display.pack(fill="both", expand=True, padx=20, pady=10)
        
        input_f = ctk.CTkFrame(self.chat_tab, fg_color="transparent")
        input_f.pack(fill="x", padx=20, pady=10)
        
        self.chat_input = ctk.CTkEntry(input_f, placeholder_text="Ask about products, get descriptions, or recommendations...")
        self.chat_input.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        ctk.CTkButton(input_f, text="Send Query", fg_color="#2ecc71", text_color="black", width=150, command=self.send_ai_query).pack(side="right")

    def send_ai_query(self):
        user_text = self.chat_input.get().strip()
        if not user_text: return
        
        self.update_chat(f"You: {user_text}\n")
        self.chat_input.delete(0, 'end')
        threading.Thread(target=self.get_ai_response, args=(user_text,), daemon=True).start()

    def get_ai_response(self, query):
        try:
            # Check if Groq client is available
            if not groq_client:
                self.after(0, lambda: self.update_chat("Nexus AI: Groq API key not configured. Please add GROQ_API_KEY to .env file\n\n"))
                return
            
            # Get ALL product categories dynamically
            all_collections = db.list_collection_names()
            excluded_tables = ["users", "ledger", "system.indexes"]
            inventory_categories = [col for col in all_collections if col not in excluded_tables]
            
            all_products = []
            for cat in inventory_categories:
                products = list(db[cat].find({}, {"_id": 0}))
                for p in products:
                    p['category'] = cat
                all_products.extend(products)
            
            # Simple keyword matching for context
            query_words = query.lower().split()
            targeted_context = []
            for p in all_products:
                if any(word in p['name'].lower() for word in query_words):
                    targeted_context.append(p)
            
            if not targeted_context:
                targeted_context = all_products[:15]

            # Create a compact context string
            context_str = json.dumps(targeted_context[:10], default=str)

            full_prompt = (
                f"You are Nexus AI Assistant for an inventory system. "
                f"Based on this inventory data: {context_str}, "
                f"answer: {query}. "
                f"Provide product descriptions, recommendations, and availability information. "
                f"Be helpful and concise."
            )
            
            # USE GROQ CLIENT - THIS IS THE FIX
            response = groq_client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": "You are a helpful AI assistant for an e-commerce inventory system."},
                    {"role": "user", "content": full_prompt}
                ],
                temperature=0.7,
                max_tokens=500
            )
            
            ai_response = response.choices[0].message.content
            self.after(0, lambda: self.update_chat(f"Nexus AI: {ai_response}\n\n"))
            
        except Exception as e:
            error_msg = str(e)
            self.after(0, lambda: self.update_chat(f"Error: {error_msg}\n\n"))
            print(f"AI Error details: {error_msg}")

    def update_chat(self, text):
        self.chat_display.configure(state="normal")
        self.chat_display.insert("end", text)
        self.chat_display.configure(state="disabled")
        self.chat_display.see("end")

    # --- LEDGER TRANSACTIONS ---
    def render_ledger(self, ledger_data):
        for widget in self.ledger_tab.winfo_children(): widget.destroy()
        
        scroll = ctk.CTkScrollableFrame(self.ledger_tab, fg_color="transparent")
        scroll.pack(fill="both", expand=True)
            
        for log in ledger_data:
            f = ctk.CTkFrame(scroll, fg_color="#222")
            f.pack(fill="x", pady=5, padx=20)
            
            quantity = log.get('quantity', 1)
            total = log.get('total', log['price'])
            
            ctk.CTkLabel(f, text=f"Buyer: {log['user']} | Item: {log['item']} (x{quantity}) | Total: ${total:.2f} | Status: {log['status']}", 
                        font=("Arial", 12)).pack(side="left", padx=20, pady=10)
            
            if log['status'] == "Paid via M-Pesa":
                ctk.CTkButton(f, text="Refund", fg_color="#e74c3c", width=100,
                            command=lambda l=log: self.process_refund(l)).pack(side="right", padx=10)

    def process_refund(self, log):
        if messagebox.askyesno("Process Return", f"Refund {log['item']}?"):
            db[log['cat']].update_one({"name": log['item']}, {"$inc": {"stock": log.get('quantity', 1)}})
            db["ledger"].update_one({"_id": log["_id"]}, {"$set": {"status": "Refunded"}})
            self.refresh_all()
            messagebox.showinfo("Success", "Refund processed successfully!")

def launch_main_app(role, username="User"):
    app = NexusApp(role, username)
    app.mainloop()

if __name__ == "__main__":
    login = LoginWindow(on_success=launch_main_app)
    login.mainloop()