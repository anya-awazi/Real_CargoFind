import os
import logging
import random
import string
from datetime import datetime
from dotenv import load_dotenv
# Explicitly load .env from current directory
basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import db, User, Delivery, Notification, Wallet
from sqlalchemy import or_
from werkzeug.security import generate_password_hash
from werkzeug.utils import secure_filename
from flask_socketio import SocketIO, emit, join_room, leave_room
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from PIL import Image
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors

def compress_image(image_path, quality=60, max_size=(800, 800)):
    """
    Compresses an image to save space and potentially resizes it.
    """
    try:
        img = Image.open(image_path)
        # Convert RGBA to RGB if necessary (e.g., for PNG to JPG)
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        
        # Resize image while maintaining aspect ratio
        img.thumbnail(max_size, Image.Resampling.LANCZOS)
        
        # Save compressed version (overwrite original or save as new)
        # If the original was not a JPG, we might want to save it as JPG for better compression
        # But here we'll just overwrite the original path
        img.save(image_path, "JPEG", optimize=True, quality=quality)
        return True
    except Exception as e:
        print(f"Compression error: {e}")
        return False

def send_email(sender, receiver, subject, body):
    """
    Utility function to send emails using SMTP.
    Configure EMAIL_USER and EMAIL_PASSWORD in .env for this to work.
    """
    msg = MIMEMultipart()
    msg['From'] = sender
    msg['To'] = receiver
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    smtp_host = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
    smtp_port = int(os.getenv('EMAIL_PORT', 587))
    smtp_user = os.getenv('EMAIL_USER')
    smtp_pass = os.getenv('EMAIL_PASSWORD')

    if not smtp_user or not smtp_pass:
        raise Exception("Email credentials not configured in .env")

    with smtplib.SMTP(smtp_host, smtp_port) as server:
        server.starttls()
        server.login(smtp_user, smtp_pass)
        server.send_message(msg)

app = Flask(__name__)

# Configure Logging for Render
logging.basicConfig(level=logging.INFO)
logger = app.logger

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
    if current_user.is_authenticated:
        if current_user.role == 'admin':
            return redirect(url_for('admin_dashboard'))
        elif current_user.role == 'driver':
            return redirect(url_for('driver_dashboard'))
        else:
            return redirect(url_for('customer_dashboard'))
    return render_template('index.html')

@app.route('/testimonials')
def testimonials():
    return render_template('testimonials.html')

@app.route('/terms')
def terms():
    return render_template('terms.html')

@app.route('/privacy')
def privacy():
    return render_template('privacy.html')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        subject = request.form.get('subject')
        message_body = request.form.get('message')
        
        # Email configuration
        sender_email = "anya.awaziakuru@ictuniversity.edu.cm"
        receiver_email = "anya.awaziakuru@ictuniversity.edu.cm"
        # Try both os.environ and explicit load_dotenv check
        password = os.getenv('EMAIL_PASSWORD')
        print(f"DEBUG: EMAIL_PASSWORD loaded: {'Yes' if password else 'No'}")
        print(f"DEBUG: EMAIL_PASSWORD length: {len(password) if password else 0}")
        
        # Create message
        msg = MIMEMultipart()
        msg['From'] = email
        msg['To'] = receiver_email
        msg['Subject'] = f"CargoFind Support: {subject}"
        
        body = f"Name: {name}\nEmail: {email}\n\nMessage:\n{message_body}"
        msg.attach(MIMEText(body, 'plain'))
        
        try:
            if not password or password == 'YOUR_APP_PASSWORD_HERE':
                print("DEBUG: EMAIL_PASSWORD not set or using placeholder. Please generate a Gmail App Password.")
                flash('Email configuration error. Please contact the administrator.', 'danger')
                return redirect(url_for('contact'))

            # Use SSL for better reliability with Gmail
            server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
            server.login(sender_email, password)
            server.send_message(msg)
            server.quit()
            flash('Thank you! Your message has been sent successfully.', 'success')
                
        except smtplib.SMTPAuthenticationError as e:
            print(f"Authentication error: {e}")
            flash('Email authentication failed. Please check the email configuration.', 'danger')
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
        
        # Validate password length
        if len(password) < 6:
            flash('Password must be at least 6 characters.', 'danger')
            return redirect(url_for('register'))
        
        user_exists = User.query.filter((User.email == email) | (User.phone == phone)).first()
        if user_exists:
            flash('Email or phone already exists')
            return redirect(url_for('register'))
        
        new_user = User(email=email, phone=phone, full_name=full_name, role=role)
        new_user.set_password(password)
        
        # Generate Registration OTP
        reg_otp = ''.join(random.choices(string.digits, k=6))
        new_user.registration_otp = reg_otp
        
        if role == 'driver':
            new_user.vehicle_type = request.form.get('vehicle_type')
            new_user.vehicle_id = request.form.get('vehicle_id')
            
            # Handle document uploads
            license_file = request.files.get('license')
            
            if not license_file:
                flash('Please upload your driver\'s license.', 'danger')
                return redirect(url_for('register'))
            
            # Save License
            lic_ext = license_file.filename.split('.')[-1]
            lic_filename = secure_filename(f"driver_{email}_license.{lic_ext}")
            lic_path = os.path.join(app.config['UPLOAD_FOLDER'], lic_filename)
            license_file.save(lic_path)
            compress_image(lic_path) # Compress uploaded License
            new_user.license_url = lic_filename
            
            new_user.is_verified = True
            new_user.is_approved = False # Still needs admin approval
            
            # Initialize wallet for driver
            wallet = Wallet(user=new_user)
            db.session.add(wallet)
        
        db.session.add(new_user)
        db.session.commit()
        
        # Send OTP email
        try:
            sender = os.getenv('EMAIL_USER')
            subject = "CargoFind - Verify Your Account"
            body = f"Hello {new_user.full_name},\n\nYour account has been created. To activate it, please enter the following OTP: {reg_otp}\n\nThank you for choosing CargoFind!"
            send_email(sender, new_user.email, subject, body)
            flash('Registration successful! Please check your email for the verification code.')
        except Exception as e:
            logger.error(f"Failed to send registration OTP to {new_user.email}: {e}")
            flash('Account created but failed to send verification email. Please try logging in to resend.')

        return redirect(url_for('verify_otp', user_id=new_user.id))
        
    return render_template('register.html')

@app.route('/verify-otp/<int:user_id>', methods=['GET', 'POST'])
def verify_otp(user_id):
    user = User.query.get_or_404(user_id)
    if user.is_active:
        flash('Account already active. Please login.')
        return redirect(url_for('login'))
        
    if request.method == 'POST':
        otp_input = request.form.get('otp').strip()
        if otp_input == user.registration_otp:
            user.is_active = True
            user.registration_otp = None # Clear OTP
            db.session.commit()
            flash('Account verified successfully! You can now log in.', 'success')
            return redirect(url_for('login'))
        else:
            flash('Invalid OTP. Please try again.', 'danger')
            
    return render_template('verify_otp.html', user_id=user_id)

@app.route('/resend-otp/<int:user_id>')
def resend_otp(user_id):
    user = User.query.get_or_404(user_id)
    if user.is_active:
        return redirect(url_for('login'))
        
    reg_otp = ''.join(random.choices(string.digits, k=6))
    user.registration_otp = reg_otp
    db.session.commit()
    
    try:
        sender = os.getenv('EMAIL_USER')
        subject = "CargoFind - Your New Verification Code"
        body = f"Hello {user.full_name},\n\nYour new verification code is: {reg_otp}\n\nThank you for choosing CargoFind!"
        send_email(sender, user.email, subject, body)
        flash('New verification code sent to your email.')
    except Exception as e:
        logger.error(f"Failed to resend registration OTP to {user.email}: {e}")
        flash('Failed to send email. Please try again later.')
        
    return redirect(url_for('verify_otp', user_id=user_id))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        identifier = request.form.get('email', '').strip().lower()
        password = request.form.get('password')
        
        user = User.query.filter((User.email == identifier) | (User.phone == identifier)).first()
        
        if user and user.check_password(password):
            if not user.is_active:
                flash('Your account is not yet verified. Please enter the OTP sent to your email.')
                return redirect(url_for('verify_otp', user_id=user.id))
                
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

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        user = User.query.filter_by(email=email).first()
        
        if user:
            # Generate reset token
            token = user.get_reset_token(app.config['SECRET_KEY'])
            reset_url = url_for('reset_password', token=token, _external=True)
            
            # Send reset email
            sender_email = os.getenv('EMAIL_USER')
            subject = 'CargoFind - Password Reset Request'
            body = f"""
            Hello {user.full_name},
            
            We received a request to reset your CargoFind password.
            
            Click the link below to reset your password:
            {reset_url}
            
            This link will expire in 30 minutes.
            
            If you didn't request this, please ignore this email.
            
            Best regards,
            CargoFind Team
            """
            
            try:
                send_email(sender_email, user.email, subject, body)
                flash('Password reset link has been sent to your email.', 'success')
            except Exception as e:
                logger.error(f"Error sending reset email: {str(e)}")
                flash(f'Failed to send reset email. Please contact support.', 'danger')
        else:
            # Don't reveal if email exists or not for security
            flash('If an account exists with this email, a reset link has been sent.', 'info')
        
        return redirect(url_for('login'))
    
    return render_template('forgot_password.html')

@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    user_id = User.verify_reset_token(token, app.config['SECRET_KEY'])
    
    if user_id is None:
        flash('Invalid or expired reset token. Please request a new password reset.', 'danger')
        return redirect(url_for('forgot_password'))
    
    user = User.query.get(user_id)
    
    if request.method == 'POST':
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('reset_password.html', token=token)
        
        if len(password) < 6:
            flash('Password must be at least 6 characters.', 'danger')
            return render_template('reset_password.html', token=token)
        
        user.set_password(password)
        try:
            db.session.commit()
            flash('Your password has been reset successfully. Please login with your new password.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error resetting password for user {user.id}: {str(e)}")
            flash('An error occurred while resetting your password. Please try again.', 'danger')
            return render_template('reset_password.html', token=token)
    
    return render_template('reset_password.html', token=token)

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

@app.route('/customer/accept_driver/<int:delivery_id>')
@login_required
def accept_driver(delivery_id):
    delivery = Delivery.query.get_or_404(delivery_id)
    if delivery.customer_id != current_user.id:
        flash('Unauthorized action.', 'danger')
        return redirect(url_for('customer_dashboard'))
    
    if delivery.status == 'Driver Accepted':
        delivery.status = 'Accepted'
        db.session.commit()
        
        # Notify driver
        save_notification(delivery.driver_id, f'Customer {current_user.full_name} accepted you for the job! You can now start the delivery.')
        flash('Driver confirmed! They have been notified.', 'success')
        
    return redirect(url_for('customer_dashboard'))

@app.route('/customer/reject_driver/<int:delivery_id>')
@login_required
def customer_reject_driver(delivery_id):
    delivery = Delivery.query.get_or_404(delivery_id)
    if delivery.customer_id != current_user.id:
        flash('Unauthorized action.', 'danger')
        return redirect(url_for('customer_dashboard'))
    
    if delivery.status == 'Driver Accepted':
        old_driver_id = delivery.driver_id
        delivery.driver_id = None
        delivery.status = 'Pending'
        db.session.commit()
        
        # Notify driver
        save_notification(old_driver_id, f'Customer {current_user.full_name} chose another driver for delivery #{delivery.id}.')
        flash('Driver rejected. Your job is back on the market.', 'info')
        
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
        total_cost = int(base_fare + (rates.get(vehicle_type, 250) * effective_distance))
        
        if request.form.get('heavy_goods'): total_cost += 1000
        if request.form.get('fragile_goods'): total_cost += 500
        if request.form.get('urgent_delivery'): total_cost += 1000
        
        # Parse pickup date and time
        pickup_date_str = request.form.get('pickup_date')
        pickup_time_str = request.form.get('pickup_time')
        dropoff_time_str = request.form.get('dropoff_time')
        
        pickup_dt = None
        if pickup_date_str and pickup_time_str:
            try:
                pickup_dt = datetime.strptime(f"{pickup_date_str} {pickup_time_str}", "%Y-%m-%d %H:%M")
            except ValueError:
                pickup_dt = datetime.utcnow()
        else:
            pickup_dt = datetime.utcnow()
            
        dropoff_dt = None
        if pickup_date_str and dropoff_time_str:
            try:
                # Assuming dropoff is on the same day for simplicity, or we could add dropoff_date
                dropoff_dt = datetime.strptime(f"{pickup_date_str} {dropoff_time_str}", "%Y-%m-%d %H:%M")
            except ValueError:
                pass

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
            pickup_time=pickup_dt,
            dropoff_time=dropoff_dt,
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
    total_cost = int(base_fare + (rates.get(vehicle_type, 250) * effective_distance))
    
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
    
    active_jobs = Delivery.query.filter_by(driver_id=current_user.id).filter(Delivery.status != 'Delivered').all()
    
    # Separation: Delivered but not paid, vs Delivered and fully Paid (History)
    unpaid_jobs = Delivery.query.filter_by(driver_id=current_user.id, status='Delivered').filter(Delivery.payment_status != 'Paid').all()
    history_jobs = Delivery.query.filter_by(driver_id=current_user.id, status='Delivered').filter(Delivery.payment_status == 'Paid').all()
    
    total_earnings = int(sum(job.total_cost for job in history_jobs))
    
    return render_template('driver/dashboard.html', 
                           active_jobs=active_jobs, 
                           unpaid_jobs=unpaid_jobs,
                           history_jobs=history_jobs,
                           completed_count=len(history_jobs), 
                           earnings=total_earnings)

@app.route('/driver/invoice/<int:delivery_id>')
@login_required
def download_invoice(delivery_id):
    if current_user.role != 'driver':
        return redirect(url_for('index'))
    
    job = Delivery.query.get_or_404(delivery_id)
    if job.driver_id != current_user.id:
        flash("You do not have permission to access this invoice.")
        return redirect(url_for('driver_dashboard'))
    
    # Create a file-like buffer to receive PDF data.
    buffer = io.BytesIO()

    # Create the PDF object, using the buffer as its "file."
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    # --- Header with Blue Background ---
    p.setFillColorRGB(0.05, 0.43, 0.99)  # #0d6efd approx
    p.rect(0, height - 120, width, 120, fill=1, stroke=0)
    
    p.setFillColor(colors.white)
    p.setFont("Helvetica-Bold", 28)
    p.drawString(50, height - 60, "CargoFind")
    
    p.setFont("Helvetica", 12)
    p.drawString(50, height - 85, "Fast & Reliable Logistics in Cameroon")
    
    p.setFont("Helvetica-Bold", 14)
    p.drawRightString(width - 50, height - 60, "INVOICE")
    
    # --- Invoice Details Section ---
    p.setFillColor(colors.black)
    p.setFont("Helvetica-Bold", 10)
    p.drawString(50, height - 150, "INVOICE NUMBER")
    p.drawString(width/2 + 50, height - 150, "DATE")
    
    p.setFont("Helvetica", 12)
    p.drawString(50, height - 170, f"#CF-{job.id}")
    p.drawString(width/2 + 50, height - 170, job.created_at.strftime('%B %d, %Y'))
    
    p.setStrokeColor(colors.lightgrey)
    p.line(50, height - 185, width - 50, height - 185)
    
    # --- Locations Section ---
    y = height - 210
    p.setFont("Helvetica-Bold", 10)
    p.setFillColor(colors.grey)
    p.drawString(50, y, "PICKUP LOCATION")
    p.drawString(width/2 + 50, y, "DELIVERY LOCATION")
    
    y -= 20
    p.setFont("Helvetica", 11)
    p.setFillColor(colors.black)
    
    # Handle long addresses with simple wrapping
    pickup_text = job.pickup_location
    if len(pickup_text) > 40: pickup_text = pickup_text[:37] + "..."
    p.drawString(50, y, pickup_text)
    
    dropoff_text = job.dropoff_location
    if len(dropoff_text) > 40: dropoff_text = dropoff_text[:37] + "..."
    p.drawString(width/2 + 50, y, dropoff_text)
    
    y -= 25
    p.line(50, y, width - 50, y)
    
    # --- Parties Section ---
    y -= 25
    p.setFont("Helvetica-Bold", 10)
    p.setFillColor(colors.grey)
    p.drawString(50, y, "CUSTOMER")
    p.drawString(width/2 + 50, y, "TRANSPORTER")
    
    y -= 20
    p.setFont("Helvetica-Bold", 11)
    p.setFillColor(colors.black)
    p.drawString(50, y, job.customer.full_name)
    p.drawString(width/2 + 50, y, job.driver.full_name)
    
    y -= 15
    p.setFont("Helvetica", 10)
    p.setFillColor(colors.darkgrey)
    p.drawString(50, y, job.customer.phone)
    p.drawString(width/2 + 50, y, f"{job.driver.vehicle_type.capitalize()} - {job.driver.vehicle_id}")
    
    y -= 12
    p.drawString(50, y, job.customer.email)
    p.drawString(width/2 + 50, y, job.driver.phone)
    
    y -= 25
    p.line(50, y, width - 50, y)
    
    # --- Table Header ---
    y -= 30
    p.setFillColorRGB(0.97, 0.98, 0.98) # #f8f9fa
    p.rect(50, y - 5, width - 100, 25, fill=1, stroke=0)
    
    p.setFillColor(colors.grey)
    p.setFont("Helvetica-Bold", 10)
    p.drawString(60, y + 5, "DESCRIPTION")
    p.drawString(width - 250, y + 5, "DISTANCE")
    p.drawRightString(width - 60, y + 5, "AMOUNT")
    
    # --- Table Body ---
    y -= 35
    p.setFillColor(colors.black)
    p.setFont("Helvetica-Bold", 11)
    p.drawString(60, y, "Cargo Delivery Service")
    p.setFont("Helvetica", 10)
    p.drawString(width - 250, y, f"{job.distance_km} km")
    p.drawRightString(width - 60, y, f"{job.total_cost:,.0f} XAF")
    
    y -= 15
    p.setFillColor(colors.grey)
    p.setFont("Helvetica", 9)
    p.drawString(60, y, "Standard delivery service")
    
    # --- Total Section ---
    y -= 50
    p.setFillColorRGB(0.97, 0.98, 0.98) # #f8f9fa
    p.rect(50, y - 15, width - 100, 45, fill=1, stroke=0)
    
    p.setFillColor(colors.black)
    p.setFont("Helvetica-Bold", 12)
    p.drawString(60, y + 5, "Total Amount")
    
    p.setFillColorRGB(0.05, 0.43, 0.99)
    p.setFont("Helvetica-Bold", 20)
    p.drawRightString(width - 60, y, f"{job.total_cost:,.0f} XAF")
    
    # --- Status Section ---
    y -= 60
    status = job.payment_status.upper()
    if status == 'PAID':
        p.setFillColorRGB(0.82, 0.91, 0.87) # light green
    else:
        p.setFillColorRGB(1.0, 0.95, 0.8) # light yellow
        
    p.roundRect(width/2 - 60, y, 120, 25, 12, fill=1, stroke=0)
    
    if status == 'PAID':
        p.setFillColorRGB(0.06, 0.32, 0.2) # dark green
    else:
        p.setFillColorRGB(0.4, 0.3, 0.0) # dark yellow
        
    p.setFont("Helvetica-Bold", 10)
    p.drawCentredString(width/2, y + 8, f"STATUS: {status}")
    
    # --- Footer ---
    p.setFillColor(colors.grey)
    p.setFont("Helvetica-Oblique", 10)
    p.drawCentredString(width/2, 50, "Thank you for choosing CargoFind for your logistics needs!")

    # Close the PDF object cleanly, and we're done.
    p.showPage()
    p.save()

    # FileResponse sets the Content-Disposition header.
    # as_attachment=False allows the browser to show the PDF in a viewer.
    buffer.seek(0)
    return send_file(buffer, as_attachment=False, mimetype='application/pdf')

@app.route('/driver/jobs')
@login_required
def available_jobs():
    if current_user.role != 'driver':
        return redirect(url_for('index'))
    
    if not current_user.is_approved:
        flash('You must be approved by an administrator before you can accept jobs.')
        return redirect(url_for('driver_dashboard'))
    
    # Get filter parameters
    query = request.args.get('q', '')
    filter_date = request.args.get('date', '')
    sort_by = request.args.get('sort', 'newest')
    vtype = request.args.get('vtype', '')

    # Base query: Pending jobs
    jobs_query = Delivery.query.filter(Delivery.status == 'Pending')

    # Filter by vehicle type
    if vtype == 'all':
        # Show all jobs regardless of vehicle type
        pass
    elif vtype:
        # Show specific vehicle type or general jobs
        jobs_query = jobs_query.filter(or_(Delivery.vehicle_type == vtype, Delivery.vehicle_type == None))
    else:
        # Default: Filter by driver's own vehicle type or general jobs
        jobs_query = jobs_query.filter(or_(Delivery.vehicle_type == current_user.vehicle_type, Delivery.vehicle_type == None))

    # Search by location or goods
    if query:
        jobs_query = jobs_query.filter(
            or_(
                Delivery.pickup_location.ilike(f'%{query}%'),
                Delivery.dropoff_location.ilike(f'%{query}%'),
                Delivery.goods_description.ilike(f'%{query}%')
            )
        )

    # Filter by date
    if filter_date:
        try:
            # Match only the date part of pickup_time
            date_obj = datetime.strptime(filter_date, '%Y-%m-%d').date()
            jobs_query = jobs_query.filter(db.func.date(Delivery.pickup_time) == date_obj)
        except ValueError:
            pass

    # Sorting
    if sort_by == 'price_high':
        jobs_query = jobs_query.order_by(Delivery.total_cost.desc())
    elif sort_by == 'weight_high':
        jobs_query = jobs_query.order_by(Delivery.weight.desc())
    elif sort_by == 'distance_short':
        jobs_query = jobs_query.order_by(Delivery.distance_km.asc())
    else: # newest
        jobs_query = jobs_query.order_by(Delivery.created_at.desc())

    all_jobs = jobs_query.all()
    return render_template('driver/jobs.html', jobs=all_jobs)

@app.route('/driver/accept/<int:delivery_id>')
@login_required
def accept_job(delivery_id):
    if current_user.role != 'driver':
        return redirect(url_for('index'))
    
    delivery = Delivery.query.get_or_404(delivery_id)
    if delivery.status == 'Pending':
        delivery.driver_id = current_user.id
        delivery.status = 'Driver Accepted'
        db.session.commit()
        flash('Interest expressed! Waiting for customer to confirm.')
        
        # Notify customer
        notif = Notification(user_id=delivery.customer_id, 
                             message=f'Driver {current_user.full_name} (Rating: {current_user.average_rating}) wants to take your job. Please confirm.',
                             link=url_for('customer_dashboard'))
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
    total_drivers = User.query.filter_by(role='driver', is_approved=True).count()
    pending_drivers = User.query.filter_by(role='driver', is_approved=False).count()
    
    active_deliveries = Delivery.query.filter(Delivery.status != 'Delivered').order_by(Delivery.id.desc()).all()
    recent_activities = Delivery.query.order_by(Delivery.id.desc()).limit(5).all()
    completed_deliveries = Delivery.query.filter_by(status='Delivered').all()
    
    total_revenue = int(sum(d.total_cost for d in completed_deliveries if d.payment_status == 'Paid'))
    
    return render_template('admin/dashboard.html', 
                           total_users=total_users, 
                           total_customers=total_customers,
                           total_drivers=total_drivers,
                           pending_drivers_count=pending_drivers,
                           active_count=len(active_deliveries),
                           completed_count=len(completed_deliveries),
                           revenue=total_revenue,
                           active_deliveries=active_deliveries,
                           recent_activities=recent_activities)

@app.route('/admin/users')
@login_required
def admin_users():
    if current_user.role != 'admin':
        return redirect(url_for('index'))
    
    query = request.args.get('q', '')
    role_filter = request.args.get('role', '')
    
    user_query = User.query
    
    if query:
        user_query = user_query.filter(
            or_(
                User.full_name.ilike(f'%{query}%'),
                User.email.ilike(f'%{query}%'),
                User.phone.ilike(f'%{query}%')
            )
        )
    
    if role_filter:
        user_query = user_query.filter(User.role == role_filter)
        
    users = user_query.order_by(User.id.desc()).all()
    return render_template('admin/users.html', users=users)

@app.route('/admin/deliveries')
@login_required
def admin_deliveries():
    if current_user.role != 'admin':
        return redirect(url_for('index'))
    
    query = request.args.get('q', '')
    status_filter = request.args.get('status', '')
    
    delivery_query = Delivery.query
    
    if query:
        delivery_query = delivery_query.filter(
            or_(
                Delivery.pickup_location.ilike(f'%{query}%'),
                Delivery.dropoff_location.ilike(f'%{query}%'),
                Delivery.goods_description.ilike(f'%{query}%')
            )
        )
    
    if status_filter:
        delivery_query = delivery_query.filter(Delivery.status == status_filter)
        
    deliveries = delivery_query.order_by(Delivery.id.desc()).all()
    return render_template('admin/deliveries.html', deliveries=deliveries)

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

@app.route('/admin/user/delete/<int:user_id>')
@login_required
def delete_user(user_id):
    if current_user.role != 'admin':
        return redirect(url_for('index'))
    
    user = User.query.get_or_404(user_id)
    
    # Prevent deleting admin users
    if user.role == 'admin':
        flash('Cannot delete admin users.')
        return redirect(url_for('admin_users'))
    
    user_name = user.full_name
    
    # Delete driver files if they exist
    if user.role == 'driver':
        for attr in ['license_url']:
            file_url = getattr(user, attr)
            if file_url:
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], file_url)
                if os.path.exists(file_path):
                    os.remove(file_path)
    
    # Delete related notifications
    Notification.query.filter_by(user_id=user.id).delete()
    
    # Delete wallet if exists
    Wallet.query.filter_by(user_id=user.id).delete()
    
    # Set driver_id to NULL for deliveries (cascade)
    Delivery.query.filter_by(driver_id=user.id).update({'driver_id': None})
    
    # Delete the user (deliveries as customer will cascade)
    db.session.delete(user)
    db.session.commit()
    
    flash(f'User {user_name} has been deleted.')
    return redirect(url_for('admin_users'))

@app.route('/admin/drivers/pending')
@login_required
def admin_pending_drivers():
    if current_user.role != 'admin':
        return redirect(url_for('index'))
    
    query = request.args.get('q', '')
    
    driver_query = User.query.filter_by(role='driver', is_approved=False)
    
    if query:
        driver_query = driver_query.filter(
            or_(
                User.full_name.ilike(f'%{query}%'),
                User.email.ilike(f'%{query}%'),
                User.phone.ilike(f'%{query}%')
            )
        )
        
    pending_drivers = driver_query.order_by(User.id.desc()).all()
    return render_template('admin/pending_drivers.html', drivers=pending_drivers)

@app.route('/admin/send_email', methods=['GET', 'POST'])
@login_required
def admin_send_email():
    if current_user.role != 'admin':
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        recipient_type = request.form.get('recipient_type')
        subject = request.form.get('subject')
        message_body = request.form.get('message')
        
        # Determine recipients
        if recipient_type == 'customer':
            recipients = User.query.filter_by(role='customer').all()
        elif recipient_type == 'driver':
            recipients = User.query.filter_by(role='driver').all()
        else:
            recipients = User.query.filter(User.role != 'admin').all()
            
        if not recipients:
            flash('No recipients found for the selected group.', 'warning')
            return redirect(url_for('admin_send_email'))
            
        # Send emails
        sender = os.getenv('EMAIL_USER')
        success_count = 0
        fail_count = 0
        
        for user in recipients:
            try:
                # Custom greeting for each user
                personalized_body = f"Hello {user.full_name},\n\n{message_body}\n\nBest regards,\nCargoFind Admin Team"
                send_email(sender, user.email, subject, personalized_body)
                success_count += 1
            except Exception as e:
                logger.error(f"Failed to send broadcast email to {user.email}: {e}")
                fail_count += 1
                
        flash(f'Broadcast complete! {success_count} emails sent successfully. {fail_count} failures.', 'success')
        return redirect(url_for('admin_dashboard'))
        
    return render_template('admin/send_email.html')

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
        
        # Parse times
        pickup_date_str = request.form.get('pickup_date')
        pickup_time_str = request.form.get('pickup_time')
        dropoff_time_str = request.form.get('dropoff_time')
        
        if pickup_date_str and pickup_time_str:
            try:
                delivery.pickup_time = datetime.strptime(f"{pickup_date_str} {pickup_time_str}", "%Y-%m-%d %H:%M")
            except ValueError:
                pass
                
        if pickup_date_str and dropoff_time_str:
            try:
                delivery.dropoff_time = datetime.strptime(f"{pickup_date_str} {dropoff_time_str}", "%Y-%m-%d %H:%M")
            except ValueError:
                pass

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

