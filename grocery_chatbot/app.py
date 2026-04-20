from flask import Flask, request, jsonify, render_template

app = Flask(__name__)

# Grocery product data
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

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    user_message = request.json.get("message", "").lower()

    # Show all products
    if "show products" in user_message or "products" in user_message:
        response = "Available products:<br>"
        for item, details in grocery_items.items():
            response += f"{item.title()} - ₹{details['price']} (Stock: {details['stock']})<br>"
        return jsonify({"reply": response})

    # Add multiple common items at once
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
        found = False
        for item in grocery_items:
            if item in user_message:
                cart[item] = cart.get(item, 0) + 1
                reply = f"{item.title()} added to cart. Price: ₹{grocery_items[item]['price']}"
                found = True
                return jsonify({"reply": reply})
        if not found:
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
            return jsonify({"reply": "Your cart is empty. Add some items first."})
        total = 0
        for item, qty in cart.items():
            total += grocery_items[item]["price"] * qty
        return jsonify({"reply": f"Order placed successfully!<br>Your total is ₹{total}<br>Delivery will arrive soon."})

    # Order tracking
    elif "track order" in user_message:
        return jsonify({"reply": "Your order is out for delivery and will arrive by 6 PM."})

    # FAQ
    elif "faq" in user_message or "delivery charge" in user_message:
        faq_text = """
        FAQs:<br>
        1. Delivery charge is ₹40.<br>
        2. Free delivery above ₹500.<br>
        3. Same-day delivery is available.<br>
        4. Payment methods: UPI, Card, Cash on Delivery.<br>
        """
        return jsonify({"reply": faq_text})

    # Offers
    elif "offers" in user_message:
        return jsonify({"reply": "Today's offers:<br>10% off on fruits<br>Buy 2 breads get 1 free<br>₹50 off above ₹999"})

    # Help
    else:
        help_text = """
        I can help you with:<br>
        - show products<br>
        - add milk<br>
        - add bread<br>
        - add eggs<br>
        - add milk bread eggs<br>
        - cart<br>
        - checkout<br>
        - track order<br>
        - faq<br>
        - offers
        """
        return jsonify({"reply": help_text})

if __name__ == "__main__":
    app.run(debug=True)