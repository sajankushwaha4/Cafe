from flask import Flask
from models import db, MenuItem

def add_pizza_burger():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///cafe.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db.init_app(app)
    
    with app.app_context():
        new_items = [
            # Pizza Category
            MenuItem(
                name="Classic Margherita Pizza",
                description="Classic Italian pizza topped with fresh tomato sauce, mozzarella cheese, and fragrant basil leaves.",
                price=190.00,
                category="Pizza",
                image_url="https://images.unsplash.com/photo-1604068549290-dea0e4a305ca?q=80&w=300&auto=format&fit=crop"
            ),
            MenuItem(
                name="Double Cheese Margherita",
                description="Loaded with a double layer of premium liquid cheese and mozzarella on a golden crust.",
                price=240.00,
                category="Pizza",
                image_url="https://images.unsplash.com/photo-1593560708920-61dd98c46a4e?q=80&w=300&auto=format&fit=crop"
            ),
            MenuItem(
                name="Paneer Tikka Pizza",
                description="Tandoori-spiced paneer cubes, capsicum, sliced onions, and green chilies on a spicy marinara base.",
                price=270.00,
                category="Pizza",
                image_url="https://images.unsplash.com/photo-1513104890138-7c749659a591?q=80&w=300&auto=format&fit=crop"
            ),
            MenuItem(
                name="Veggie Supreme Pizza",
                description="A rich mix of black olives, sweet corn, bell peppers, button mushrooms, and red onions with fresh herbs.",
                price=290.00,
                category="Pizza",
                image_url="https://images.unsplash.com/photo-1571407970349-bc81e7e96d47?q=80&w=300&auto=format&fit=crop"
            ),
            # Burger Category
            MenuItem(
                name="Classic Veggie Burger",
                description="Crispy mixed vegetable patty served with lettuce, sliced tomatoes, creamy mayo, and toasted sesame buns.",
                price=110.00,
                category="Burger",
                image_url="https://images.unsplash.com/photo-1550547660-d9450f859349?q=80&w=300&auto=format&fit=crop"
            ),
            MenuItem(
                name="Spicy Paneer Burger",
                description="A thick block of golden-fried paneer patty, jalapeños, lettuce, and spicy chipotle sauce.",
                price=150.00,
                category="Burger",
                image_url="https://images.unsplash.com/photo-1456418047667-56bec35b12a3?q=80&w=300&auto=format&fit=crop"
            ),
            MenuItem(
                name="Cheese Burst Veg Burger",
                description="Crispy potato patty stuffed with liquid cheese, topped with sliced onions and mustard relish.",
                price=170.00,
                category="Burger",
                image_url="https://images.unsplash.com/photo-1568901346375-23c9450c58cd?q=80&w=300&auto=format&fit=crop"
            ),
            MenuItem(
                name="Double Decker Premium Burger",
                description="Double vegetable patties, double slice of cheddar cheese, caramelized onions, and house special sauce.",
                price=210.00,
                category="Burger",
                image_url="https://images.unsplash.com/photo-1586190848861-99aa4a171e90?q=80&w=300&auto=format&fit=crop"
            )
        ]
        
        added_count = 0
        for item in new_items:
            # Check if item with this name already exists
            existing = MenuItem.query.filter_by(name=item.name).first()
            if not existing:
                db.session.add(item)
                added_count += 1
                
        db.session.commit()
        print(f"Success: Added {added_count} new Pizza and Burger items to database.")

if __name__ == '__main__':
    add_pizza_burger()
