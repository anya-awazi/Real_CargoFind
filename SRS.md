# System Requirements Specification (SRS) - CargoFind

## 1. Introduction

### 1.1 Purpose
The purpose of this document is to define the functional and non-functional requirements of the **CargoFind** platform, a logistics and delivery system designed to connect customers with drivers for seamless goods transport across Cameroon.

### 1.2 Scope
CargoFind is a web-based application built with Flask and SocketIO. It facilitates:
- **Delivery Booking**: Interactive map-based pickup and drop-off selection.
- **Real-Time Tracking**: Live location updates via SocketIO and Leaflet.js.
- **Driver Management**: Job acceptance, earnings tracking, and profile verification.
- **Administrative Control**: Unified operations monitoring and user management.

### 1.3 Definitions and Acronyms
- **SRS**: System Requirements Specification
- **OTP**: One-Time Password
- **MoMo**: Mobile Money (Local payment system)
- **SocketIO**: Real-time bidirectional communication engine
- **GIS**: Geographic Information System (Map-based features)

---

## 2. Overall Description

### 2.1 Product Perspective
CargoFind is a standalone web application designed for desktop and mobile browsers. It integrates with mapping services (OpenStreetMap via Leaflet.js) and email services (SMTP) for transactional notifications.

### 2.2 Product Functions
- **Authentication**: Multi-role registration (Customer, Driver) with admin approval for drivers.
- **Logistics**: Distance calculation, cost estimation, and delivery lifecycle management.
- **Finance**: Driver wallet system and automated invoice generation.
- **Communications**: Real-time notifications and broadcast email system.

### 2.3 User Classes and Characteristics
- **Customers**: Individuals or businesses requiring delivery services.
- **Drivers**: Verified vehicle owners seeking delivery jobs.
- **Administrators**: System operators managing users, fleet, and operations.

### 2.4 Operating Environment
- **Server**: Python 3.8+, Flask, SQLite (Database), SocketIO (Real-time).
- **Client**: Modern web browsers (Chrome, Firefox, Safari, Edge) on Desktop and Mobile.
- **Deployment**: Compatible with Gunicorn and Eventlet/Gevent-WebSocket for production.

### 2.5 Constraints
- Requires stable internet connection for real-time tracking.
- Driver accounts require manual administrative approval before job acceptance.
- Default database is SQLite (upgrade to PostgreSQL recommended for high-scale production).

---

## 3. System Features

### 3.1 Authentication & Security
- **Registration**: Users choose role (Customer/Driver) during signup.
- **Login**: Email/password authentication with session persistence.
- **Role-Based Access Control (RBAC)**: Strict separation between Customer, Driver, and Admin dashboards.
- **Account Verification**: Drivers must upload ID and License for admin review.

### 3.2 Customer Module
- **Booking Flow**: Pick locations on map -> Select Vehicle (Car/Van/Truck) -> Enter Goods details -> Get Quote -> Confirm.
- **Live Tracking**: View driver's real-time position on a map after job acceptance.
- **History**: Dashboard for active and past deliveries with status tracking.
- **Invoicing**: Automatic PDF generation for completed deliveries.

### 3.3 Driver Module
- **Job Pool**: View available jobs in real-time with pickup/drop-off details.
- **Job Workflow**: Accept Job -> Mark Picked Up -> Mark Delivered.
- **Location Updates**: Periodic background coordinate transmission to server.
- **Wallet**: Track earnings per delivery and view transaction history.

### 3.4 Administrative Module
- **Command Center**: Dashboard with global stats (Users, Revenue, Active Deliveries).
- **Operations Map**: Unified view of all active deliveries across the network.
- **User Management**: Approve/Suspend/Delete users; Role management.
- **Broadcasting**: Send mass emails to specific user categories.

### 3.5 Real-Time Communication
- **Notifications**: Instant pop-up alerts for status changes (e.g., "Driver has arrived").
- **Live Sync**: Latency-optimized coordinate broadcasting via SocketIO rooms.

---

## 4. External Interface Requirements

### 4.1 User Interfaces
- **Responsive Web Design**: Bootstrap 5 based frontend for accessibility on mobile and desktop.
- **Interactive Maps**: Leaflet.js integration for coordinate picking and tracking.
- **Visual Feedback**: FontAwesome 6 icons and Toast/Flash messages for user feedback.

### 4.2 Software Interfaces
- **Database**: SQLAlchemy ORM for database abstraction.
- **Email**: SMTP integration for transactional and marketing emails.
- **Images**: PIL/Pillow for image compression on document uploads.
- **PDF**: ReportLab for on-the-fly invoice generation.

---

## 5. Non-Functional Requirements

### 5.1 Performance
- Page load time < 2 seconds for core dashboards.
- Map update frequency: 10-30 seconds depending on network stability.

### 5.2 Security
- Password hashing using Werkzeug `security`.
- CSRF protection for all forms.
- Secure OTP-based handover for deliveries (Pickup/Delivery validation).

### 5.3 Availability
- Designed for 99.9% uptime in production environments.
- Fallback mechanisms for email delivery failures.

### 5.4 Maintainability
- Modular project structure: `app.py` (logic), `models.py` (data), `templates/` (UI).
- Clear separation of concerns between roles and features.
