import secrets
from shop.mail import send

def start_password_reset(email):
    token = secrets.token_urlsafe(32)
    send(email, f"Reset link: https://shop.example/reset?t={token}")
    return token
