import os
import random
import string
from dotenv import load_dotenv
# Explicitly load .env from current directory
basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import db, User, Delivery, Notification, Wallet
from werkzeug.security import generate_password_hash
from werkzeug.utils import secure_filename
from flask_socketio import SocketIO, emit, join_room, leave_room
import base64
import numpy as np
import cv2
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def compare_faces(path1, path2):
    """
    Perform a robust face comparison using OpenCV-only methods.
    Detects faces using Haar Cascades and compares them using Histogram similarity.
    This is highly portable and doesn't require complex ML libraries.
    """
    # Load images
    img1 = cv2.imread(path1)
    img2 = cv2.imread(path2)
    if img1 is None or img2 is None: return False

    # Convert to grayscale for Haar cascade
    gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
    gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)

    # Load pre-trained face detector (Haar Cascade)
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

    # Detect faces
    faces1 = face_cascade.detectMultiScale(gray1, 1.1, 4)
    faces2 = face_cascade.detectMultiScale(gray2, 1.1, 4)

    if len(faces1) == 0 or len(faces2) == 0:
        return False

    # Extract first face from each
    (x1, y1, w1, h1) = faces1[0]
    (x2, y2, w2, h2) = faces2[0]
    face1 = gray1[y1:y1+h1, x1:x1+w1]
    face2 = gray2[y2:y2+h2, x2:x2+w2]

    # Resize to same dimensions for comparison
    face1 = cv2.resize(face1, (100, 100))
    face2 = cv2.resize(face2, (100, 100))

    # Calculate histograms for comparison
    hist1 = cv2.calcHist([face1], [0], None, [256], [0, 256])
    hist2 = cv2.calcHist([face2], [0], None, [256], [0, 256])
    cv2.normalize(hist1, hist1, 0, 1, cv2.NORM_MINMAX)
    cv2.normalize(hist2, hist2, 0, 1, cv2.NORM_MINMAX)

    # Compare histograms using correlation (closer to 1.0 means more similar)
    similarity = cv2.compareHist(hist1, hist2, cv2.HISTCMP_CORREL)
    
    # Also perform a basic SSIM-like Structural similarity via absolute difference
    diff = cv2.absdiff(face1, face2)
    diff_score = 1.0 - (np.mean(diff) / 255.0)

    # Combined score
    final_score = (similarity * 0.7) + (diff_score * 0.3)
    
    # Threshold for matching faces (Adjusted to 42%)
    return final_score > 0.42 

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-here')
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'cargofind.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join(basedir, 'static', 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload

# Create upload folder if it doesn't exist
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Render proxy support - use eventlet if available (production), otherwise fallback to default
socketio = SocketIO(app, cors_allowed_origins="*", async_mode=None)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def generate_otp():
    return ''.join(random.choices(string.digits, k=6))

def save_notification(user_id, message, link=None):
    notif = Notification(user_id=user_id, message=message, link=link)
    db.session.add(notif)
    db.session.commit()

@app.route('/notifications')
@login_required
def notifications():
    user_notifications = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.created_at.desc()).all()
    # Mark all as read when viewed
    for notif in user_notifications:
        notif.is_read = True
    db.session.commit()
    return render_template('notifications.html', notifications=user_notifications)

@app.route('/notifications/clear', methods=['POST'])
@login_required
def clear_notifications():
    Notification.query.filter_by(user_id=current_user.id).delete()
    db.session.commit()
    flash('All notifications cleared.', 'success')
    return redirect(url_for('notifications'))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/testimonials')
def testimonials():
    return render_template('testimonials.html')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        subject = request.form.get('subject')
        message_body = request.form.get('message')
        
        # Email configuration
        sender_email = "anyanicklaus@gmail.com"
        receiver_email = "anyanicklaus@gmail.com"
        # Try both os.environ and explicit load_dotenv check
        password = os.getenv('EMAIL_PASSWORD')
        
        # Create message
        msg = MIMEMultipart()
        msg['From'] = email
        msg['To'] = receiver_email
        msg['Subject'] = f"CargoFind Support: {subject}"
        
        body = f"Name: {name}\nEmail: {email}\n\nMessage:\n{message_body}"
        msg.attach(MIMEText(body, 'plain'))
        
        try:
            if not password:
                print("DEBUG: EMAIL_PASSWORD not found in environment variables.")
                flash('Email configuration missing.', 'danger')
                return redirect(url_for('contact'))

            # Use SSL for better reliability with Gmail
            server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
            server.login(sender_email, password)
            server.send_message(msg)
            server.quit()
            flash('Thank you for your message! Our support team will receive it shortly.', 'success')
                
        except Exception as e:
            print(f"Error sending email: {e}")
            flash(f'Error sending email: {str(e)}', 'danger')
            
        return redirect(url_for('index'))
    return render_template('contact.html')

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
            
            # Handle document uploads
            id_card_file = request.files.get('id_card')
            license_file = request.files.get('license')
            selfie_data = request.form.get('selfie_data')
            
            if not id_card_file or not license_file or not selfie_data:
                flash('Please upload ID card, license, and take a live selfie.', 'danger')
                return redirect(url_for('register'))
            
            # Save ID Card
            id_ext = id_card_file.filename.split('.')[-1]
            id_filename = secure_filename(f"driver_{email}_id.{id_ext}")
            id_path = os.path.join(app.config['UPLOAD_FOLDER'], id_filename)
            id_card_file.save(id_path)
            new_user.id_card_url = id_filename

            # Save License
            lic_ext = license_file.filename.split('.')[-1]
            lic_filename = secure_filename(f"driver_{email}_license.{lic_ext}")
            lic_path = os.path.join(app.config['UPLOAD_FOLDER'], lic_filename)
            license_file.save(lic_path)
            new_user.license_url = lic_filename

            # Process Selfie from Base64
            try:
                # Remove header from base64 string if present
                if ';base64,' in selfie_data:
                    format, imgstr = selfie_data.split(';base64,') 
                else:
                    imgstr = selfie_data
                
                selfie_filename = secure_filename(f"driver_{email}_selfie.jpg")
                selfie_path = os.path.join(app.config['UPLOAD_FOLDER'], selfie_filename)
                
                with open(selfie_path, "wb") as f:
                    f.write(base64.b64decode(imgstr))
                new_user.selfie_url = selfie_filename

                # FACE COMPARISON USING MEDIAPIPE + ORB
                match_confirmed = compare_faces(id_path, selfie_path)
                
                if not match_confirmed:
                    flash('Security alert: Your live selfie does not match your ID card photo.', 'danger')
                    # Cleanup failed attempt files
                    for p in [id_path, lic_path, selfie_path]:
                        if os.path.exists(p): os.remove(p)
                    return render_template('register.html', form_data=request.form)
                
                new_user.is_verified = True
                new_user.is_approved = False # Still needs admin approval
                
            except Exception as e:
                print(f"Face Error: {e}")
                flash('Security verification failed. Please ensure good lighting.')
                return render_template('register.html', form_data=request.form)
            
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
            save_notification(user.id, "Welcome back to CargoFind! You have successfully logged in.")
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
    
    # Get driver's current coordinates if a driver is assigned
    driver_lat = None
    driver_lng = None
    if delivery.driver_id:
        driver = User.query.get(delivery.driver_id)
        if driver:
            driver_lat = driver.current_lat
            driver_lng = driver.current_lng
            
    return render_template('customer/tracking.html', 
                           delivery=delivery, 
                           driver_lat=driver_lat, 
                           driver_lng=driver_lng)

@app.route('/checkout/<int:delivery_id>')
@login_required
def checkout(delivery_id):
    delivery = Delivery.query.get_or_404(delivery_id)
    if delivery.customer_id != current_user.id:
        return redirect(url_for('customer_dashboard'))
    return render_template('customer/checkout.html', delivery=delivery)

@app.route('/customer/pay/<int:delivery_id>', methods=['POST'])
@login_required
def process_payment(delivery_id):
    delivery = Delivery.query.get_or_404(delivery_id)
    if delivery.customer_id == current_user.id:
        method = request.form.get('payment_method')
        delivery.payment_method = method
        
        if method == 'Cash':
            delivery.payment_status = 'Pending'
            save_notification(current_user.id, f"You selected 'Pay in Cash' for delivery #{delivery.id}. Please pay the driver upon arrival.")
            flash('Payment preference saved. Please pay the driver in cash.', 'info')
        else:
            # Mocking a successful mobile money transaction
            delivery.payment_status = 'Paid'
            
            # Credit driver wallet if driver is assigned
            if delivery.driver_id:
                driver = User.query.get(delivery.driver_id)
                if not driver.wallet:
                    driver.wallet = Wallet(user_id=driver.id)
                driver.wallet.balance += delivery.total_cost
                driver.wallet.total_earned += delivery.total_cost
                
            save_notification(current_user.id, f"Mobile Money payment of {delivery.total_cost} XAF for delivery #{delivery.id} was successful.")
            flash(f'Payment of {delivery.total_cost} XAF via {method} was successful!', 'success')
            
        db.session.commit()
    return redirect(url_for('customer_dashboard'))

@app.route('/customer/cancel/<int:delivery_id>', methods=['POST'])
@login_required
def cancel_delivery(delivery_id):
    delivery = Delivery.query.get_or_404(delivery_id)
    if delivery.customer_id != current_user.id:
        flash('Unauthorized action.', 'danger')
        return redirect(url_for('customer_dashboard'))
    
    if delivery.status != 'Pending' or delivery.driver_id is not None:
        flash('Cannot cancel this request because it has already been accepted by a driver.', 'warning')
        return redirect(url_for('customer_dashboard'))
    
    db.session.delete(delivery)
    db.session.commit()
    flash('Delivery request cancelled successfully.', 'success')
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
                flash('Thank you for your feedback!', 'success')
            else:
                flash('Please select a rating', 'warning')
        except (ValueError, TypeError):
            flash('Invalid rating value', 'danger')
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
        rates = {'car': 250, 'van': 350, 'truck': 500}
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
            pickup_otp=generate_otp(),
            delivery_otp=generate_otp(),
            status='Pending'
        )
        
        db.session.add(new_delivery)
        db.session.commit()
        
        save_notification(current_user.id, f"Your delivery request to {dropoff_loc} has been successfully booked. Cost: {total_cost} XAF")
        
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
    rates = {'car': 250, 'van': 350, 'truck': 500}
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
    
    # Separation: Delivered but not paid, vs Delivered and fully Paid (History)
    unpaid_jobs = Delivery.query.filter_by(driver_id=current_user.id, status='Delivered').filter(Delivery.payment_status != 'Paid').all()
    history_jobs = Delivery.query.filter_by(driver_id=current_user.id, status='Delivered').filter(Delivery.payment_status == 'Paid').all()
    
    total_earnings = sum(job.total_cost for job in history_jobs)
    
    return render_template('driver/dashboard.html', 
                           active_job=active_job, 
                           unpaid_jobs=unpaid_jobs,
                           history_jobs=history_jobs,
                           completed_count=len(history_jobs), 
                           earnings=total_earnings)

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
        otp_code = request.form.get('otp_code', '').strip()
        
        if new_status == 'Picked Up' and otp_code != delivery.pickup_otp:
            flash('Invalid Pickup OTP. Please ask the customer for the correct code.', 'danger')
            return redirect(url_for('driver_dashboard'))
        
        if new_status == 'Delivered' and otp_code != delivery.delivery_otp:
            flash('Invalid Delivery OTP. Please ask the customer for the correct code.', 'danger')
            return redirect(url_for('driver_dashboard'))
            
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

@app.route('/admin/driver/reject/<int:user_id>')
@login_required
def reject_driver(user_id):
    if current_user.role != 'admin':
        return redirect(url_for('index'))
    user = User.query.get_or_404(user_id)
    if user.role == 'driver':
        name = user.full_name
        # Delete associated files if they exist
        for attr in ['id_card_url', 'license_url', 'selfie_url']:
            file_url = getattr(user, attr)
            if file_url:
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], file_url)
                if os.path.exists(file_path):
                    os.remove(file_path)
        
        db.session.delete(user)
        db.session.commit()
        flash(f'Driver {name} application rejected and account removed.', 'warning')
    return redirect(url_for('admin_pending_drivers'))

@app.route('/driver/mark_paid/<int:delivery_id>', methods=['POST'])
@login_required
def mark_paid(delivery_id):
    if current_user.role != 'driver':
        return redirect(url_for('index'))
    delivery = Delivery.query.get_or_404(delivery_id)
    if delivery.driver_id == current_user.id:
        delivery.payment_status = 'Paid'
        delivery.payment_method = 'Cash'
        
        # Credit driver wallet
        if not current_user.wallet:
            current_user.wallet = Wallet(user_id=current_user.id)
        current_user.wallet.balance += delivery.total_cost
        current_user.wallet.total_earned += delivery.total_cost
        
        db.session.commit()
        save_notification(delivery.customer_id, f"The driver confirmed receipt of {delivery.total_cost} XAF in cash for delivery #{delivery.id}. Thank you!")
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
        rates = {'car': 250, 'van': 350, 'truck': 500}
        total_cost = base_fare + (rates.get(delivery.vehicle_type, 250) * effective_distance)
        
        if request.form.get('heavy_goods'): total_cost += 1000
        if request.form.get('fragile_goods'): total_cost += 500
        if request.form.get('urgent_delivery'): total_cost += 1000
        
        delivery.total_cost = total_cost
        db.session.commit()
        
        flash('Delivery request updated successfully!')
        return redirect(url_for('customer_dashboard'))

    return render_template('customer/edit_book.html', delivery=delivery)

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

