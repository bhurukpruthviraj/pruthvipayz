import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
PRODUCTS_FILE = ROOT / "data" / "products.json"


def get_catalog():
    with open(PRODUCTS_FILE, "r", encoding="utf-8") as file:
        products = json.load(file)

    return {
        "merchant": {
            "id": "merchant_demo",
            "name": "Demo Merchant",
            "currency": "INR",
            "agentic_commerce_enabled": True
        },
        "products": [
            {
                **product,
                "available": product["stock"] > 0,
                "agent_purchase_allowed": True
            }
            for product in products
        ]
    }
