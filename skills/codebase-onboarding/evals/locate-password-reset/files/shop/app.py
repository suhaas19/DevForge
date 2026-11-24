from flask import Flask
from shop.routes.orders import bp as orders_bp
from shop.auth.routes import bp as auth_bp

def create_app():
    app = Flask(__name__)
    app.register_blueprint(orders_bp, url_prefix="/orders")
    app.register_blueprint(auth_bp, url_prefix="/auth")
    return app

if __name__ == "__main__":
    create_app().run()
