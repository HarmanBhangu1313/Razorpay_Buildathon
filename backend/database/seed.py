import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add the backend dir to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.models import Base, Product
from dotenv import load_dotenv

load_dotenv()

from database.db import SessionLocal, engine

def seed_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    
    # Check if already seeded
    if db.query(Product).count() > 0:
        print("Database already seeded.")
        db.close()
        return

    products = [
        Product(
            id="AERO-14",
            name="AeroBook 14",
            description="Ultra-lightweight laptop perfect for students and professionals. Features a stunning 14-inch display, 16GB RAM, and 512GB SSD.",
            category="Laptop",
            price=64999.0,
            stock=50,
            features=["14-inch display", "16GB RAM", "512GB SSD", "10h battery life", "Ultra-lightweight"],
            related_products=["SLEEVE-14", "MOUSE-WL"]
        ),
        Product(
            id="PROBOOK-16",
            name="ProBook 16 Max",
            description="High-performance laptop for creators and developers. 16-inch 4K display, 32GB RAM, 1TB SSD, dedicated GPU.",
            category="Laptop",
            price=124999.0,
            stock=20,
            features=["16-inch 4K display", "32GB RAM", "1TB SSD", "Dedicated GPU", "High performance"],
            related_products=["SLEEVE-16", "HUB-USBC"]
        ),
        Product(
            id="SLEEVE-14",
            name="Premium Leather Sleeve 14\"",
            description="Elegant and protective leather sleeve tailored for 14-inch laptops.",
            category="Accessories",
            price=799.0,
            stock=100,
            features=["Genuine leather", "Water-resistant", "Snug fit"],
            related_products=["AERO-14"]
        ),
        Product(
            id="SLEEVE-16",
            name="Premium Leather Sleeve 16\"",
            description="Elegant and protective leather sleeve tailored for 16-inch laptops.",
            category="Accessories",
            price=899.0,
            stock=80,
            features=["Genuine leather", "Water-resistant", "Snug fit"],
            related_products=["PROBOOK-16"]
        ),
        Product(
            id="MOUSE-WL",
            name="Ergonomic Wireless Mouse",
            description="Comfortable wireless mouse with silent clicks and adjustable DPI.",
            category="Accessories",
            price=1499.0,
            stock=150,
            features=["Ergonomic design", "Silent clicks", "Adjustable DPI", "Bluetooth 5.0"],
            related_products=[]
        ),
        Product(
            id="AUDIO-PRO",
            name="SonicPro X2 Wireless Headphones",
            description="Premium over-ear noise-cancelling headphones with 40-hour battery life.",
            category="Audio",
            price=4799.0,
            stock=60,
            features=["Active Noise Cancelling", "40-hour battery", "Over-ear comfort", "Hi-Res Audio"],
            related_products=["CASE-AUDIO"]
        ),
        Product(
            id="CASE-AUDIO",
            name="Hard Carrying Case for Headphones",
            description="Durable travel case for SonicPro X2 and similar sized headphones.",
            category="Accessories",
            price=499.0,
            stock=200,
            features=["Hard shell", "Soft interior", "Travel-friendly"],
            related_products=["AUDIO-PRO"]
        ),
        Product(
            id="PHONE-Z1",
            name="Zephyr Z1 Smartphone",
            description="Flagship smartphone with an amazing camera and all-day battery.",
            category="Smartphone",
            price=45999.0,
            stock=40,
            features=["6.7-inch OLED", "128GB Storage", "Triple camera setup", "5G ready"],
            related_products=["CASE-Z1", "CHARGER-FAST"]
        ),
        Product(
            id="CASE-Z1",
            name="Zephyr Z1 Clear Case",
            description="Anti-yellowing clear case to protect your phone without hiding its design.",
            category="Accessories",
            price=299.0,
            stock=300,
            features=["Anti-yellowing", "Shock absorbent", "Slim fit"],
            related_products=["PHONE-Z1"]
        ),
        Product(
            id="CHARGER-FAST",
            name="65W GaN Fast Charger",
            description="Ultra-compact 65W charger suitable for phones, tablets, and laptops.",
            category="Accessories",
            price=1999.0,
            stock=120,
            features=["65W Output", "GaN Technology", "2 USB-C ports", "1 USB-A port"],
            related_products=["PHONE-Z1", "AERO-14", "PROBOOK-16"]
        )
    ]
    
    db.add_all(products)
    db.commit()
    print("Database seeded with electronics products.")
    db.close()

if __name__ == "__main__":
    seed_db()
