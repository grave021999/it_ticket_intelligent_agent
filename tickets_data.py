from faker import Faker
from datetime import datetime, timedelta
import random
import uuid
import pandas as pd
import os
import glob

# Initialize Faker
fake = Faker()

# --- Ticket Metadata ---
CATEGORIES = ["Hardware", "Software", "Network", "Access", "Email"]
SUBCATEGORIES = {
    "Hardware": ["Laptop", "Printer", "Monitor", "Keyboard"],
    "Software": ["OS", "Application", "Patch", "Update"],
    "Network": ["WiFi", "VPN", "Router", "LAN"],
    "Access": ["Password", "Account Lock", "Permissions", "2FA"],
    "Email": ["Outlook", "Spam", "Delivery", "Quota"]
}
STATUSES = ["Open", "In Progress", "Resolved", "Closed"]
PRIORITIES = ["Low", "Medium", "High", "Critical"]


def generate_tickets(n=1000):
    """Generate n fake IT tickets."""
    tickets = []
    for _ in range(n):
        category = random.choice(CATEGORIES)
        subcategory = random.choice(SUBCATEGORIES[category])
        tickets.append({
            "ticket_id": f"TCK-{str(uuid.uuid4())[:8]}",
            "title": f"{category} issue - {fake.word()}",
            "description": fake.sentence(nb_words=12),
            "category": category,
            "subcategory": subcategory,
            "status": random.choice(STATUSES),
            "priority": random.choice(PRIORITIES),
            "created_by": fake.first_name(),
            "assigned_to": fake.first_name(),
            "created_date": (datetime.now() - timedelta(days=random.randint(0, 30))).isoformat()
        })
    return tickets


if __name__ == "__main__":
    df = pd.DataFrame(generate_tickets(1000))

    try:
        # Try saving to default file
        df.to_csv("dummy_it_tickets.csv", index=False)
        print("✅ 1000 dummy IT tickets generated and saved to dummy_it_tickets.csv")

    except PermissionError:
        # If file is locked, create a new one automatically
        alt_filename = f"dummy_it_tickets_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        df.to_csv(alt_filename, index=False)
        print(f"⚠️ 'dummy_it_tickets.csv' is currently in use. Saved as: {alt_filename}")

    # Optional: Automatically show the latest CSV file in the folder
    latest = sorted(glob.glob("dummy_it_tickets*.csv"), key=os.path.getmtime, reverse=True)[0]
    print(f"📁 Latest dataset available: {latest}")
