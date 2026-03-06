import os
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import db, User, Delivery, Notification, Wallet, PayoutRequest
from werkzeug.security import generate_password_hash
from flask_socketio import SocketIO, emit, join_room, leave_room

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-here')
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'cargofind.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Render proxy support - use eventlet if available (production), otherwise fallback to default
socketio = SocketIO(app, cors_allowed_origins="*", async_mode=None)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        phone = request.form.get('phone', '').strip()
        password = request.form.get('password')
        full_name = request.form.get('full_name', '').strip()
        role = request.form.get('role', 'customer')
        
        user_exists = User.query.filter((User.email == email) | (User.phone == phone)).first()
        if user_exists:
            flash('Email or phone already exists')
            return redirect(url_for('register'))
        
        new_user = User(email=email, phone=phone, full_name=full_name, role=role)
        new_user.set_password(password)
        
        if role == 'driver':
            new_user.vehicle_type = request.form.get('vehicle_type')
            new_user.vehicle_id = request.form.get('vehicle_id')
            # Initialize wallet for driver
            wallet = Wallet(user=new_user)
            db.session.add(wallet)
        
        db.session.add(new_user)
        db.session.commit()
        
        flash('Registration successful!')
        return redirect(url_for('login'))
        
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        identifier = request.form.get('email', '').strip().lower()
        password = request.form.get('password')
        
        user = User.query.filter((User.email == identifier) | (User.phone == identifier)).first()
        
        if user and user.check_password(password):
            if not user.is_active:
                flash('Your account has been deactivated. Please contact an administrator.')
                return redirect(url_for('login'))
                
            login_user(user)
            if user.role == 'driver' and not user.is_approved:
                flash('Note: Your driver account is pending admin approval. You will be able to accept jobs once approved.')
            
            if user.role == 'admin':
                return redirect(url_for('admin_dashboard'))
            elif user.role == 'driver':
                return redirect(url_for('driver_dashboard'))
            else:
                return redirect(url_for('customer_dashboard'))
        
        flash('Invalid email or password')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

# --- Customer Routes ---
@app.route('/customer/dashboard')
@login_required
def customer_dashboard():
    if current_user.role != 'customer':
        return redirect(url_for('index'))
    
    active_deliveries = Delivery.query.filter_by(customer_id=current_user.id).filter(Delivery.status != 'Delivered').all()
    past_deliveries = Delivery.query.filter_by(customer_id=current_user.id, status='Delivered').order_by(Delivery.created_at.desc()).all()
    notifications = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.created_at.desc()).limit(5).all()
    
    return render_template('customer/dashboard.html', active=active_deliveries, past=past_deliveries, notifications=notifications)

@app.route('/customer/track/<int:delivery_id>')
@login_required
def track_delivery(delivery_id):
    delivery = Delivery.query.get_or_404(delivery_id)
    if delivery.customer_id != current_user.id:
        return redirect(url_for('index'))
    return render_template('customer/tracking.html', delivery=delivery)

@app.route('/customer/pay/<int:delivery_id>', methods=['POST'])
@login_required
def process_payment(delivery_id):
    delivery = Delivery.query.get_or_404(delivery_id)
    if delivery.customer_id == current_user.id and delivery.status == 'Delivered':
        delivery.payment_status = 'Paid'
        delivery.payment_method = request.form.get('payment_method')
        
        # Credit driver wallet
        if delivery.driver_id:
            driver = User.query.get(delivery.driver_id)
            if not driver.wallet:
                driver.wallet = Wallet(user_id=driver.id)
            driver.wallet.balance += delivery.total_cost
            driver.wallet.total_earned += delivery.total_cost
            
        db.session.commit()
        flash('Payment successful! Thank you for using CargoFind.')
    return redirect(url_for('customer_dashboard'))

@app.route('/customer/rate/<int:delivery_id>', methods=['POST'])
@login_required
def rate_delivery(delivery_id):
    delivery = Delivery.query.get_or_404(delivery_id)
    if delivery.customer_id == current_user.id:
        try:
            rating_val = request.form.get('rating')
            if rating_val:
                delivery.rating = int(rating_val)
                delivery.feedback = request.form.get('feedback')
                db.session.commit()
                flash('Thank you for your feedback!')
            else:
                flash('Please select a rating')
        except (ValueError, TypeError):
            flash('Invalid rating value')
    return redirect(url_for('customer_dashboard'))

@app.route('/customer/book', methods=['GET', 'POST'])
@login_required
def book_delivery():
    if current_user.role != 'customer':
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        pickup_loc = request.form.get('pickup_location')
        pickup_lat_val = request.form.get('pickup_lat')
        pickup_lng_val = request.form.get('pickup_lng')
        
        dropoff_loc = request.form.get('dropoff_location')
        dropoff_lat_val = request.form.get('dropoff_lat')
        dropoff_lng_val = request.form.get('dropoff_lng')

        if not all([pickup_lat_val, pickup_lng_val, dropoff_lat_val, dropoff_lng_val]):
            flash('Please select pickup and drop-off locations on the map.')
            return redirect(url_for('book_delivery'))
            
        try:
            pickup_lat = float(pickup_lat_val)
            pickup_lng = float(pickup_lng_val)
            dropoff_lat = float(dropoff_lat_val)
            dropoff_lng = float(dropoff_lng_val)
        except (ValueError, TypeError):
            flash('Invalid location coordinates.')
            return redirect(url_for('book_delivery'))
        
        goods_desc = request.form.get('goods_description')
        
        # Safely convert weight and distance
        weight_val = request.form.get('weight', '0')
        weight = float(weight_val) if weight_val and weight_val.strip() else 0.0
        
        vehicle_type = request.form.get('vehicle_type')
        distance_val = request.form.get('distance_km', '0')
        distance = float(distance_val) if distance_val and distance_val.strip() else 0.0
        effective_distance = max(distance, 1.0)
        
        # Calculate cost
        base_fare = 500
        rates = {'bike': 150, 'car': 250, 'van': 350, 'truck': 500}
        total_cost = base_fare + (rates.get(vehicle_type, 250) * effective_distance)
        
        if request.form.get('heavy_goods'): total_cost += 1000
        if request.form.get('fragile_goods'): total_cost += 500
        if request.form.get('urgent_delivery'): total_cost += 1000
        
        new_delivery = Delivery(
            customer_id=current_user.id,
            pickup_location=pickup_loc,
            pickup_lat=pickup_lat,
            pickup_lng=pickup_lng,
            dropoff_location=dropoff_loc,
            dropoff_lat=dropoff_lat,
            dropoff_lng=dropoff_lng,
            goods_description=goods_desc,
            weight=weight,
            vehicle_type=vehicle_type,
            distance_km=distance,
            total_cost=total_cost,
            status='Pending'
        )
        
        db.session.add(new_delivery)
        db.session.commit()
        
        flash(f'Delivery booked successfully! Total Cost: {total_cost} XAF')
        return redirect(url_for('customer_dashboard'))

    return render_template('customer/book.html')

@app.route('/api/calculate_price', methods=['POST'])
@login_required
def calculate_price():
    data = request.json
    distance_val = data.get('distance', 0)
    try:
        distance = float(distance_val) if distance_val else 0.0
    except (ValueError, TypeError):
        distance = 0.0
    effective_distance = max(distance, 1.0)
    vehicle_type = data.get('vehicle_type', 'car')
    
    base_fare = 500
    rates = {'bike': 150, 'car': 250, 'van': 350, 'truck': 500}
    total_cost = base_fare + (rates.get(vehicle_type, 250) * effective_distance)
    
    if data.get('heavy'): total_cost += 1000
    if data.get('fragile'): total_cost += 500
    if data.get('urgent'): total_cost += 1000
    
    return jsonify({'total_cost': total_cost})

# --- Driver Routes ---
@app.route('/driver/dashboard')
@login_required
def driver_dashboard():
    if current_user.role != 'driver':
        return redirect(url_for('index'))
    
    active_job = Delivery.query.filter_by(driver_id=current_user.id).filter(Delivery.status != 'Delivered').first()
    completed_jobs = Delivery.query.filter_by(driver_id=current_user.id, status='Delivered').all()
    total_earnings = sum(job.total_cost for job in completed_jobs if job.payment_status == 'Paid')
    payout_requests = PayoutRequest.query.filter_by(user_id=current_user.id).order_by(PayoutRequest.created_at.desc()).all()
    
    return render_template('driver/dashboard.html', 
                           active_job=active_job, 
                           completed_count=len(completed_jobs), 
                           earnings=total_earnings,
                           payout_requests=payout_requests)

@app.route('/driver/jobs')
@login_required
def available_jobs():
    if current_user.role != 'driver':
        return redirect(url_for('index'))
    
    if not current_user.is_approved:
        flash('You must be approved by an administrator before you can accept jobs.')
        return redirect(url_for('driver_dashboard'))
    
    # Check if driver is already on a job
    active_job = Delivery.query.filter_by(driver_id=current_user.id).filter(Delivery.status.in_(['Accepted', 'Picked Up', 'In Transit', 'Traffic Delay'])).first()
    
    # Filter jobs by driver's vehicle type to ensure relevance
    jobs = Delivery.query.filter_by(status='Pending', vehicle_type=current_user.vehicle_type).all()
    general_jobs = Delivery.query.filter_by(status='Pending', vehicle_type=None).all()
    
    all_jobs = jobs + general_jobs
    return render_template('driver/jobs.html', jobs=all_jobs, is_busy=active_job is not None)

@app.route('/driver/accept/<int:delivery_id>')
@login_required
def accept_job(delivery_id):
    if current_user.role != 'driver':
        return redirect(url_for('index'))
    
    # Check if driver already has an active job
    active_job = Delivery.query.filter_by(driver_id=current_user.id).filter(Delivery.status.in_(['Accepted', 'Picked Up', 'In Transit', 'Traffic Delay'])).first()
    if active_job:
        flash('You cannot accept a new job while you have an active delivery.')
        return redirect(url_for('driver_dashboard'))
    
    delivery = Delivery.query.get_or_404(delivery_id)
    if delivery.status == 'Pending':
        delivery.driver_id = current_user.id
        delivery.status = 'Accepted'
        db.session.commit()
        flash('Job accepted!')
        
        # Notify customer (simple notification for now)
        notif = Notification(user_id=delivery.customer_id, message=f'Driver {current_user.full_name} accepted your delivery!')
        db.session.add(notif)
        db.session.commit()
        
    return redirect(url_for('driver_dashboard'))

@app.route('/driver/update_status/<int:delivery_id>', methods=['POST'])
@login_required
def update_status(delivery_id):
    if current_user.role != 'driver':
        return redirect(url_for('index'))
    
    delivery = Delivery.query.get_or_404(delivery_id)
    if delivery.driver_id == current_user.id:
        new_status = request.form.get('status')
        delivery.status = new_status
        db.session.commit()
        
        notif = Notification(user_id=delivery.customer_id, message=f'Delivery status updated to: {new_status}')
        db.session.add(notif)
        db.session.commit()
        
        flash(f'Status updated to {new_status}')
    return redirect(url_for('driver_dashboard'))

# --- Admin Routes ---
@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if current_user.role != 'admin':
        return redirect(url_for('index'))
    
    total_users = User.query.count()
    total_customers = User.query.filter_by(role='customer').count()
    total_drivers = User.query.filter_by(role='driver').count()
    pending_drivers = User.query.filter_by(role='driver', is_approved=False).count()
    
    active_deliveries = Delivery.query.filter(Delivery.status != 'Delivered').all()
    completed_deliveries = Delivery.query.filter_by(status='Delivered').all()
    
    total_revenue = sum(d.total_cost for d in completed_deliveries if d.payment_status == 'Paid')
    
    return render_template('admin/dashboard.html', 
                           total_users=total_users, 
                           total_customers=total_customers,
                           total_drivers=total_drivers,
                           pending_drivers_count=pending_drivers,
                           active_count=len(active_deliveries),
                           completed_count=len(completed_deliveries),
                           revenue=total_revenue,
                           active_deliveries=active_deliveries)

@app.route('/admin/users')
@login_required
def admin_users():
    if current_user.role != 'admin':
        return redirect(url_for('index'))
    users = User.query.all()
    return render_template('admin/users.html', users=users)

@app.route('/admin/user/toggle/<int:user_id>')
@login_required
def toggle_user_status(user_id):
    if current_user.role != 'admin':
        return redirect(url_for('index'))
    user = User.query.get_or_404(user_id)
    user.is_active = not user.is_active
    db.session.commit()
    flash(f'User {user.full_name} status updated.')
    return redirect(url_for('admin_users'))

@app.route('/admin/drivers/pending')
@login_required
def admin_pending_drivers():
    if current_user.role != 'admin':
        return redirect(url_for('index'))
    pending_drivers = User.query.filter_by(role='driver', is_approved=False).all()
    return render_template('admin/pending_drivers.html', drivers=pending_drivers)

@app.route('/admin/driver/approve/<int:user_id>')
@login_required
def approve_driver(user_id):
    if current_user.role != 'admin':
        return redirect(url_for('index'))
    user = User.query.get_or_404(user_id)
    if user.role == 'driver':
        user.is_approved = True
        db.session.commit()
        
        # Notify driver
        notif = Notification(user_id=user.id, message='Congratulations! Your driver account has been approved.')
        db.session.add(notif)
        db.session.commit()
        
        flash(f'Driver {user.full_name} has been approved.')
    return redirect(url_for('admin_pending_drivers'))

@app.route('/driver/mark_paid/<int:delivery_id>', methods=['POST'])
@login_required
def mark_paid(delivery_id):
    if current_user.role != 'driver':
        return redirect(url_for('index'))
    delivery = Delivery.query.get_or_404(delivery_id)
    if delivery.driver_id == current_user.id:
        delivery.payment_status = 'Paid'
        delivery.payment_method = 'Cash (Collected by Driver)'
        
        # Credit driver wallet (internal tracking)
        if not current_user.wallet:
            current_user.wallet = Wallet(user_id=current_user.id)
        current_user.wallet.balance += delivery.total_cost
        current_user.wallet.total_earned += delivery.total_cost
        
        db.session.commit()
        flash('Payment marked as received.')
    return redirect(url_for('driver_dashboard'))

@app.route('/customer/invoice/<int:delivery_id>')
@login_required
def view_invoice(delivery_id):
    delivery = Delivery.query.get_or_404(delivery_id)
    if delivery.customer_id != current_user.id:
        return redirect(url_for('index'))
    return render_template('customer/invoice.html', delivery=delivery)

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        current_user.full_name = request.form.get('full_name')
        current_user.phone = request.form.get('phone')
        current_user.address = request.form.get('address')
        db.session.commit()
        flash('Profile updated!')
        return redirect(url_for('profile'))
    return render_template('profile.html')

@app.route('/customer/edit/<int:delivery_id>', methods=['GET', 'POST'])
@login_required
def edit_delivery(delivery_id):
    delivery = Delivery.query.get_or_404(delivery_id)
    if delivery.customer_id != current_user.id or delivery.status != 'Pending':
        flash('You cannot edit this delivery.')
        return redirect(url_for('customer_dashboard'))
    
    if request.method == 'POST':
        delivery.pickup_location = request.form.get('pickup_location')
        delivery.pickup_lat = float(request.form.get('pickup_lat'))
        delivery.pickup_lng = float(request.form.get('pickup_lng'))
        delivery.dropoff_location = request.form.get('dropoff_location')
        delivery.dropoff_lat = float(request.form.get('dropoff_lat'))
        delivery.dropoff_lng = float(request.form.get('dropoff_lng'))
        delivery.goods_description = request.form.get('goods_description')
        delivery.weight = float(request.form.get('weight', 0))
        delivery.vehicle_type = request.form.get('vehicle_type')
        delivery.distance_km = float(request.form.get('distance_km', 0))
        effective_distance = max(delivery.distance_km, 1.0)
        
        # Recalculate cost
        base_fare = 500
        rates = {'bike': 150, 'car': 250, 'van': 350, 'truck': 500}
        total_cost = base_fare + (rates.get(delivery.vehicle_type, 250) * effective_distance)
        
        if request.form.get('heavy_goods'): total_cost += 1000
        if request.form.get('fragile_goods'): total_cost += 500
        if request.form.get('urgent_delivery'): total_cost += 1000
        
        delivery.total_cost = total_cost
        db.session.commit()
        
        flash('Delivery request updated successfully!')
        return redirect(url_for('customer_dashboard'))

    return render_template('customer/edit_book.html', delivery=delivery)

@app.route('/driver/payout', methods=['POST'])
@login_required
def request_payout():
    if current_user.role != 'driver':
        return redirect(url_for('index'))
    
    amount = float(request.form.get('amount', 0))
    method = request.form.get('payment_method')
    
    if not current_user.wallet or current_user.wallet.balance < amount:
        flash('Insufficient balance in your wallet.')
        return redirect(url_for('driver_dashboard'))
    
    if amount < 5000:
        flash('Minimum payout amount is 5,000 XAF.')
        return redirect(url_for('driver_dashboard'))
    
    # Deduct from wallet immediately to prevent double withdrawal
    current_user.wallet.balance -= amount
    
    new_payout = PayoutRequest(user_id=current_user.id, amount=amount, payment_method=method)
    db.session.add(new_payout)
    db.session.commit()
    
    flash('Payout request submitted successfully! Admin will process it shortly.')
    return redirect(url_for('driver_dashboard'))

@app.route('/admin/payouts')
@login_required
def admin_payouts():
    if current_user.role != 'admin':
        return redirect(url_for('index'))
    payouts = PayoutRequest.query.order_by(PayoutRequest.created_at.desc()).all()
    return render_template('admin/payouts.html', payouts=payouts)

@app.route('/admin/payout/approve/<int:payout_id>')
@login_required
def approve_payout(payout_id):
    if current_user.role != 'admin':
        return redirect(url_for('index'))
    payout = PayoutRequest.query.get_or_404(payout_id)
    if payout.status == 'Pending':
        payout.status = 'Processed'
        
        # Notify driver
        notif = Notification(user_id=payout.user_id, message=f'Your payout request of {payout.amount} XAF has been processed!')
        db.session.add(notif)
        db.session.commit()
        
        flash(f'Payout for {payout.user.full_name} marked as processed.')
    return redirect(url_for('admin_payouts'))

# --- SocketIO Events ---
@socketio.on('join_delivery')
def on_join_delivery(data):
    delivery_id = data.get('delivery_id')
    if delivery_id:
        room = f'delivery_{delivery_id}'
        join_room(room)
        print(f'User joined room: {room}')

@socketio.on('leave_delivery')
def on_leave_delivery(data):
    delivery_id = data.get('delivery_id')
    if delivery_id:
        room = f'delivery_{delivery_id}'
        leave_room(room)
        print(f'User left room: {room}')

@socketio.on('update_location')
def handle_location_update(data):
    delivery_id = data.get('delivery_id')
    if delivery_id:
        # Update driver location in database
        if current_user.is_authenticated and current_user.role == 'driver':
            current_user.current_lat = data.get('lat')
            current_user.current_lng = data.get('lng')
            db.session.commit()
            
        room = f'delivery_{delivery_id}'
        emit('location_changed', data, room=room)

with app.app_context():
    db.create_all()
    # Create default admin if not exists
    if not User.query.filter_by(role='admin').first():
        admin = User(email='admin@cargofind.com', phone='000000000', full_name='System Admin', role='admin')
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()

if __name__ == '__main__':
    socketio.run(app, debug=True)

