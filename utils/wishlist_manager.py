# wishlist_manager.py
import json, os

WISHLIST_PATH = "wishlist.json"

def load_wishlist(username=None):
    if not os.path.exists(WISHLIST_PATH):
        return []

    with open(WISHLIST_PATH, "r") as f:
        data = json.load(f)

    if username:
        return data.get(username, [])

    return data

def save_wishlist(data):
    with open(WISHLIST_PATH, "w") as f:
        json.dump(data, f, indent=2)

def add_to_wishlist(product, username):
    data = load_wishlist()

    if username not in data:
        data[username] = []

    if not any(p["link"] == product["link"] for p in data[username]):
        data[username].append(product)

    save_wishlist(data)

def remove_from_wishlist(link, username):
    data = load_wishlist()

    if username in data:
        data[username] = [
            p for p in data[username]
            if p["link"] != link
        ]

    save_wishlist(data)