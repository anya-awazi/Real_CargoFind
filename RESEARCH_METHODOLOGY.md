# Research Methodology - CargoFind

This document outlines the systematic approach and technical methodology employed in the research, design, and development of the CargoFind logistics and delivery platform.

## 1. Research Overview

This study describes the methodical technique used to investigate the efficacy of a real-time digital logistics platform in optimizing last-mile delivery services within the Cameroonian context. Given that logistical inefficiencies and lack of transparency account for significant delays and increased costs in regional transport, the research approach was thoughtfully created to address these challenges. This study employs a mixed-methods research design that incorporates both qualitative and quantitative approaches to fully understand user requirements, design real-time tracking modules, and assess their impact on delivery reliability. This approach adheres to the theoretical underpinnings of Supply Chain Management and the Technology Acceptance Model (TAM) covered in the literature review. The methodology includes methods for collecting requirements, procedures for designing and implementing the system, and frameworks for evaluation that gauge delivery efficiency and user satisfaction levels. The research participants, data gathering tools, development process, and ethical considerations are all covered in length in this chapter.

## 2. Research Design

Design Science Research (DSR) is a systematic methodology for creating and evaluating artifacts (e.g., tools, frameworks) to solve real-world problems (Schole & Shepherd, 2019). This study applies DSR to develop **CargoFind**, a real-time digital logistics platform for customers and drivers in Cameroon. The six DSR steps according to (Boluwatife et al., 2025) are:

- **Problem Identification** → Surveys/Focus Groups
- **Objective Definition** → Requirement Analysis
- **Design & Development** → Agile + UML
- **Demonstration** → Prototype Testing
- **Evaluation** → Performance Metrics/User Feedback
- **Communication** → Scholarly Dissemination

### 2.1 Design Science Research Steps

| Design Science Research step | Action                                                                  | Objective                                                | Research Question                                                                                   |
| :--------------------------- | :---------------------------------------------------------------------- | :------------------------------------------------------- | :-------------------------------------------------------------------------------------------------- |
| **Problem Identification**   | Survey stakeholders on logistics challenges in Cameroon.                | Identify core logistics problems and user requirements.  | **RQ1**: What are the key logistical challenges and user requirements in the local delivery market? |
| **Objective Definition**     | Analyze survey data to define platform requirements.                    | Define objectives for CargoFind.                         | **RQ2**: What are the key objectives for designing a real-time logistics platform?                  |
| **Design and Development**   | Develop CargoFind using real-time tracking (SocketIO, Leaflet.js).      | Design and implement the platform based on requirements. | **RQ3**: How can CargoFind be designed to meet real-time delivery and management requirements?      |
| **Demonstration**            | Pilot CargoFind with a focus group (customers and drivers).             | Test prototype functionality and delivery flow.          | **RQ4**: How effective is CargoFind in optimizing delivery coordination?                            |
| **Evaluation**               | Assess platform effectiveness via system performance and user feedback. | Evaluate platform performance.                           | **RQ5**: To what extent does the platform improve delivery transparency and efficiency?             |
| **Communication**            | Publish findings for academia and industry (Pahlavanpour, 2022).        | Disseminate research results.                            |                                                                                                     |

This study will adopt a descriptive research design, integrating both qualitative and quantitative methods to comprehensively explore the effectiveness of a digital platform in logistics optimization. This mixed-methods approach will capture both statistical trends and in-depth insights into user engagement, system reliability, and delivery efficiency.

## 3. Data Collection and Requirements Gathering

### 3.1.1 Research Approach
This study employs a mixed-methods research approach, integrating both qualitative and quantitative methodologies to provide a comprehensive understanding of a digital platform's effectiveness in optimizing logistics and delivery services. The mixed-methods technique allows for triangulation of data, boosting the validity and dependability of conclusions while giving both statistical evidence and rich contextual information (Walter, 2025).

#### 3.1.1.2 Study Area
The study was carried out in Cameroon, a Central/West African country, particularly focusing on major urban logistics hubs like the Center Region (Yaoundé) and the Littoral Region (Douala), targeting the general public including independent drivers and everyday customers. These regions were chosen for this study because of their rapidly growing logistics sector and technology-focused atmosphere, which offers participants a perfect blend of logistical needs and current digital adoption. The well-established mobile network infrastructure in these urban centers guarantees dependable real-time tracking and data collection, and the diverse population with high levels of mobile engagement provides an ideal environment for testing digital logistics solutions. Furthermore, these urban centers are representative of Cameroon's broader trends in technology adoption in the transport sector, so findings may be generalizable to other urban contexts where technical advancements are reshaping traditional services.

Data was collected through:

- **Stakeholder Analysis**: Identifying the distinct needs of three primary user groups:
  - **Customers**: Need ease of booking, transparent pricing, and real-time tracking.
  - **Drivers**: Need efficient job discovery, earnings management, and navigation support.
  - **Administrators**: Need full visibility of operations and user management controls.
- **Competitive Analysis**: Studying existing logistics platforms to identify industry standards and areas for improvement in the local Cameroonian context.
- **Technical Constraints**: Evaluating network reliability and mapping accuracy for regional-specific deployment.

## 4. System Analysis and Design

The system architecture follows the **Model-View-Controller (MVC)** design pattern, implemented via the Flask framework.

### 4.1 Data Modeling (Entity-Relationship)

The database schema was designed using **SQLAlchemy ORM** to ensure data integrity across four core entities:

- **User**: Handles authentication and role-based profiles (Admin, Driver, Customer).
- **Delivery**: Captures pickup/drop-off coordinates, vehicle types, goods descriptions, and status.
- **Wallet**: Manages driver earnings and transaction history.
- **Notification/Activity**: Tracks system-wide events for auditing and user alerts.

### 4.2 Communication Design

The research incorporates **WebSockets (SocketIO)** for low-latency, bidirectional communication, essential for live driver tracking and instant status notifications.

## 5. Implementation Methodology (Tech Stack)

The following technologies were selected based on their scalability, community support, and performance:

- **Backend**: Python (Flask) for its lightweight yet extensible nature.
- **Database**: SQLite (Development) / PostgreSQL (Production) with SQLAlchemy for abstraction.
- **Frontend**: Bootstrap 5 for responsive design and Jinja2 for server-side template rendering.
- **Mapping**: Leaflet.js and OpenStreetMap (OSM) for license-free, high-performance geospatial visualization.
- **Real-time Engine**: Flask-SocketIO for managing live delivery sessions.

## 6. Testing and Quality Assurance

A multi-tiered testing strategy was adopted:

- **Unit Testing**: Testing individual routes and database models for expected behavior.
- **Integration Testing**: Ensuring the seamless flow of data between the Flask backend, SocketIO engine, and the frontend map interface.
- **User Acceptance Testing (UAT)**: Simulating the end-to-end delivery lifecycle—from customer booking to driver completion—to validate user experience (UX) and system reliability.

## 7. Deployment and Maintenance

The platform is designed for cloud deployment using:

- **Gunicorn**: A production-grade WSGI HTTP Server.
- **Eventlet**: A concurrent networking library to support long-polling and WebSocket connections required by SocketIO.
- **Environment Management**: Using `.env` files for secure configuration of secret keys and SMTP credentials.

---

© 2026 CargoFind Research & Development Team.
