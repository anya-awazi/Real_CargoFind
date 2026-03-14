# CargoFind - Core Functionalities

This document provides a detailed breakdown of the features and capabilities of the CargoFind platform, categorized by user roles and core system modules.

## 1. Authentication & Security
- **Multi-Role Registration**: Users can register as either a **Customer** or **Driver**.
- **Secure Authentication**: Password hashing using Werkzeug.
- **OTP Verification**: (Implemented/Placeholder) for phone/email validation.
- **Login Persistence**: Remembers user sessions via Flask-Login.
- **Access Control**: Role-based redirection (e.g., admins cannot access customer-only routes).
- **Session Protection**: Automatic redirection for unauthenticated users trying to access protected dashboards.

## 2. Customer Features
- **Delivery Booking System**:
    - **Location Selection**: Interactive map (Leaflet) for picking pickup and drop-off points.
    - **Vehicle Options**: Choice of Car, Van, or Truck with dynamic base rates.
    - **Goods Customization**: Specify weight, description, and special requirements (Fragile, Urgent, Heavy).
- **Dynamic Pricing**: Instant cost estimation based on distance (KM) and vehicle/cargo type.
- **Live Tracking**:
    - **Real-time Map**: Visualized route and driver movements via SocketIO.
    - **Status Updates**: From "Pending" to "In Transit" to "Delivered".
- **History & Management**:
    - **Dashboard**: Overview of active and past orders.
    - **Order Editing**: Modify pending requests before a driver accepts them.
    - **Invoice Generation**: Auto-generated PDF-style invoices for record-keeping.
- **Communication**: Integrated notification system for order acceptance, pickups, and completions.

## 3. Driver Features
- **Job Management**:
    - **Driver Panel**: Real-time list of available delivery jobs in the area.
    - **Job Acceptance**: Review pickup/drop-off details before committing.
    - **Delivery Lifecycle**: One-click actions to mark items as "Picked Up" or "Delivered".
- **Driver Wallet**:
    - **Earnings Tracking**: Real-time balance updates after each successful delivery.
    - **Transaction History**: List of all earnings and payments.
- **Tracking Service**:
    - **Location Updates**: Periodic background updates of coordinates sent to the customer's live tracking map via SocketIO.
- **Account Verification**:
    - **Document Upload**: (ID card, Driver's License) for admin review and approval.
    - **Status Tracking**: Visual indicators for "Pending Approval" vs "Approved" status.

## 4. Administrative Command Center
- **System Overview**: High-level stats on total users, total revenue, and active fleet.
- **Live Operations Map**: A unified view of all active deliveries happening across the network.
- **User Management**:
    - **Review & Approval**: Manual approval for new driver registrations.
    - **Account Controls**: Ability to suspend, reactivate, or delete user accounts.
- **Broadcast System**:
    - **Mass Emailing**: Send notifications or updates to all users, all drivers, or all customers simultaneously.
- **Activity Monitoring**:
    - **Audit Log**: A chronological list of recent system events.
    - **Deep Dive**: Detailed view of every delivery's history, route, and participants.

## 5. System Communications
- **Real-time Engine (SocketIO)**:
    - **Instant Notifications**: Pop-up alerts for status changes.
    - **Live Map Sync**: Low-latency coordinate broadcasting between driver and customer.
- **Email System**:
    - **SMTP Integration**: Automated transactional and broadcast emails.
- **Notification Center**: A dedicated UI for users to view their history of system messages.

## 6. Public & Informational
- **Interactive Landing Page**: Introduction to services for new users.
- **Support & Contact**: Dedicated contact forms with email integration.
- **Testimonials**: Community feedback and reviews display.
- **Legal**: Terms of Service and Privacy Policy pages.
