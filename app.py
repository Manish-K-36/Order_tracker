import sqlite3
import os
import random
import string
import datetime
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash

# Load local .env file if it exists (for local testing)
# Do not overwrite variables already set in the environment (e.g. on Render/Replit)
env_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), '.env')
if os.path.exists(env_path):
    with open(env_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, val = line.split('=', 1)
                k = key.strip()
                v = val.strip().strip('"').strip("'")
                if k not in os.environ:
                    os.environ[k] = v

app = Flask(__name__)
# Secret key for session signing. In production, this should be set via environment variable.
app.secret_key = os.environ.get('SECRET_KEY', 'b2b-order-tracker-dev-secret-key-12345')

# Admin password. In production, this should be set via environment variable.
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'admin123')

DATABASE = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'database.db')

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import threading

def get_smtp_config():
    config = {
        'SMTP_SERVER': os.environ.get('SMTP_SERVER'),
        'SMTP_PORT': int(os.environ.get('SMTP_PORT', '587')) if os.environ.get('SMTP_PORT', '587').isdigit() else 587,
        'SMTP_USERNAME': os.environ.get('SMTP_USERNAME'),
        'SMTP_PASSWORD': os.environ.get('SMTP_PASSWORD'),
        'SENDER_NAME': os.environ.get('SENDER_NAME', 'B2B Order Tracker')
    }
    
    # Reload local .env dynamically in development to allow updates without server reboot.
    # On Render/Replit, environment variables should not be overwritten by a local/template .env.
    if 'RENDER' not in os.environ and 'PORT' not in os.environ:
        env_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), '.env')
        if os.path.exists(env_path):
            with open(env_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, val = line.split('=', 1)
                        k = key.strip()
                        v = val.strip().strip('"').strip("'")
                        if k == 'SMTP_PORT':
                            config[k] = int(v) if v.isdigit() else 587
                        else:
                            config[k] = v
    return config

def send_email_async(url_root, order_number, client_name, recipient_email, status, estimated_delivery, courier_name, tracking_number):
    if not recipient_email:
        return
        
    config = get_smtp_config()
    
    smtp_server = config.get('SMTP_SERVER')
    smtp_port = config.get('SMTP_PORT', 587)
    smtp_username = config.get('SMTP_USERNAME')
    smtp_password = config.get('SMTP_PASSWORD')
    sender_name = config.get('SENDER_NAME', 'B2B Order Tracker')
    
    if not smtp_server or not smtp_username or not smtp_password:
        print(f"[Email Warning] SMTP credentials not set. Email not sent for Order #{order_number}.", flush=True)
        return

    def send_thread():
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"Update on your Order #{order_number} - {status}"
            msg['From'] = f"{sender_name} <{smtp_username}>"
            msg['To'] = recipient_email
            
            tracking_link = f"{url_root.rstrip('/')}/track/{order_number}"
            
            html_content = f"""
            <html>
            <body style="font-family: Arial, sans-serif; background-color: #0d111a; color: #f0f3f8; padding: 20px;">
                <div style="max-width: 600px; margin: 0 auto; background-color: #161b22; border: 1px solid #30363d; border-radius: 12px; padding: 30px; box-shadow: 0 10px 25px rgba(0,0,0,0.3);">
                    <div style="text-align: center; margin-bottom: 25px;">
                        <span style="font-size: 40px;">📦</span>
                        <h2 style="color: #ffffff; margin-top: 10px;">Order Status Update</h2>
                    </div>
                    
                    <p style="font-size: 16px; color: #c9d1d9; line-height: 1.5;">Hello <strong>{client_name}</strong>,</p>
                    <p style="font-size: 16px; color: #c9d1d9; line-height: 1.5;">The status of your order <strong>#{order_number}</strong> has been updated to:</p>
                    
                    <div style="text-align: center; margin: 25px 0;">
                        <span style="background-color: #58a6ff; color: #ffffff; font-weight: bold; font-size: 18px; padding: 10px 24px; border-radius: 50px; display: inline-block;">
                            {status}
                        </span>
                    </div>
                    
                    <table style="width: 100%; border-collapse: collapse; margin-bottom: 25px; color: #c9d1d9; font-size: 15px;">
                        <tr>
                            <td style="padding: 10px 0; border-bottom: 1px solid #30363d; color: #8b949e;">Expected Dispatch/Delivery:</td>
                            <td style="padding: 10px 0; border-bottom: 1px solid #30363d; text-align: right; font-weight: bold;">{estimated_delivery or 'Updating soon'}</td>
                        </tr>
            """
            
            if courier_name or tracking_number:
                html_content += f"""
                        <tr>
                            <td style="padding: 10px 0; border-bottom: 1px solid #30363d; color: #8b949e;">Courier Partner:</td>
                            <td style="padding: 10px 0; border-bottom: 1px solid #30363d; text-align: right; font-weight: bold;">{courier_name or 'N/A'}</td>
                        </tr>
                        <tr>
                            <td style="padding: 10px 0; border-bottom: 1px solid #30363d; color: #8b949e;">Tracking Number:</td>
                            <td style="padding: 10px 0; border-bottom: 1px solid #30363d; text-align: right; font-weight: bold;">{tracking_number or 'N/A'}</td>
                        </tr>
                """
                
            html_content += f"""
                    </table>
                    
                    <div style="text-align: center; margin-top: 30px; margin-bottom: 20px;">
                        <a href="{tracking_link}" target="_blank" style="background-color: #238636; color: #ffffff; text-decoration: none; font-weight: bold; font-size: 16px; padding: 12px 24px; border-radius: 6px; display: inline-block;">
                            View Live Tracking Progress ➔
                        </a>
                    </div>
                    
                    <div style="margin-top: 35px; padding-top: 20px; border-top: 1px solid #30363d; text-align: center; font-size: 12px; color: #8b949e;">
                        <p>This is an automated update for your purchase from {sender_name}.</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            msg.attach(MIMEText(html_content, 'html'))
            
            if smtp_port == 465:
                server = smtplib.SMTP_SSL(smtp_server, smtp_port, timeout=10)
                server.ehlo()
            else:
                server = smtplib.SMTP(smtp_server, smtp_port, timeout=10)
                server.ehlo()
                server.starttls()
                server.ehlo()
                
            server.login(smtp_username, smtp_password)
            server.sendmail(smtp_username, recipient_email, msg.as_string())
            server.quit()
            print(f"[Email Success] Sent to {recipient_email} for Order #{order_number}", flush=True)
        except Exception as e:
            print(f"[Email Error] Failed to send email to {recipient_email} for Order #{order_number}: {e}", flush=True)
            
    threading.Thread(target=send_thread).start()

def run_query(query, params=(), commit=False, fetchone=False, fetchall=False):
    db_url = os.environ.get('DATABASE_URL')
    if db_url:
        # PostgreSQL
        import psycopg2
        import psycopg2.extras
        if db_url.startswith("postgres://"):
            db_url = db_url.replace("postgres://", "postgresql://", 1)
        # Convert sqlite placeholders '?' to postgres '%s'
        query = query.replace('?', '%s')
        
        conn = psycopg2.connect(db_url)
        try:
            with conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    cur.execute(query, params)
                    if commit:
                        conn.commit()
                    if fetchone:
                        return cur.fetchone()
                    if fetchall:
                        return cur.fetchall()
        finally:
            conn.close()
    else:
        # SQLite
        import sqlite3
        conn = sqlite3.connect(DATABASE)
        conn.row_factory = sqlite3.Row
        try:
            with conn:
                cur = conn.execute(query, params)
                if commit:
                    conn.commit()
                if fetchone:
                    return cur.fetchone()
                if fetchall:
                    return cur.fetchall()
        finally:
            conn.close()

def init_db():
    db_url = os.environ.get('DATABASE_URL')
    if db_url:
        # PostgreSQL Setup
        import psycopg2
        if db_url.startswith("postgres://"):
            db_url = db_url.replace("postgres://", "postgresql://", 1)
        conn = psycopg2.connect(db_url)
        try:
            with conn:
                with conn.cursor() as cur:
                    cur.execute('''
                        CREATE TABLE IF NOT EXISTS orders (
                            id SERIAL PRIMARY KEY,
                            order_number VARCHAR(100) UNIQUE NOT NULL,
                            client_name VARCHAR(255) NOT NULL,
                            item_details TEXT NOT NULL,
                            status VARCHAR(100) NOT NULL,
                            notes TEXT,
                            courier_name VARCHAR(255),
                            tracking_number VARCHAR(255),
                            estimated_delivery VARCHAR(255),
                            created_at VARCHAR(100) NOT NULL,
                            updated_at VARCHAR(100) NOT NULL,
                            email VARCHAR(255)
                        )
                    ''')
                    # PostgreSQL column migration: Ensure the email column is added if it was missing
                    cur.execute("ALTER TABLE orders ADD COLUMN IF NOT EXISTS email VARCHAR(255)")
        finally:
            conn.close()
    else:
        # SQLite Setup
        import sqlite3
        conn = sqlite3.connect(DATABASE)
        try:
            with conn:
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS orders (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        order_number TEXT UNIQUE NOT NULL,
                        client_name TEXT NOT NULL,
                        item_details TEXT NOT NULL,
                        status TEXT NOT NULL,
                        notes TEXT,
                        courier_name TEXT,
                        tracking_number TEXT,
                        estimated_delivery TEXT,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL,
                        email TEXT
                    )
                ''')
                # Check if email column exists (migration for existing databases)
                cursor = conn.execute("PRAGMA table_info(orders)")
                columns = [row[1] for row in cursor.fetchall()]
                if 'email' not in columns:
                    conn.execute("ALTER TABLE orders ADD COLUMN email TEXT")
        finally:
            conn.close()

# Helper to generate a unique random order number if not specified
def generate_order_number():
    year = datetime.datetime.now().year
    while True:
        # Generate MK-YYYY-XXXX (e.g. MK-2026-B81C)
        rand_suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
        order_num = f"MK-{year}-{rand_suffix}"
        
        # Check uniqueness
        row = run_query("SELECT id FROM orders WHERE order_number = ?", (order_num,), fetchone=True)
        if row is None:
            return order_num

# Initialize database
init_db()

# --- ROUTES ---

@app.route('/')
def home():
    # Homepage allows clients to enter an Order ID or redirects to admin if logged in
    return render_template('home.html')

@app.route('/track', methods=['GET', 'POST'])
def track_search():
    if request.method == 'POST':
        order_number = request.form.get('order_number', '').strip().upper()
        if not order_number:
            flash('Please enter a valid Order ID', 'error')
            return redirect(url_for('home'))
        return redirect(url_for('track_order', order_number=order_number))
    return redirect(url_for('home'))

@app.route('/track/<order_number>')
def track_order(order_number):
    order_number = order_number.strip().upper()
    order = run_query("SELECT * FROM orders WHERE UPPER(order_number) = ?", (order_number,), fetchone=True)
    
    if not order:
        return render_template('home.html', error=f"Order '{order_number}' not found. Please check and try again.")
    
    # Define statuses and their display icons / step numbers for progress
    status_flow = [
        {"name": "Order Received", "label": "Order Confirmed", "desc": "We have received your order details."},
        {"name": "Sample Approval", "label": "Sample Approval", "desc": "Design preview or sample sent for your confirmation."},
        {"name": "Production Start", "label": "Production Started", "desc": "Custom crafting, engraving, or manufacturing is underway."},
        {"name": "Packing", "label": "Quality Check & Packing", "desc": "Items are checked for quality and securely packed."},
        {"name": "Ready for Dispatch", "label": "Ready for Dispatch", "desc": "Your package is ready to be handed over to the courier."},
        {"name": "In Transit", "label": "In Transit", "desc": "Your order is on the way to your destination."},
        {"name": "Delivered", "label": "Delivered", "desc": "Order successfully delivered!"}
    ]
    
    # Calculate current step index
    current_status = order['status']
    current_step = 0
    for idx, step in enumerate(status_flow):
        if step['name'] == current_status:
            current_step = idx
            break
            
    return render_template('track.html', order=order, status_flow=status_flow, current_step=current_step)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if session.get('logged_in'):
        return redirect(url_for('admin_dashboard'))
        
    admin_password_is_default = (ADMIN_PASSWORD == 'admin123')
        
    if request.method == 'POST':
        password = request.form.get('password')
        if password == ADMIN_PASSWORD:
            session['logged_in'] = True
            flash('Successfully logged in!', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            return render_template('login.html', error='Invalid Password', admin_password_is_default=admin_password_is_default)
            
    return render_template('login.html', admin_password_is_default=admin_password_is_default)

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('Logged out successfully.', 'info')
    return redirect(url_for('login'))

# Decorator to secure admin routes
def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/admin')
@login_required
def admin_dashboard():
    # Support sorting & simple searching
    search_query = request.args.get('search', '').strip()
    status_filter = request.args.get('status', '').strip()
    
    sql = "SELECT * FROM orders WHERE 1=1"
    params = []
    
    if search_query:
        sql += " AND (order_number LIKE ? OR client_name LIKE ? OR item_details LIKE ?)"
        search_pattern = f"%{search_query}%"
        params.extend([search_pattern, search_pattern, search_pattern])
        
    if status_filter:
        sql += " AND status = ?"
        params.append(status_filter)
        
    sql += " ORDER BY id DESC"
    
    orders = run_query(sql, params, fetchall=True)
    
    # Provide stats
    total_orders_row = run_query("SELECT COUNT(*) as cnt FROM orders", fetchone=True)
    total_orders = total_orders_row['cnt'] if total_orders_row else 0
    
    in_production_row = run_query("SELECT COUNT(*) as cnt FROM orders WHERE status = 'Production Start'", fetchone=True)
    in_production = in_production_row['cnt'] if in_production_row else 0
    
    ready_or_transit_row = run_query("SELECT COUNT(*) as cnt FROM orders WHERE status IN ('Ready for Dispatch', 'In Transit')", fetchone=True)
    ready_or_transit = ready_or_transit_row['cnt'] if ready_or_transit_row else 0
    
    return render_template('admin.html', 
                           orders=orders, 
                           search=search_query, 
                           status_filter=status_filter,
                           total_orders=total_orders,
                           in_production=in_production,
                           ready_or_transit=ready_or_transit,
                           admin_password_is_default=(ADMIN_PASSWORD == 'admin123'))

@app.route('/admin/create', methods=['POST'])
@login_required
def admin_create_order():
    client_name = request.form.get('client_name', '').strip()
    item_details = request.form.get('item_details', '').strip()
    status = request.form.get('status', 'Order Received').strip()
    notes = request.form.get('notes', '').strip()
    courier_name = request.form.get('courier_name', '').strip()
    tracking_number = request.form.get('tracking_number', '').strip()
    estimated_delivery = request.form.get('estimated_delivery', '').strip()
    email = request.form.get('email', '').strip()
    
    order_number = request.form.get('order_number', '').strip().upper()
    if not order_number:
        order_number = generate_order_number()
        
    if not client_name or not item_details:
        flash('Client Name and Item Details are required!', 'error')
        return redirect(url_for('admin_dashboard'))
        
    now_str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    try:
        run_query('''
            INSERT INTO orders (order_number, client_name, item_details, status, notes, courier_name, tracking_number, estimated_delivery, created_at, updated_at, email)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (order_number, client_name, item_details, status, notes, courier_name, tracking_number, estimated_delivery, now_str, now_str, email), commit=True)
        flash(f'Order {order_number} created successfully!', 'success')
        
        # Trigger email notification
        if email:
            send_email_async(request.url_root, order_number, client_name, email, status, estimated_delivery, courier_name, tracking_number)
            
    except Exception as e:
        err_str = str(e).lower()
        if 'unique' in err_str or 'duplicate' in err_str:
            flash(f'Order ID {order_number} already exists! Please use a unique ID.', 'error')
        else:
            flash(f'Error creating order: {e}', 'error')
        
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/update/<int:order_id>', methods=['POST'])
@login_required
def admin_update_order(order_id):
    client_name = request.form.get('client_name', '').strip()
    item_details = request.form.get('item_details', '').strip()
    status = request.form.get('status', '').strip()
    notes = request.form.get('notes', '').strip()
    courier_name = request.form.get('courier_name', '').strip()
    tracking_number = request.form.get('tracking_number', '').strip()
    estimated_delivery = request.form.get('estimated_delivery', '').strip()
    email = request.form.get('email', '').strip()
    
    if not client_name or not item_details or not status:
        flash('Client Name, Item Details, and Status are required!', 'error')
        return redirect(url_for('admin_dashboard'))
        
    # Retrieve previous order info to check status change
    old_order = run_query("SELECT status, email, order_number FROM orders WHERE id = ?", (order_id,), fetchone=True)
    
    now_str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    run_query('''
        UPDATE orders 
        SET client_name = ?, item_details = ?, status = ?, notes = ?, courier_name = ?, tracking_number = ?, estimated_delivery = ?, updated_at = ?, email = ?
        WHERE id = ?
    ''', (client_name, item_details, status, notes, courier_name, tracking_number, estimated_delivery, now_str, email, order_id), commit=True)
    
    flash('Order updated successfully!', 'success')
    
    # Trigger status change notification
    if old_order and email and (old_order['status'] != status):
        send_email_async(request.url_root, old_order['order_number'], client_name, email, status, estimated_delivery, courier_name, tracking_number)
        
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete/<int:order_id>', methods=['POST'])
@login_required
def admin_delete_order(order_id):
    run_query("DELETE FROM orders WHERE id = ?", (order_id,), commit=True)
    flash('Order deleted successfully!', 'success')
    return redirect(url_for('admin_dashboard'))

if __name__ == '__main__':
    # Run server locally on port 5000
    app.run(host='0.0.0.0', port=5000, debug=True)
