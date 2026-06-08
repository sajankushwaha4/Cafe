from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from models import db, User, MenuItem, Reservation, Order, CafeLocation
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os
import smtplib
import json
import uuid
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import socket

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'kushwaha-cafe-secret-key-12345')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///cafe.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# Helper function to send email notification
def send_email_notification(recipient_email, subject, body_html):
    smtp_email = os.environ.get('SMTP_EMAIL')
    # Can also be set in code directly or read from a config file
    smtp_password = os.environ.get('SMTP_PASSWORD')
    
    if smtp_email and smtp_password:
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = smtp_email
            msg['To'] = recipient_email
            
            part = MIMEText(body_html, 'html')
            msg.attach(part)
            
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(smtp_email, smtp_password)
            server.sendmail(smtp_email, recipient_email, msg.as_string())
            server.quit()
            print(f"[SMTP SUCCESS] Real email sent to {recipient_email}")
            return True
        except Exception as e:
            print(f"[SMTP ERROR] Failed to send real email: {e}")
            # Fallback to simulation
            
    # Email Simulation Log in Terminal
    print("\n" + "="*30 + " EMAIL SIMULATION " + "="*30)
    print(f"Recipient: {recipient_email}")
    print(f"Subject:   {subject}")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-"*78)
    print(body_html)
    print("="*78 + "\n")
    return True

# Context processor to make user status available in all templates
@app.context_processor
def inject_user():
    return {
        'logged_in': 'user_id' in session,
        'username': session.get('username'),
        'user_role': session.get('role'),
        'user_email': session.get('email')
    }

@app.context_processor
def inject_locations():
    return {
        'cafe_locations': CafeLocation.query.all()
    }

# ----------------- HOME & MENU ROUTES -----------------

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/menu')
def menu():
    categories = ['Hot Drinks', 'Cold Drinks', 'Snacks', 'Pizza', 'Burger', 'Desserts']
    # Fetch menu items group by category
    items_by_category = {}
    for cat in categories:
        items_by_category[cat] = MenuItem.query.filter_by(category=cat, is_available=True).all()
    return render_template('menu.html', items_by_category=items_by_category)

# ----------------- AUTHENTICATION ROUTES -----------------

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'register':
            username = request.form.get('username').strip()
            email = request.form.get('email').strip().lower()
            password = request.form.get('password')
            
            # Simple validation
            if not username or not email or not password:
                flash('Please fill in all fields.', 'error')
                return redirect(url_for('login'))
                
            existing_user = User.query.filter((User.username == username) | (User.email == email)).first()
            if existing_user:
                flash('Username or Email already exists.', 'error')
                return redirect(url_for('login'))
                
            hashed_pw = generate_password_hash(password)
            new_user = User(username=username, email=email, password_hash=hashed_pw, role='customer')
            
            db.session.add(new_user)
            db.session.commit()
            
            # Send welcome email
            welcome_html = f"""
            <h3>Welcome to Kushwaha Cafe, {username}!</h3>
            <p>Thank you for registering an account with us.</p>
            <p>You can now book tables, order delicious coffee and bakery items, and view your orders from your profile.</p>
            <br>
            <p>Warm Regards,</p>
            <p><b>Kushwaha Cafe Team</b></p>
            """
            send_email_notification(email, "Welcome to Kushwaha Cafe!", welcome_html)
            
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
            
        elif action == 'login':
            username_or_email = request.form.get('username_or_email').strip()
            password = request.form.get('password')
            
            user = User.query.filter((User.username == username_or_email) | (User.email == username_or_email.lower())).first()
            if user and check_password_hash(user.password_hash, password):
                session['user_id'] = user.id
                session['username'] = user.username
                session['email'] = user.email
                session['role'] = user.role
                
                flash(f'Welcome back, {user.username}!', 'success')
                if user.role == 'admin':
                    return redirect(url_for('admin_dashboard'))
                return redirect(url_for('index'))
            else:
                flash('Invalid credentials. Please try again.', 'error')
                return redirect(url_for('login'))
                
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully.', 'success')
    return redirect(url_for('index'))

# ----------------- CUSTOMER PROFILE -----------------

@app.route('/profile')
def profile():
    if 'user_id' not in session:
        flash('Please login to view your profile.', 'error')
        return redirect(url_for('login'))
        
    release_expired_reservations()
        
    user_id = session['user_id']
    user = db.session.get(User, user_id)
    
    user_reservations = Reservation.query.filter_by(user_id=user_id).order_by(Reservation.created_at.desc()).all()
    user_orders = Order.query.filter_by(user_id=user_id).order_by(Order.created_at.desc()).all()
    
    # Decode JSON items for easier rendering
    orders_data = []
    for order in user_orders:
        try:
            items_list = json.loads(order.items)
        except:
            items_list = []
        orders_data.append({
            'order': order,
            'items_list': items_list
        })
        
    return render_template('profile.html', user=user, reservations=user_reservations, orders_data=orders_data)

def release_expired_reservations():
    now = datetime.now()
    current_date_str = now.strftime('%Y-%m-%d')
    current_time_str = now.strftime('%H:%M')
    
    active_res = Reservation.query.filter_by(status='Active').all()
    updated_count = 0
    
    for res in active_res:
        try:
            # Check if date has passed or if it is today and time has passed slot_out
            if res.date < current_date_str or (res.date == current_date_str and current_time_str >= res.slot_out):
                res.status = 'Released'
                updated_count += 1
        except Exception as e:
            print(f"[AUTO-RELEASE ERROR] Failed to process reservation {res.id}: {e}")
            
    if updated_count > 0:
        db.session.commit()
        print(f"[AUTO-RELEASE] Automatically released {updated_count} expired table slots.")

# ----------------- TABLE RESERVATION -----------------

@app.route('/reserve', methods=['GET', 'POST'])
def reserve():
    if 'user_id' not in session:
        flash('Please login or register to book a table.', 'error')
        return redirect(url_for('login'))
        
    release_expired_reservations()
        
    if request.method == 'POST':
        name = request.form.get('name').strip()
        email = request.form.get('email').strip().lower()
        phone = request.form.get('phone').strip()
        date = request.form.get('date')
        slot_in = request.form.get('slot_in')
        slot_out = request.form.get('slot_out')
        guests = request.form.get('guests')
        special_requests = request.form.get('special_requests').strip()
        
        if not name or not email or not phone or not date or not slot_in or not slot_out or not guests:
            flash('All fields are required.', 'error')
            return redirect(url_for('reserve'))
            
        if slot_in >= slot_out:
            flash('Slot Out time must be after Slot In time.', 'error')
            return redirect(url_for('reserve'))
            
        new_res = Reservation(
            user_id=session['user_id'],
            name=name,
            email=email,
            phone=phone,
            date=date,
            slot_in=slot_in,
            slot_out=slot_out,
            status='Active',
            guests=int(guests),
            special_requests=special_requests
        )
        
        db.session.add(new_res)
        db.session.commit()
        
        # Email Notification
        email_html = f"""
        <div style="font-family: Arial, sans-serif; border: 1px solid #e2e8f0; padding: 20px; border-radius: 8px; max-width: 600px; background-color: #FCF8F2;">
            <h2 style="color: #2A1A10; border-bottom: 2px solid #D4AF37; padding-bottom: 10px;">Kushwaha Cafe Table Booking Confirmation</h2>
            <p>Dear <b>{name}</b>,</p>
            <p>Your table booking request has been successfully confirmed. Below are your reservation details:</p>
            <table style="width: 100%; border-collapse: collapse; margin: 15px 0;">
                <tr style="background-color: #f7fafc;"><td style="padding: 8px; font-weight: bold; border: 1px solid #e2e8f0;">Reservation ID</td><td style="padding: 8px; border: 1px solid #e2e8f0;">KC-RES-{new_res.id}</td></tr>
                <tr><td style="padding: 8px; font-weight: bold; border: 1px solid #e2e8f0;">Date</td><td style="padding: 8px; border: 1px solid #e2e8f0;">{date}</td></tr>
                <tr style="background-color: #f7fafc;"><td style="padding: 8px; font-weight: bold; border: 1px solid #e2e8f0;">Slot In Time</td><td style="padding: 8px; border: 1px solid #e2e8f0;">{slot_in}</td></tr>
                <tr><td style="padding: 8px; font-weight: bold; border: 1px solid #e2e8f0;">Slot Out Time</td><td style="padding: 8px; border: 1px solid #e2e8f0;">{slot_out}</td></tr>
                <tr style="background-color: #f7fafc;"><td style="padding: 8px; font-weight: bold; border: 1px solid #e2e8f0;">Number of Guests</td><td style="padding: 8px; border: 1px solid #e2e8f0;">{guests} Persons</td></tr>
                <tr><td style="padding: 8px; font-weight: bold; border: 1px solid #e2e8f0;">Contact Phone</td><td style="padding: 8px; border: 1px solid #e2e8f0;">{phone}</td></tr>
            </table>
            {f'<p><b>Special Note:</b> {special_requests}</p>' if special_requests else ''}
            <p>If you need to make changes or cancel, please log in to your profile or contact us directly.</p>
            <p>We look forward to serving you!</p>
            <br>
            <p>Warm Regards,</p>
            <p><b>Kushwaha Cafe Team</b></p>
        </div>
        """
        send_email_notification(email, f"Table Booking Confirmed - Kushwaha Cafe (ID: KC-RES-{new_res.id})", email_html)
        
        flash('Table reservation confirmed! Check your email for details.', 'success')
        return redirect(url_for('profile'))
        
    return render_template('reserve.html')

# ----------------- ORDER & PAYMENT FLOW -----------------

@app.route('/api/orders/create', methods=['POST'])
def create_order():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Please login to checkout.'}), 401
        
    data = request.get_json()
    if not data or 'cart' not in data or 'customer_name' not in data or 'customer_phone' not in data:
        return jsonify({'success': False, 'message': 'Invalid order data.'}), 400
        
    customer_name = data.get('customer_name').strip()
    customer_phone = data.get('customer_phone').strip()
    cart_items = data.get('cart')  # List of objects: {id, name, price, quantity}
    
    if not cart_items:
        return jsonify({'success': False, 'message': 'Your cart is empty.'}), 400
        
    # Recalculate total amount from DB to prevent client-side manipulation
    total = 0.0
    verified_items = []
    
    for item in cart_items:
        db_item = db.session.get(MenuItem, item['id'])
        if not db_item or not db_item.is_available:
            return jsonify({'success': False, 'message': f"Item '{item['name']}' is not available."}), 400
        qty = int(item['quantity'])
        item_total = db_item.price * qty
        total += item_total
        verified_items.append({
            'id': db_item.id,
            'name': db_item.name,
            'price': db_item.price,
            'quantity': qty,
            'total': item_total
        })
        
    # GST / Tax calculations could go here, let's keep total_amount as subtotal and show GST on UI or include it
    new_order = Order(
        user_id=session['user_id'],
        customer_name=customer_name,
        customer_phone=customer_phone,
        items=json.dumps(verified_items),
        total_amount=total,
        payment_status='Pending',
        order_status='Pending'
    )
    
    db.session.add(new_order)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'order_id': new_order.id,
        'total_amount': total
    })

@app.route('/checkout')
def checkout():
    if 'user_id' not in session:
        flash('Please login to continue checkout.', 'error')
        return redirect(url_for('login'))
        
    order_id = request.args.get('order_id')
    if not order_id:
        return redirect(url_for('menu'))
        
    order = db.session.get(Order, int(order_id))
    if not order or order.user_id != session['user_id']:
        flash('Order not found.', 'error')
        return redirect(url_for('menu'))
        
    if order.payment_status == 'Paid':
        return redirect(url_for('bill', order_id=order.id))
        
    # Generate REAL UPI payment link for exact total amount
    payee_upi = "7408433563@upi"
    payee_name = "Kushwaha Cafe"
    upi_string = f"upi://pay?pa={payee_upi}&pn={payee_name.replace(' ', '%20')}&am={order.total_amount}&cu=INR"
    
    return render_template('checkout.html', order=order, upi_string=upi_string, payee_upi=payee_upi)

@app.route('/api/orders/pay/<int:order_id>', methods=['POST'])
def pay_order(order_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
        
    order = db.session.get(Order, order_id)
    if not order or order.user_id != session['user_id']:
        return jsonify({'success': False, 'message': 'Order not found'}), 404
        
    if order.payment_status == 'Paid':
        return jsonify({'success': True, 'message': 'Already Paid', 'order_id': order.id})
        
    # Read UTR number from payload
    data = request.get_json() or {}
    utr_number = data.get('utr_number', '').strip()
    
    if not utr_number or len(utr_number) != 12 or not utr_number.isdigit():
        return jsonify({'success': False, 'message': 'Please enter a valid 12-digit UPI Ref/UTR number.'}), 400
        
    # Update payment to Paid
    order.payment_status = 'Paid'
    order.order_status = 'Preparing'
    order.transaction_id = utr_number
    db.session.commit()
    
    # Send Email invoice to customer
    user = db.session.get(User, session['user_id'])
    items_list = json.loads(order.items)
    
    items_rows = ""
    for it in items_list:
        items_rows += f"""
        <tr>
            <td style="padding: 8px; border: 1px solid #e2e8f0;">{it['name']}</td>
            <td style="padding: 8px; border: 1px solid #e2e8f0; text-align: center;">{it['quantity']}</td>
            <td style="padding: 8px; border: 1px solid #e2e8f0; text-align: right;">INR {it['price']:.2f}</td>
            <td style="padding: 8px; border: 1px solid #e2e8f0; text-align: right;">INR {it['total']:.2f}</td>
        </tr>
        """
        
    email_html = f"""
    <div style="font-family: Arial, sans-serif; border: 1px solid #e2e8f0; padding: 20px; border-radius: 8px; max-width: 600px; background-color: #FCF8F2;">
        <h2 style="color: #2A1A10; border-bottom: 2px solid #D4AF37; padding-bottom: 10px; text-align: center;">Kushwaha Cafe - Order Bill Receipt</h2>
        <p>Dear <b>{order.customer_name}</b>,</p>
        <p>Thank you for your order! We have successfully received your payment. Here is your digital receipt:</p>
        
        <table style="width: 100%; border-collapse: collapse; margin-bottom: 15px;">
            <tr><td><b>Order ID:</b> KC-ORD-{order.id}</td><td style="text-align: right;"><b>Date:</b> {datetime.now().strftime('%Y-%m-%d %H:%M')}</td></tr>
            <tr><td><b>Transaction ID:</b> {order.transaction_id}</td><td style="text-align: right;"><b>Status:</b> PAID</td></tr>
        </table>
        
        <table style="width: 100%; border-collapse: collapse; margin: 15px 0;">
            <thead>
                <tr style="background-color: #2A1A10; color: white;">
                    <th style="padding: 8px; text-align: left;">Item</th>
                    <th style="padding: 8px; text-align: center;">Qty</th>
                    <th style="padding: 8px; text-align: right;">Price</th>
                    <th style="padding: 8px; text-align: right;">Total</th>
                </tr>
            </thead>
            <tbody>
                {items_rows}
                <tr style="background-color: #f7fafc; font-weight: bold;">
                    <td colspan="3" style="padding: 8px; text-align: right; border: 1px solid #e2e8f0;">Grand Total</td>
                    <td style="padding: 8px; text-align: right; border: 1px solid #e2e8f0;">INR {order.total_amount:.2f}</td>
                </tr>
            </tbody>
        </table>
        
        <p style="text-align: center; font-style: italic; margin-top: 25px; color: #555;">We are now preparing your delicious food. Visited again soon!</p>
        <br>
        <p>Warm Regards,</p>
        <p><b>Kushwaha Cafe Team</b></p>
    </div>
    """
    send_email_notification(user.email, f"Invoice: Order KC-ORD-{order.id} Paid successfully!", email_html)
    
    # Send Email notification to owner (Admin)
    owner_email_html = f"""
    <div style="font-family: Arial, sans-serif; border: 1px solid #e2e8f0; padding: 20px; border-radius: 8px; max-width: 600px; background-color: #FCF8F2;">
        <h2 style="color: #2A1A10; border-bottom: 2px solid #D4AF37; padding-bottom: 10px; text-align: center;">Kushwaha Cafe - New Order Alert!</h2>
        <p>Hello <b>Owner/Admin</b>,</p>
        <p>A new order has been paid and received. Please start preparation:</p>
        
        <table style="width: 100%; border-collapse: collapse; margin-bottom: 15px;">
            <tr><td><b>Order ID:</b> KC-ORD-{order.id}</td><td style="text-align: right;"><b>Date:</b> {datetime.now().strftime('%Y-%m-%d %H:%M')}</td></tr>
            <tr><td><b>Customer Name:</b> {order.customer_name}</td><td style="text-align: right;"><b>Phone:</b> {order.customer_phone}</td></tr>
            <tr><td><b>Transaction ID:</b> {order.transaction_id}</td><td style="text-align: right;"><b>Status:</b> PAID</td></tr>
        </table>
        
        <table style="width: 100%; border-collapse: collapse; margin: 15px 0;">
            <thead>
                <tr style="background-color: #2A1A10; color: white;">
                    <th style="padding: 8px; text-align: left;">Item</th>
                    <th style="padding: 8px; text-align: center;">Qty</th>
                    <th style="padding: 8px; text-align: right;">Price</th>
                    <th style="padding: 8px; text-align: right;">Total</th>
                </tr>
            </thead>
            <tbody>
                {items_rows}
                <tr style="background-color: #f7fafc; font-weight: bold;">
                    <td colspan="3" style="padding: 8px; text-align: right; border: 1px solid #e2e8f0;">Grand Total</td>
                    <td style="padding: 8px; text-align: right; border: 1px solid #e2e8f0;">INR {order.total_amount:.2f}</td>
                </tr>
            </tbody>
        </table>
        <p>Go to your <a href="http://127.0.0.1:5000/admin">Admin Dashboard</a> to update status.</p>
    </div>
    """
    send_email_notification("admin@kushwahacafe.com", f"[NEW ORDER ALERT] Order KC-ORD-{order.id} Paid!", owner_email_html)
    
    # Visual console alert for the owner
    print("\n" + "#"*30 + " OWNER ALERTS " + "#"*30)
    print(f"NEW PAID ORDER RECEIVED: Order ID KC-ORD-{order.id}")
    print(f"Customer Name: {order.customer_name} | Phone: {order.customer_phone}")
    print(f"Total Amount:  INR {order.total_amount:.2f} | Txn ID: {order.transaction_id}")
    print("#"*74 + "\n")
    
    return jsonify({
        'success': True,
        'message': 'Payment confirmed!',
        'order_id': order.id
    })

@app.route('/bill/<int:order_id>')
def bill(order_id):
    if 'user_id' not in session:
        flash('Please login to view bills.', 'error')
        return redirect(url_for('login'))
        
    order = db.session.get(Order, order_id)
    if not order or (order.user_id != session['user_id'] and session.get('role') != 'admin'):
        flash('Bill not found.', 'error')
        return redirect(url_for('menu'))
        
    try:
        items_list = json.loads(order.items)
    except:
        items_list = []
        
    # Calculate simulated taxes (5% GST)
    subtotal = order.total_amount / 1.05
    gst = order.total_amount - subtotal
    
    return render_template('bill.html', order=order, items=items_list, subtotal=subtotal, gst=gst)

# ----------------- ADMIN DASHBOARD ROUTES -----------------

@app.route('/admin')
def admin_dashboard():
    if 'user_id' not in session or session.get('role') != 'admin':
        flash('Unauthorized. Admins only.', 'error')
        return redirect(url_for('login'))
        
    release_expired_reservations()
        
    # Statistics
    total_sales = db.session.query(db.func.sum(Order.total_amount)).filter_by(payment_status='Paid').scalar() or 0.0
    total_bookings = Reservation.query.count()
    total_orders = Order.query.filter_by(payment_status='Paid').count()
    
    reservations = Reservation.query.order_by(Reservation.created_at.desc()).all()
    orders = Order.query.order_by(Order.created_at.desc()).all()
    menu_items = MenuItem.query.all()
    
    # Parse items json for rendering in admin panel
    orders_data = []
    for o in orders:
        try:
            it = json.loads(o.items)
        except:
            it = []
        orders_data.append({
            'order': o,
            'items_list': it
        })
        
    return render_template('admin.html', 
                           total_sales=total_sales, 
                           total_bookings=total_bookings,
                           total_orders=total_orders,
                           reservations=reservations, 
                           orders_data=orders_data, 
                           menu_items=menu_items)

@app.route('/admin/menu/add', methods=['POST'])
def admin_menu_add():
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))
        
    name = request.form.get('name').strip()
    description = request.form.get('description').strip()
    price = float(request.form.get('price'))
    category = request.form.get('category')
    image_url = request.form.get('image_url').strip()
    
    if not image_url:
        image_url = "https://images.unsplash.com/photo-1495474472287-4d71bcdd2085?q=80&w=300&auto=format&fit=crop" # Generic coffee placeholder
        
    new_item = MenuItem(
        name=name,
        description=description,
        price=price,
        category=category,
        image_url=image_url,
        is_available=True
    )
    
    db.session.add(new_item)
    db.session.commit()
    
    flash('Menu item added successfully!', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/menu/delete/<int:item_id>', methods=['POST'])
def admin_menu_delete(item_id):
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))
        
    item = db.session.get(MenuItem, item_id)
    if item:
        db.session.delete(item)
        db.session.commit()
        flash('Menu item deleted.', 'success')
    else:
        flash('Menu item not found.', 'error')
        
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/order/status/<int:order_id>', methods=['POST'])
def admin_order_status(order_id):
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))
        
    status = request.form.get('status')
    order = db.session.get(Order, order_id)
    if order and status in ['Preparing', 'Completed']:
        order.order_status = status
        db.session.commit()
        flash(f'Order #{order.id} status updated to {status}.', 'success')
    else:
        flash('Invalid status update.', 'error')
        
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/location/add', methods=['POST'])
def admin_location_add():
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))
        
    name = request.form.get('name').strip()
    address = request.form.get('address').strip()
    map_url = request.form.get('map_url').strip()
    phone = request.form.get('phone').strip()
    
    if not name or not address or not map_url:
        flash('Name, Address and Navigation/Map URL are required.', 'error')
        return redirect(url_for('admin_dashboard'))
        
    new_loc = CafeLocation(
        name=name,
        address=address,
        map_url=map_url,
        phone=phone if phone else None
    )
    
    db.session.add(new_loc)
    db.session.commit()
    
    flash('Cafe location added successfully!', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/location/delete/<int:location_id>', methods=['POST'])
def admin_location_delete(location_id):
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))
        
    loc = db.session.get(CafeLocation, location_id)
    if loc:
        db.session.delete(loc)
        db.session.commit()
        flash('Cafe location deleted successfully.', 'success')
    else:
        flash('Location not found.', 'error')
        
    return redirect(url_for('admin_dashboard'))

# ----------------- MOCK PAYMENT WEBHOOK API & SIMULATION -----------------

@app.route('/mock-pay/<int:order_id>')
def mock_pay(order_id):
    order = db.session.get(Order, order_id)
    if not order:
        return "Order not found", 404
    return render_template('mock_pay.html', order=order)

@app.route('/api/orders/status/<int:order_id>')
def order_status(order_id):
    order = db.session.get(Order, order_id)
    if not order:
        return jsonify({'status': 'not_found'}), 404
    return jsonify({'status': order.payment_status})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
