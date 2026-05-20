# Smart Inventory Manager 

A Python-based Desktop application designed to manage electronics inventory with integrated AI capabilities.

##  Features
- **CRUD Operations**: Add, View, and Delete electronics products.
- **AI-Powered Catalog**: Automatically generates technical descriptions for products using llama AI model.
- **Intelligent Assistant**: A built-in chatbot that can answer questions about stock levels, pricing, and product specs by "scraping" the MongoDB data.
- **Cloud Database**: Fully integrated with MongoDB Atlas for real-time data persistence.

##  Tech Stack
- **Language**: Python 3.12
- **GUI**: Tkinter
- **Database**: MongoDB Atlas (PyMongo)
- **AI Model**: llama-3.1-8b-instant
- **Environment**: Dotenv for secure API key management

##  Installation
1. Clone the repository.
2. Install dependencies:
   ```bash
   pip install groq