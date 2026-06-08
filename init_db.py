from flask import Flask
from models import db, MenuItem, User, CafeLocation
from werkzeug.security import generate_password_hash

def seed_database():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///cafe.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db.init_app(app)
    
    with app.app_context():
        # Create all tables
        db.create_all()
        print("Database tables created successfully.")
        
        # Check if an admin user already exists
        admin_user = User.query.filter_by(username='admin').first()
        if not admin_user:
            hashed_pw = generate_password_hash('adminpassword')
            new_admin = User(
                username='admin',
                email='admin@kushwahacafe.com',
                password_hash=hashed_pw,
                role='admin'
            )
            db.session.add(new_admin)
            print("Admin user created (Username: admin, Password: adminpassword).")
        else:
            print("Admin user already exists.")
            
        # Check if menu items exist
        if MenuItem.query.count() == 0:
            initial_items = [
                # Hot Drinks
                MenuItem(
                    name="Classic Espresso",
                    description="Rich and bold double shot of our house espresso blend.",
                    price=90.00,
                    category="Hot Drinks",
                    image_url="https://images.unsplash.com/photo-1514432324607-a09d9b4aefdd?q=80&w=300&auto=format&fit=crop"
                ),
                MenuItem(
                    name="Cappuccino Premium",
                    description="Espresso balanced with steamed milk and a thick layer of creamy foam, dusted with cocoa.",
                    price=140.00,
                    category="Hot Drinks",
                    image_url="https://images.unsplash.com/photo-1572442388796-11668a67e53d?q=80&w=300&auto=format&fit=crop"
                ),
                MenuItem(
                    name="Vanilla Cafe Latte",
                    description="Double shot of espresso, steamed milk, and sweet Madagascar vanilla syrup.",
                    price=160.00,
                    category="Hot Drinks",
                    image_url="https://images.unsplash.com/photo-1541167760496-1628856ab772?q=80&w=300&auto=format&fit=crop"
                ),
                MenuItem(
                    name="Masala Chai Tea",
                    description="Traditional Indian black tea brewed with fresh ginger, cardamom, cloves, and milk.",
                    price=80.00,
                    category="Hot Drinks",
                    image_url="https://images.unsplash.com/photo-1576092768241-dec231879fc3?q=80&w=300&auto=format&fit=crop"
                ),
                # Cold Drinks
                MenuItem(
                    name="Iced Caramel Macchiato",
                    description="Chilled milk marked with espresso, sweetened with vanilla syrup and topped with buttery caramel drizzle.",
                    price=180.00,
                    category="Cold Drinks",
                    image_url="https://images.unsplash.com/photo-1461023058943-07fcbe16d735?q=80&w=300&auto=format&fit=crop"
                ),
                MenuItem(
                    name="Hazelnut Frappe",
                    description="Blended coffee ice drink flavored with roasted hazelnut syrup, finished with whipped cream.",
                    price=190.00,
                    category="Cold Drinks",
                    image_url="https://images.unsplash.com/photo-1572490122747-3968b75cc699?q=80&w=300&auto=format&fit=crop"
                ),
                MenuItem(
                    name="Mint Mojito Cooler",
                    description="A refreshing non-alcoholic blend of fresh mint leaves, lime wedges, sugar, and sparkling water.",
                    price=120.00,
                    category="Cold Drinks",
                    image_url="https://images.unsplash.com/photo-1513558161293-cdaf765ed2fd?q=80&w=300&auto=format&fit=crop"
                ),
                # Snacks
                MenuItem(
                    name="Cheese Garlic Bread",
                    description="Four slices of toasted baguette topped with house garlic butter, mozzarella, and herbs.",
                    price=130.00,
                    category="Snacks",
                    image_url="https://images.unsplash.com/photo-1573140247632-f8fd74997d5c?q=80&w=300&auto=format&fit=crop"
                ),
                MenuItem(
                    name="Paneer Tikka Sandwich",
                    description="Spiced paneer cubes, capsicum, and onions in a creamy mint chutney spread, grilled in wheat bread.",
                    price=150.00,
                    category="Snacks",
                    image_url="https://images.unsplash.com/photo-1528735602780-2552fd46c7af?q=80&w=300&auto=format&fit=crop"
                ),
                # Desserts
                MenuItem(
                    name="Fudge Brownie with Ice Cream",
                    description="Warm, gooey double chocolate brownie served with a scoop of premium vanilla bean ice cream.",
                    price=170.00,
                    category="Desserts",
                    image_url="https://images.unsplash.com/photo-1606313564200-e75d5e30476c?q=80&w=300&auto=format&fit=crop"
                ),
                MenuItem(
                    name="Red Velvet Cheesecake Slice",
                    description="A slice of creamy baked cheesecake on a rich cocoa red velvet cake crust.",
                    price=210.00,
                    category="Desserts",
                    image_url="https://images.unsplash.com/photo-1533134242443-d4fd215305ad?q=80&w=300&auto=format&fit=crop"
                )
            ]
            for item in initial_items:
                db.session.add(item)
            print("Initial menu items seeded.")
        else:
            print("Menu items already seeded.")
            
        # Check if locations exist
        if CafeLocation.query.count() == 0:
            initial_locations = [
                CafeLocation(
                    name="Kushwaha Cafe - Sector 62 Branch",
                    address="Sector-62, Noida, Uttar Pradesh, India",
                    map_url="https://maps.app.goo.gl/wJ59s4tYnQ6xU39A7",
                    phone="+91 98765 43210"
                ),
                CafeLocation(
                    name="Kushwaha Cafe - Gorakhpur Branch",
                    address="Near Station Road, Gorakhpur, Uttar Pradesh, India",
                    map_url="https://maps.app.goo.gl/B9U7P3PZ6yXmF39A8",
                    phone="+91 74084 33563"
                )
            ]
            for loc in initial_locations:
                db.session.add(loc)
            print("Initial cafe locations seeded.")
        else:
            print("Cafe locations already seeded.")
            
        db.session.commit()
        print("Database seeded and closed successfully!")

if __name__ == '__main__':
    seed_database()
