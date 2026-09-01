import os
import razorpay
from dotenv import load_dotenv

load_dotenv()

RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET")

client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))

def create_payment_link(amount_inr: float, reference_id: str, description: str, customer_details: dict = None):
    """
    Creates a Razorpay Payment Link.
    IMPORTANT: Converts INR to paise internally.
    """
    # Convert INR to paise (smallest unit)
    amount_paise = int(amount_inr * 100)
    
    data = {
        "amount": amount_paise,
        "currency": "INR",
        "accept_partial": False,
        "description": description,
        "reference_id": reference_id,
        "notify": {
            "sms": False,
            "email": False
        },
        "reminder_enable": False,
        "callback_url": "http://localhost:3000/chat",
        "callback_method": "get"
    }
    
    if customer_details:
        data["customer"] = customer_details

    try:
        response = client.payment_link.create(data)
        return {
            "success": True,
            "payment_link_id": response.get("id"),
            "payment_link_url": response.get("short_url"),
            "status": response.get("status")
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

def get_payment_link_status(payment_link_id: str):
    """Fetches the status of a payment link."""
    try:
        response = client.payment_link.fetch(payment_link_id)
        return {
            "success": True,
            "status": response.get("status"), # e.g. "created", "paid", "cancelled"
            "payment_id": response.get("payment_id") # populated if paid
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
