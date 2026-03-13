# CargoFind - Logistics & Delivery Platform

CargoFind is a fast and reliable logistics platform designed to connect customers with trusted drivers for seamless deliveries across Cameroon.

## Features

### 👤 Customer
- **Book Deliveries**: Schedule pickups and drop-offs with detailed goods descriptions.
- **Live Tracking**: Monitor your delivery in real-time on an interactive map.
- **Dashboard**: Manage active and past deliveries.
- **Invoices**: View and download invoices for completed deliveries.
- **Notifications**: Receive updates on delivery status and payment.

### 🚛 Driver
- **Driver Panel**: View and accept available delivery jobs.
- **Wallet System**: Track earnings and manage balance.
- **Real-time Location**: Update current coordinates for customers to track.
- **Profile Management**: Upload licenses and vehicle details for approval.

### 🛡️ Admin
- **Command Center**: Overview of total users, drivers, and active deliveries.
- **Live Operations Map**: View all active pickups and drop-offs in real-time.
- **User Management**: Approve drivers, suspend/activate accounts, and manage roles.
- **Broadcast System**: Send email notifications to specific user groups.
- **Recent Activities**: Monitor the latest system events with deep-dive capabilities.

## Tech Stack
- **Backend**: Python / Flask
- **Database**: SQLAlchemy (SQLite)
- **Real-time**: Flask-SocketIO
- **Maps**: Leaflet.js / OpenStreetMap
- **Frontend**: Bootstrap 5 / FontAwesome
- **Deployment**: Gunicorn / Eventlet

## Getting Started

### Prerequisites
- Python 3.8+
- Pip (Python Package Manager)

### Installation
1. Clone the repository
2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Set up environment variables in a `.env` file:
   ```env
   SECRET_KEY=your_secret_key
   EMAIL_USER=your_email@gmail.com
   EMAIL_PASSWORD=your_app_password
   ```
5. Run the application:
   ```bash
   python app.py
   ```

## Development
- `models.py`: Database schema and models.
- `app.py`: Main application logic and routes.
- `templates/`: HTML templates organized by user role.
- `static/`: CSS, JavaScript, and uploaded assets.

## License
© 2026 CargoFind Cameroon. All rights reserved.
