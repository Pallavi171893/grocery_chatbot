
from flask import Flask, render_template, request, jsonify, session
import re

app = Flask(__name__)
app.secret_key = "freshcart-demo-secret-change-this"

PRODUCTS = {
    "Rice": 60,
    "Wheat Flour": 45,
    "Sugar": 45,
    "Milk": 30,
    "Bread": 40,
    "Eggs": 7,
    "Apples": 180,
    "Bananas": 60,
    "Tomatoes": 40,
    "Potatoes": 35,
    "Onions": 40,
    "Cooking Oil": 150,
    "Coffee": 120,
    "Biscuits": 30,
    "Cheese": 100
}


def get_cart():
    return session.setdefault("cart", {})


def get_bill():
    cart = get_cart()
    items = []
    subtotal = 0

    for name, quantity in cart.items():
        if name in PRODUCTS and quantity > 0:
            price = PRODUCTS[name]
            item_total = price * quantity
            subtotal += item_total

            items.append({
                "name": name,
                "quantity": quantity,
                "price": price,
                "total": item_total
            })

    coupon = session.get("coupon", "")
    discount = subtotal * 0.10 if (
        coupon == "FRESH10" and subtotal >= 200
    ) else 0

    delivery = 0 if subtotal == 0 or subtotal >= 500 else 30
    total = subtotal - discount + delivery

    return {
        "items": items,
        "subtotal": round(subtotal, 2),
        "discount": round(discount, 2),
        "delivery": round(delivery, 2),
        "total": round(total, 2),
        "coupon": coupon
    }


def find_product(text):
    text = text.lower().strip()

    # Match longer product names first.
    for name in sorted(PRODUCTS, key=len, reverse=True):
        if name.lower() in text:
            return name

    # Support singular/plural variations.
    aliases = {
        "egg": "Eggs",
        "apple": "Apples",
        "banana": "Bananas",
        "tomato": "Tomatoes",
        "potato": "Potatoes",
        "onion": "Onions",
        "biscuit": "Biscuits"
    }

    for alias, name in aliases.items():
        if re.search(r"\b" + re.escape(alias) + r"\b", text):
            return name

    return None


def product_list():
    return "\n".join(
        f"{name}: ₹{price} per unit"
        for name, price in PRODUCTS.items()
    )


def bill_text():
    bill = get_bill()

    if not bill["items"]:
        return "Your cart is empty. Add groceries first."

    lines = ["Your FreshCart Bill"]

    for item in bill["items"]:
        lines.append(
            f"{item['name']} x {item['quantity']} = "
            f"₹{item['total']:.2f}"
        )

    lines.extend([
        f"Subtotal: ₹{bill['subtotal']:.2f}",
        f"Discount: ₹{bill['discount']:.2f}",
        f"Delivery: ₹{bill['delivery']:.2f}",
        f"FINAL TOTAL: ₹{bill['total']:.2f}"
    ])

    return "\n".join(lines)


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/api/products")
def products():
    return jsonify([
        {"name": name, "price": price}
        for name, price in PRODUCTS.items()
    ])


@app.route("/api/cart")
def cart_details():
    return jsonify(get_bill())


@app.route("/api/coupon", methods=["POST"])
def apply_coupon():
    data = request.get_json(silent=True) or {}
    code = str(data.get("coupon", "")).strip().upper()

    if code != "FRESH10":
        return jsonify({
            "reply": "Invalid coupon. Try FRESH10.",
            "bill": get_bill()
        }), 400

    session["coupon"] = "FRESH10"
    bill = get_bill()

    if bill["subtotal"] < 200:
        reply = "FRESH10 applied! Your subtotal must reach ₹200 to get 10% off."
    else:
        reply = f"Coupon applied! You saved ₹{bill['discount']:.2f}."

    return jsonify({"reply": reply, "bill": bill})


@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json(silent=True) or {}
    message = str(data.get("message", "")).strip()
    text = message.lower()

    if not message:
        return jsonify({"reply": "Please type a grocery command.",
                        "bill": get_bill()})

    # Greetings
    if text in ["hi", "hello", "hey", "good morning", "good evening"]:
        reply = (
            "Hello! Welcome to FreshCart AI!\n"
            "Try 'show products', 'add eggs', 'my cart', "
            "or 'calculate my bill'."
        )

    # Show products
    elif any(word in text for word in [
        "show products", "list products", "list groceries",
        "available groceries", "show groceries", "product list"
    ]) or text == "list":
        reply = "Available groceries:\n" + product_list()

    # Coupon and discount
    elif "discount" in text or "coupon" in text:
        bill = get_bill()
        reply = (
            "Use coupon FRESH10 to get 10% off when your "
            "subtotal is ₹200 or more.\n"
            "Delivery is free on orders of ₹500 or more.\n"
            f"Your current subtotal is ₹{bill['subtotal']:.2f}.\n"
            "Enter FRESH10 in the coupon box and click Apply."
        )

    # Clear cart
    elif any(phrase in text for phrase in [
        "clear cart", "empty cart", "remove all", "clear my cart"
    ]):
        session["cart"] = {}
        reply = "Your cart has been cleared."

    # Remove an item
    elif text.startswith(("remove ", "delete ", "take out ")):
        name = find_product(text)

        if not name:
            reply = "Please mention a valid product to remove."
        else:
            cart = get_cart()
            if name in cart:
                cart.pop(name)
                session["cart"] = cart
                reply = f"{name} removed from your cart."
            else:
                reply = f"{name} is not in your cart."

    # Add items, e.g. "add eggs" or "add 2 milk"
    elif text.startswith(("add ", "buy ", "i want ", "get ")):
        name = find_product(text)

        if not name:
            reply = "I couldn't find that product. Type 'show products'."
        else:
            match = re.search(r"\b(\d+)\b", text)
            quantity = int(match.group(1)) if match else 1

            if quantity < 1 or quantity > 100:
                reply = "Please choose a quantity between 1 and 100."
            else:
                cart = get_cart()
                cart[name] = cart.get(name, 0) + quantity
                session["cart"] = cart
                reply = (
                    f"Adding {quantity} {name} at "
                    f"₹{PRODUCTS[name]} each.\n"
                    f"{name} added successfully!"
                )

    # Price query
    elif "price" in text or "cost" in text:
        name = find_product(text)
        if name:
            reply = f"{name} costs ₹{PRODUCTS[name]} per unit."
        else:
            reply = "Please mention a product, such as 'price of rice'."

    # Cart and bill
    elif any(word in text for word in [
        "my cart", "show cart", "calculate my bill",
        "calculate bill", "my bill", "total", "checkout",
        "place order", "confirm order", "order now"
    ]):
        bill = get_bill()

        if not bill["items"]:
            reply = "Your cart is empty. Add groceries before checkout."
        elif any(word in text for word in [
            "place order", "confirm order", "order now", "checkout"
        ]):
            reply = (
                "Order summary:\n" + bill_text() +
                "\n\nThis is a demo. No payment has been taken "
                "and no order has been saved."
            )
        else:
            reply = "🧾 " + bill_text()

    else:
        reply = (
            "I'm FreshCart AI, your grocery assistant!\n"
            "Try these commands:\n"
            "• add eggs\n"
            "• add 2 milk\n"
            "• remove eggs\n"
            "• show products\n"
            "• price of rice\n"
            "• calculate my bill\n"
            "• show discount\n"
            "• place order"
        )

    return jsonify({"reply": reply, "bill": get_bill()})


if __name__ == "__main__":
    app.run(debug=True)
