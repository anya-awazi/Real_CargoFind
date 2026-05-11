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
Non-functional requirements outline the operational limitations, performance standards, and quality qualities that determine the proper operation of the CargoFind logistics system. Rather than focusing on particular functional behaviors, these criteria cover system security, usability, scalability, and dependability.

### 5.1 Precision and Dependability
The system's capacity to deliver accurate logistics evaluations and sustain steady operation.
- **Estimation Accuracy**: The cost estimation algorithms must calculate delivery fees with an accuracy of 95% based on distance, vehicle type, and cargo weight.
- **Tracking Precision**: Real-time GPS coordinate transmission must maintain a maximum deviation of 10-20 meters to ensure reliable tracking.
- **Availability**: 99.5% system availability must be maintained to support 24/7 delivery operations using automated monitoring tools.

### 5.2 User Experience and Accessibility
The usability, interface design, and accessibility requirements of the system for a range of user demographics.
- **Responsive Design**: The web application must provide a user-friendly interface that adapts seamlessly to desktop, tablet, and mobile platforms.
- **Learning Curve**: Due to consistent design principles and a clear visual hierarchy, the system should require minimal training (less than 15 minutes) for new users.
- **Accessibility**: The system must adhere to accessibility guidelines to ensure usability for people with disabilities.
- **Localization**: Support for regional languages (e.g., English and French) to cater to the diverse Cameroonian demographic.

### 5.3 Effectiveness and Reactivity
Requirements for reaction time, processing efficiency, and system performance for the best possible user experience.
- **Page Performance**: Core dashboards and booking pages should load in less than 2 seconds under standard network conditions.
- **Real-Time Latency**: Coordinate broadcasting via SocketIO must ensure that location updates are reflected on the customer map with less than 3 seconds of latency.
- **Scalability**: The system ought to accommodate hundreds of concurrent active deliveries without sacrificing processing speed.

### 5.4 Security and Privacy Protection
System integrity and user data are safeguarded by extensive cybersecurity controls and data protection procedures.
- **Data Encryption**: All sensitive information, including user credentials and financial records, must be encrypted using Werkzeug security and industry-standard TLS protocols.
- **Access Control**: Strict Role-Based Access Control (RBAC) must ensure that drivers, customers, and admins only access data relevant to their specific permissions.
- **Privacy**: Personal contact information should be masked until a delivery job is officially accepted by a driver.

### 5.5 Fault Tolerance and System Reliability
Error-handling, recovery, and system stability that guarantee ongoing operation.
- **Backup & Recovery**: Automated database backup programs with a Recovery Point Objective (RPO) of 1 hour must be implemented.
- **Error Management**: The platform should implement elegant error management with easily navigable error messages and fallback options for failed API calls or map services.
- **Stability**: The architecture must support redundant deployment to allow for automatic failover in the event of server issues.

### 5.6 Extensibility and Maintainability
A system architecture that facilitates simple feature additions, updates, and revisions.
- **Modular Architecture**: Independent component updates (e.g., adding new payment gateways or vehicle types) must be possible without system-wide outages.
- **Documentation**: Thorough documentation for the database schema, internal APIs, and component logic must be maintained.
- **Testing**: Automated testing frameworks should be utilized to cover unit and integration tests for critical delivery workflows.
- **CI/CD Integration**: Pipelines for continuous integration and version control must be established to streamline deployment and code quality.

---

## 6. System Design

### 6.1 Overview
The system is a comprehensive logistics and delivery platform, **CargoFind**, designed to connect customers with reliable drivers for goods transport. It leverages real-time tracking, interactive mapping, and automated financial management to streamline the delivery process for individuals and businesses across Cameroon.

### 6.2 Architecture of the System
The application's architecture is organized into three distinct layers:

#### 6.2.1 User Interface (Frontend Layer)
- **Technologies**: HTML5, CSS3, JavaScript (ES6+), Bootstrap 5.
- **Components**: Customer Dashboard, Driver Panel, Admin Command Center, Interactive Map (Leaflet.js), Booking Interface, Real-time Notifications, and Wallet Management.
- **Panel Function**: Manages responsive user interfaces and displays real-time data via web browsers on desktop and mobile devices.

#### 6.2.2 Backend Layer (Logic for Applications)
- **Technology**: Python (Flask Framework).
- **Core Features**:
    - **Authentication**: Multi-role registration and login using Flask-Login.
    - **Logistics Engine**: Real-time delivery booking, distance calculation, and cost estimation.
    - **Real-Time Communication**: Bidirectional updates via Flask-SocketIO.
    - **Document Management**: Verification upload handling and image compression (Pillow).
    - **Reporting**: Automated invoice generation (ReportLab).
    - **Email Services**: Transactional alerts and mass broadcasting (SMTP).

#### 6.2.3 Data Management (Data Layer)
- **Technology**: SQLite (via SQLAlchemy ORM).
- **Stored Data**: User profiles (roles, vehicles, verification), delivery records (coordinates, status, OTPs), wallet transactions, system notifications, and audit logs.

### 6.3 Features of Security
- **Password Protection**: Industry-standard hashing using Werkzeug's `security` module.
- **Session Management**: Secure user session tracking and protection against unauthorized access using Flask-Login.
- **Role-Based Access Control (RBAC)**: Strict separation of permissions between Customers, Drivers, and Administrators.
- **Input Validation**: Comprehensive data sanitization to protect against SQL injection and Cross-Site Scripting (XSS).
- **Secure Handover**: OTP-based verification for pickup and delivery to prevent theft or misplacement.

### 6.4 Core Logistics Components
- **Interactive Booking**: Leaflet.js-powered map for precise coordinate selection of pickup and drop-off points.
- **Dynamic Pricing**: Algorithms that calculate costs instantly based on vehicle type, cargo weight, and distance.
- **Live Tracking System**: Real-time coordinate broadcasting using SocketIO rooms for live driver movements.
- **Driver Wallet**: Automated earnings tracking with real-time balance updates and history.
- **Admin Command Center**: Global monitoring of active fleet, revenue tracking, and manual driver approval.

### 6.5 Workflow for the System
1. **Authentication**: Users register/login with role-specific profiles.
2. **Verification**: Drivers upload identification for administrative approval.
3. **Booking**: Customers select locations on the map and confirm delivery details.
4. **Job Acceptance**: Verified drivers view and accept pending jobs.
5. **Transit & Tracking**: Real-time tracking begins; driver marks "Picked Up" using OTP.
6. **Completion**: Driver marks "Delivered" using OTP; automated invoice is generated.
7. **Settlement**: Funds are credited to the driver's wallet and recorded in the system.

### 6.6 Deployment
- **Local Development**: Standard Python virtual environments with SQLite for rapid testing.
- **Production Hosting**: Gunicorn with `eventlet` or `gevent` workers for high-concurrency SocketIO support.
- **Cloud Infrastructure**: Scalable deployment ready for platforms like AWS, Heroku, or Render using environment-specific configurations.

The thorough architectural blueprint specified above ensures a robust, scalable, and secure implementation of the CargoFind platform, aligning with both user needs and technical best practices.

---

## 7. Use Case Diagram

### 7.1 Overview
A Use Case diagram is a graphic depiction that illustrates the various ways in which actors or users interact with the **CargoFind** logistics system. It lists all of the system's features and specifies who is capable of using them. For developers and stakeholders, this diagram is a vital communication tool since it gives a high-level overview of the functions of the system and who uses it.

### 7.2 System Participants

#### 1. Customer
- **Role**: The primary service seeker of the logistics platform.
- **Profile**: Individuals or businesses requiring the transport of goods.
- **Goal**: Successfully book deliveries, track goods in real-time, and manage delivery history.

#### 2. Driver
- **Role**: The service provider responsible for physical logistics.
- **Profile**: Verified vehicle owners (Car, Van, Truck) seeking delivery jobs.
- **Goal**: Accept delivery requests, navigate to locations, and manage personal earnings.

#### 3. Administrator
- **Role**: The system manager with enhanced privileges.
- **Profile**: Operations managers or system overseers.
- **Goal**: Control users, verify driver credentials, monitor global fleet activity, and manage financial records.

### 7.3 Use Cases for Actors

#### Customer Use Cases: Booking & Management
- **Register or Login**: Multi-role authentication for secure access.
- **Book a Delivery**: Interactive map-based selection of pickup and drop-off points.
- **Select Vehicle Type**: Choose between Car, Van, or Truck based on cargo size.
- **Live Tracking**: View driver movements in real-time via SocketIO map integration.
- **View Delivery History**: Track active and completed orders with status updates.
- **Download Invoices**: Access auto-generated PDF records of completed transactions.
- **Provide Feedback**: Rate drivers and provide comments on service quality.

#### Driver Use Cases: Operations & Earnings
- **Verification Upload**: Upload ID and Driver's License for administrative review.
- **View Available Jobs**: Access a real-time pool of pending delivery requests.
- **Manage Delivery Workflow**: One-click actions to mark jobs as "Picked Up" and "Delivered."
- **Coordinate Sync**: Background transmission of GPS coordinates for live tracking.
- **Manage Wallet**: View real-time balance, total earnings, and transaction history.

#### Admin Use Cases: Oversight & Management
- **Manage Users**: Approve, suspend, or delete Customer and Driver accounts.
- **Driver Approval**: Review uploaded documents and grant verified status to drivers.
- **Global Operations Map**: View a unified map of all active deliveries across the network.
- **System Analytics**: Monitor total users, revenue, and fleet activity trends.
- **Mass Broadcasting**: Send automated or manual notifications/emails to specific user groups.
- **Audit Logging**: Review system activity and delivery lifecycle logs.

### 7.4 Relationships between Use Cases
- **Job Acceptance**: A driver's job acceptance automatically triggers a notification to the customer and starts the live tracking session.
- **Secure Handover**: The "Picked Up" and "Delivered" use cases require OTP verification to ensure delivery integrity.
- **Financial Integration**: Marking a job as "Delivered" automatically updates the Driver's Wallet and generates a PDF invoice for the Customer.
- **Verification Dependency**: Access to the "Job Pool" is strictly dependent on the "Driver Approval" use case being completed by an Admin.

### 7.5 Goals and Advantages
- **Functional Range Clarification**: Outlines the features and access rights offered to each specific role.
- **Improving Communication**: Provides technical and non-technical stakeholders with a shared language regarding system flow.
- **Development Roadmap**: Facilitates planning and prioritization of core logistics features.
- **Testing Framework**: Specific test cases (e.g., booking a truck or processing a wallet withdrawal) can be created from each use case.
- **Conditions Verification**: Guarantees that system behavior complies with anticipated user interactions for a seamless logistics experience.

The interactions between the three main characters (Admins, Drivers, and Customers) and the operation of the system are thoroughly mapped out to provide precise instructions for implementation and testing.
