from flask import Flask, request, jsonify, render_template
import smtplib
from email.mime.text import MIMEText

app = Flask(__name__)

# =========================================================
# REPLACE THESE 3 VALUES WITH YOUR REAL DETAILS
# =========================================================
OWNER_EMAIL = "pallaviks1718@gmail.com"              # your email where order notifications will come
GMAIL_SEND_FROM = "pallaviks1718@gmail.com"          # same Gmail can be used here
GMAIL_APP_PASSWORD = "dbxd oxph qeqh zjdp"    # Gmail App Password from Google
# =========================================================

grocery_items = {
    "milk": {"price": 30, "stock": 10},
    "bread": {"price": 40, "stock": 15},
    "eggs": {"price": 55, "stock": 20},
    "rice": {"price": 70, "stock": 25},
    "apple": {"price": 120, "stock": 18},
    "banana": {"price": 45, "stock": 30},
    "tomato": {"price": 35, "stock": 22}
}

cart = {}

user_state = {
    "awaiting_order_type": False,
    "awaiting_address": False,
    "awaiting_contact": False,
    "order_type": "",
    "address": "",
    "contact": ""
}

def calculate_total():
    total = 0
    for item, qty in cart.items():
        total += grocery_items[item]["price"] * qty
    return total

def cart_items_text():
    text = ""
    for item, qty in cart.items():
        text += f"{item.title()} x {qty}\n"
    return text

def send_order_email():
    try:
        delivery_charge = 40 if user_state["order_type"] == "delivery" else 0
        total = calculate_total() + delivery_charge

        body = f"""
New Grocery Order Received

Order Type: {user_state['order_type'].title()}
Contact Number: {user_state['contact']}
Address: {user_state['address'] if user_state['address'] else 'Pickup from store'}

Items Ordered:
{cart_items_text()}

Delivery Charge: ₹{delivery_charge}
Total Amount: ₹{total}
"""

        msg = MIMEText(body)
        msg["Subject"] = "New Grocery Order Received"
        msg["From"] = GMAIL_SEND_FROM
        msg["To"] = OWNER_EMAIL

        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(GMAIL_SEND_FROM, GMAIL_APP_PASSWORD)
        server.sendmail(GMAIL_SEND_FROM, OWNER_EMAIL, msg.as_string())
        server.quit()

        return True
    except Exception as e:
        print("Email sending failed:", e)
        return False

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    original_message = request.json.get("message", "").strip()
    user_message = original_message.lower()

    # Step 1: Waiting for delivery/pickup choice
    if user_state["awaiting_order_type"]:
        if user_message == "1" or "delivery" in user_message:
            user_state["order_type"] = "delivery"
            user_state["awaiting_order_type"] = False
            user_state["awaiting_address"] = True
            return jsonify({"reply": "Delivery charge is ₹40.<br>Please enter your full delivery address."})

        elif user_message == "2" or "pickup" in user_message:
            user_state["order_type"] = "pickup"
            user_state["awaiting_order_type"] = False
            user_state["awaiting_contact"] = True
            return jsonify({"reply": "Please enter your contact number for pickup confirmation."})

        else:
            return jsonify({"reply": "Please choose:<br>1. Delivery<br>2. Pickup"})

    # Step 2: Waiting for address
    if user_state["awaiting_address"]:
        user_state["address"] = original_message
        user_state["awaiting_address"] = False
        user_state["awaiting_contact"] = True
        return jsonify({"reply": "Please enter your contact number."})

    # Step 3: Waiting for contact number
    if user_state["awaiting_contact"]:
        user_state["contact"] = original_message
        user_state["awaiting_contact"] = False

        email_sent = send_order_email()
        delivery_charge = 40 if user_state["order_type"] == "delivery" else 0
        total = calculate_total() + delivery_charge

        if user_state["order_type"] == "delivery":
            reply = f"""
Your order is placed successfully!<br>
Order Type: Delivery<br>
Delivery Charge: ₹40<br>
Total Amount: ₹{total}<br>
Address: {user_state['address']}<br>
Contact Number: {user_state['contact']}<br>
Your order will be delivered soon.
"""
        else:
            reply = f"""
Your order is placed successfully!<br>
Order Type: Pickup<br>
Total Amount: ₹{total}<br>
Contact Number: {user_state['contact']}<br>
Please collect your order from the store.
"""

        if email_sent:
            reply += "<br>Shop owner has been notified by email."
        else:
            reply += "<br>Order placed, but email notification failed."

        return jsonify({"reply": reply})

    # Show products
    if "show products" in user_message or user_message == "products":
        response = "Available products:<br>"
        for item, details in grocery_items.items():
            response += f"{item.title()} - ₹{details['price']} (Stock: {details['stock']})<br>"
        return jsonify({"reply": response})

    # Add multiple common items
    elif "add milk bread eggs" in user_message or "add milk, bread, eggs" in user_message:
        total = 0
        added_items = []
        for item in ["milk", "bread", "eggs"]:
            if grocery_items[item]["stock"] > 0:
                cart[item] = cart.get(item, 0) + 1
                total += grocery_items[item]["price"]
                added_items.append(f"{item.title()} - ₹{grocery_items[item]['price']}")
        response = "Added to cart:<br>" + "<br>".join(added_items)
        response += f"<br><b>Total: ₹{total}</b>"
        return jsonify({"reply": response})

    # Add single item
    elif "add" in user_message:
        for item in grocery_items:
            if item in user_message:
                cart[item] = cart.get(item, 0) + 1
                return jsonify({"reply": f"{item.title()} added to cart. Price: ₹{grocery_items[item]['price']}"})
        return jsonify({"reply": "Item not found. Try: milk, bread, eggs, rice, apple, banana, tomato"})

    # View cart
    elif "cart" in user_message:
        if not cart:
            return jsonify({"reply": "Your cart is empty."})
        total = 0
        response = "Your cart:<br>"
        for item, qty in cart.items():
            subtotal = grocery_items[item]["price"] * qty
            total += subtotal
            response += f"{item.title()} x {qty} = ₹{subtotal}<br>"
        response += f"<b>Total = ₹{total}</b>"
        return jsonify({"reply": response})

    # Checkout
    elif "checkout" in user_message:
        if not cart:
            return jsonify({"reply": "Your cart is empty. Add items first."})
        user_state["awaiting_order_type"] = True
        return jsonify({"reply": "Do you want:<br>1. Delivery<br>2. Pickup"})

    # FAQ
    elif "faq" in user_message:
        return jsonify({"reply": """
FAQs:<br>
1. Delivery charge is ₹40.<br>
2. Free delivery above ₹500.<br>
3. Same-day delivery is available.<br>
4. Payment methods: UPI, Card, Cash on Delivery.
"""})

    # Offers
    elif "offers" in user_message:
        return jsonify({"reply": "Today's offers:<br>10% off on fruits<br>Buy 2 breads get 1 free<br>₹50 off above ₹999"})

    # Track order
    elif "track order" in user_message:
        return jsonify({"reply": "Your order is being processed."})

    else:
        return jsonify({"reply": """
I can help you with:<br>
- show products<br>
- add milk<br>
- add bread<br>
- add eggs<br>
- add milk bread eggs<br>
- cart<br>
- checkout<br>
- faq<br>
- offers<br>
- track order
"""})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)