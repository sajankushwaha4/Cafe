from flask import Flask
from models import db, MenuItem

def update_images():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///cafe.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db.init_app(app)
    
    with app.app_context():
        # Update Spicy Paneer Burger
        burger = MenuItem.query.filter_by(name="Spicy Paneer Burger").first()
        if burger:
            burger.image_url = "/static/images/spicy_paneer_burger.png"
            print("Updated Spicy Paneer Burger image URL.")
            
        # Update Classic Margherita Pizza
        pizza = MenuItem.query.filter_by(name="Classic Margherita Pizza").first()
        if pizza:
            pizza.image_url = "/static/images/margherita_pizza.png"
            print("Updated Classic Margherita Pizza image URL.")
            
        # Update Cappuccino Premium
        cappuccino = MenuItem.query.filter_by(name="Cappuccino Premium").first()
        if cappuccino:
            cappuccino.image_url = "/static/images/cappuccino.png"
            print("Updated Cappuccino Premium image URL.")
            
        db.session.commit()
        print("Database image URLs updated successfully!")

if __name__ == '__main__':
    update_images()
