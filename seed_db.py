import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")

if not MONGO_URI:
    print("Critical Error: MONGO_URI environment variable is missing from your .env file!")
    exit(1)

# Configure a safe 5-second connection timeout so the script doesn't hang forever
try:
    print("Connecting to MongoDB Atlas Cluster...")
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    db = client["inventory_db"]
    # Force a connection test ping
    client.server_info()
    print("Successfully connected to MongoDB Atlas!")
except Exception as e:
    print(f"Network Connection Failed: {e}")
    print("\nTroubleshooting tips:")
    print("1. Check your internet connection.")
    print("2. Ensure your current IP is whitelisted in MongoDB Atlas under Network Access.")
    print("3. Try changing your system DNS to 8.8.8.8 (Google) or 1.1.1.1 (Cloudflare).")
    exit(1)

# Robust, professional product dataset (30 entries total)
ecommerce_data = {
    "electronics": [
        {"name": "Laptop Pro 16", "price": 1499.00, "stock": 8, "image": "https://images.unsplash.com/photo-1496181133206-80ce9b88a853?w=500"},
        {"name": "Wireless Anc Buds", "price": 179.99, "stock": 25, "image": "https://images.unsplash.com/photo-1590658268037-6bf12165a8df?w=500"},
        {"name": "Smart Fitness Watch", "price": 249.50, "stock": 14, "image": "https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=500"},
        {"name": "Mechanical Pro Keyboard", "price": 135.00, "stock": 11, "image": "https://images.unsplash.com/photo-1511467687858-23d96c32e4ae?w=500"},
        {"name": "UltraWide 4K Monitor", "price": 520.00, "stock": 6, "image": "https://images.unsplash.com/photo-1527443224154-c4a3942d3acf?w=500"},
        {"name": "Ergonomic Gaming Mouse", "price": 79.99, "stock": 40, "image": "https://images.unsplash.com/photo-1615663245857-ac93bb7c39e7?w=500"},
        {"name": "Noise Cancelling Headset", "price": 329.00, "stock": 9, "image": "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=500"},
        {"name": "External 2TB SSD", "price": 159.00, "stock": 18, "image": "https://images.unsplash.com/photo-1601524909162-be87252be298?w=500"},
        {"name": "HD Streaming Webcam", "price": 89.50, "stock": 22, "image": "https://images.unsplash.com/photo-1603162591427-0fa83c316719?w=500"},
        {"name": "Smart Home Speaker", "price": 119.00, "stock": 30, "image": "https://images.unsplash.com/photo-1543512214-318c7553f230?w=500"},
        {"name": "Graphic Drawing Tablet", "price": 199.99, "stock": 7, "image": "https://images.unsplash.com/photo-1522199755839-a2bacb67c546?w=500"},
        {"name": "Dual-Band Wi-Fi 6 Router", "price": 145.00, "stock": 12, "image": "https://images.unsplash.com/photo-1610471930099-87c50999e4b3?w=500"},
        {"name": "Portable Power Bank", "price": 49.99, "stock": 50, "image": "https://images.unsplash.com/photo-1609592424109-dd9892f1b177?w=500"},
        {"name": "4K DSLR Camera Studio", "price": 1150.00, "stock": 4, "image": "https://images.unsplash.com/photo-1516035069371-29a1b244cc32?w=500"},
        {"name": "USB-C Multi-Port Hub", "price": 39.99, "stock": 35, "image": "https://images.unsplash.com/photo-1468495244123-6c6c332eeece?w=500"}
    ],
    "furniture": [
        {"name": "Ergonomic Mesh Chair", "price": 289.00, "stock": 12, "image": "https://images.unsplash.com/photo-1505797149-43b0ad766207?w=500"},
        {"name": "Premium Oak Desk", "price": 499.00, "stock": 5, "image": "https://images.unsplash.com/photo-1518455027359-f3f8164ba6bd?w=500"},
        {"name": "Dual-Motor Standing Desk", "price": 680.00, "stock": 4, "image": "https://images.unsplash.com/photo-1595515106969-1ce29566ff1c?w=500"},
        {"name": "Mid-Century Velvet Sofa", "price": 1150.00, "stock": 3, "image": "https://images.unsplash.com/photo-1555041469-a586c61ea9bc?w=500"},
        {"name": "Minimalist Bookshelf", "price": 185.00, "stock": 20, "image": "https://images.unsplash.com/photo-1594620302200-9a762244a156?w=500"},
        {"name": "Leather Lounge Chair", "price": 420.00, "stock": 6, "image": "https://images.unsplash.com/photo-1567538096630-e0c55bd6374c?w=500"},
        {"name": "Bedside Nightstand Table", "price": 95.00, "stock": 16, "image": "https://images.unsplash.com/photo-1532372320978-9b4d6a3a854c?w=500"},
        {"name": "Modern Dining Table", "price": 599.00, "stock": 5, "image": "https://images.unsplash.com/photo-1577140917170-285929fb55b7?w=500"},
        {"name": "Fabric Ottoman Stool", "price": 65.00, "stock": 25, "image": "https://images.unsplash.com/photo-1592078615290-033ee584e267?w=500"},
        {"name": "Industrial Floor Lamp", "price": 110.00, "stock": 14, "image": "https://images.unsplash.com/photo-1507473885765-e6ed057f782c?w=500"},
        {"name": "6-Drawer Dresser Chest", "price": 340.00, "stock": 8, "image": "https://images.unsplash.com/photo-1595428774223-ef52624120d2?w=500"},
        {"name": "Wooden Coffee Table", "price": 145.00, "stock": 10, "image": "https://images.unsplash.com/photo-1533090161767-e6ffed986c88?w=500"},
        {"name": "Tufted Queen Headboard", "price": 275.00, "stock": 7, "image": "https://images.unsplash.com/photo-1540518614846-7eded433c457?w=500"},
        {"name": "Floating Wall Shelves", "price": 45.00, "stock": 30, "image": "https://images.unsplash.com/photo-1616486338812-3dadae4b4ace?w=500"},
        {"name": "Ergonomic Footrest", "price": 35.00, "stock": 45, "image": "https://images.unsplash.com/photo-1581428982868-e410dd047a90?w=500"}
    ],
        "clothing": [
        {"name": "Premium Cotton T-Shirt", "price": 29.99, "stock": 50, "image": "https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?w=500"},
        {"name": "Slim Fit Jeans", "price": 79.99, "stock": 35, "image": "https://images.unsplash.com/photo-1541099649105-f69ad21f3246?w=500"},
        {"name": "Leather Jacket", "price": 199.99, "stock": 12, "image": "https://images.unsplash.com/photo-1551028719-00167b16eac5?w=500"},
        {"name": "Running Sneakers", "price": 89.99, "stock": 28, "image": "https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=500"},
        {"name": "Wool Winter Coat", "price": 159.99, "stock": 15, "image": "https://images.unsplash.com/photo-1539533113208-f6df8cc8b543?w=500"},
        {"name": "Formal Dress Shirt", "price": 49.99, "stock": 42, "image": "https://images.unsplash.com/photo-1596755094514-f87e34085b2c?w=500"},
        {"name": "Yoga Leggings", "price": 39.99, "stock": 60, "image": "https://images.unsplash.com/photo-1506629082955-511b1aa562c8?w=500"},
        {"name": "Wool Beanie", "price": 19.99, "stock": 75, "image": "https://images.unsplash.com/photo-1576871337632-b9aef4c17ab9?w=500"},
        {"name": "Leather Belt", "price": 34.99, "stock": 55, "image": "https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=500"},
        {"name": "Cashmere Scarf", "price": 59.99, "stock": 30, "image": "https://images.unsplash.com/photo-1520903928029-232bdb5b8b8f?w=500"}
    ],
    "books": [
        {"name": "The Midnight Library", "price": 24.99, "stock": 45, "image": "https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?w=500"},
        {"name": "Atomic Habits", "price": 19.99, "stock": 62, "image": "https://images.unsplash.com/photo-1589998059171-988d887df646?w=500"},
        {"name": "Dune Messiah", "price": 22.99, "stock": 38, "image": "https://images.unsplash.com/photo-1532012197267-da84d127e765?w=500"},
        {"name": "Project Hail Mary", "price": 27.99, "stock": 41, "image": "https://images.unsplash.com/photo-1621351183012-e2f9972dd9bf?w=500"},
        {"name": "The Psychology of Money", "price": 18.99, "stock": 53, "image": "https://images.unsplash.com/photo-1589829085413-56de8ae18c73?w=500"},
        {"name": "It Ends With Us", "price": 16.99, "stock": 47, "image": "https://images.unsplash.com/photo-1544947950-fa07a98d237f?w=500"},
        {"name": "The Silent Patient", "price": 21.99, "stock": 44, "image": "https://images.unsplash.com/photo-1543002588-bfa74002ed7e?w=500"},
        {"name": "Becoming", "price": 29.99, "stock": 32, "image": "https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?w=500"},
        {"name": "The Four Agreements", "price": 14.99, "stock": 68, "image": "https://images.unsplash.com/photo-1544947950-fa07a98d237f?w=500"},
        {"name": "Where the Crawdads Sing", "price": 23.99, "stock": 39, "image": "https://images.unsplash.com/photo-1621351183012-e2f9972dd9bf?w=500"}
    ],
    "sports": [
        {"name": "Professional Soccer Ball", "price": 49.99, "stock": 25, "image": "https://images.unsplash.com/photo-1575361203039-a4b63a5b6eae?w=500"},
        {"name": "Carbon Fiber Tennis Racket", "price": 189.99, "stock": 18, "image": "https://images.unsplash.com/photo-1589998059171-988d887df646?w=500"},
        {"name": "Yoga Mat Premium", "price": 34.99, "stock": 42, "image": "https://images.unsplash.com/photo-1592432678016-e910b452f9a2?w=500"},
        {"name": "Adjustable Dumbbell Set", "price": 299.99, "stock": 12, "image": "https://images.unsplash.com/photo-1581009146145-b5ef050c2e1e?w=500"},
        {"name": "Basketball", "price": 39.99, "stock": 35, "image": "https://images.unsplash.com/photo-1519861531473-9200262188bf?w=500"},
        {"name": "Resistance Bands Set", "price": 29.99, "stock": 55, "image": "https://images.unsplash.com/photo-1598266663439-2056e6900339?w=500"},
        {"name": "Cycling Helmet", "price": 79.99, "stock": 22, "image": "https://images.unsplash.com/photo-1532298229144-0ec0c57515c7?w=500"},
        {"name": "Fitness Tracker Watch", "price": 129.99, "stock": 31, "image": "https://images.unsplash.com/photo-1575311373937-040b8e1fd5b6?w=500"},
        {"name": "Punching Bag", "price": 89.99, "stock": 15, "image": "https://images.unsplash.com/photo-1552074284-5e88ef1aef18?w=500"},
        {"name": "Ski Goggles", "price": 59.99, "stock": 28, "image": "https://images.unsplash.com/photo-1531834685032-c34bf0d84c1f?w=500"}
    ]
}

def seed():
    print("\nStarting inventory drop and purge sequence...")
    for cat, items in ecommerce_data.items():
        col = db[cat]
        # Purge existing stale documents
        col.delete_many({})
        # Bulk load clean curated listings
        col.insert_many(items)
        print(f" Loaded {len(items)} items into the '{cat}' collection map.")
    
    print("\nStructural DB Update complete! The application frontend is ready to pull data.")

if __name__ == "__main__":
    seed()