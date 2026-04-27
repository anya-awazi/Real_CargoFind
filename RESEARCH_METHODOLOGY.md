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

## 5. Development and Implementation Methodology

### 3.1.3 Development Environment

Visual Studio Code, sometimes known as VS Code, is the main integrated development environment (IDE) used for this project. With features including intelligent code completion, debugging capabilities, an integrated terminal, and a robust ecosystem of extensions, Visual Studio Code offers a complete development environment with broad support for web technologies like Python, Flask, and JavaScript. Version control management is made easier by the IDE's integrated Git integration, and developer productivity is increased by its configurable interface and workspace settings. The project leverages extensions such as Python and Pylance to streamline the development process, allowing for real-time code analysis and efficient debugging of the Flask backend and Jinja2 templates.

### 3.1.4 Database Management System

The local development database environment utilizes SQLite, a C-language library that implements a small, fast, self-contained, high-reliability, full-featured, SQL database engine. For data administration and storage, the project employs SQLAlchemy as an Object-Relational Mapper (ORM), providing a high-level abstraction for database operations and ensuring data integrity through a well-defined schema. Database-driven web applications may be developed and tested locally with ease thanks to this integrated package, which avoids the overhead of managing a separate database server during the early stages of development. By facilitating database migrations, query execution, and data visualization, the integrated ORM approach improves the usability and effectiveness of database management within the Flask ecosystem.

### 3.1.5 Testing Software

#### Unit Testing Framework

To guarantee code functionality and dependability, the program uses thorough unit testing techniques. Automated test suites are created and run using Python-based testing frameworks like `unittest` or `pytest`. These frameworks offer tools for code coverage analysis, mock functions, assertion libraries, and test case structure. The purpose of unit tests is to verify that each piece of code, particularly the core logistics logic and database models, operates as intended under a variety of circumstances by validating distinct modules, functions, and components separately.

#### Integration Testing

In addition to unit testing, integration testing is used to confirm how various application modules and components interact with one another. Testing database connections, API endpoints, and the interaction between the Flask backend and the SocketIO real-time engine are all included in this. Integration tests ensure smooth data flow and appropriate system connectivity by assisting in the identification of potential problems that may occur when separate components, such as the live tracking and delivery status modules, operate together.

#### Browser Testing

To guarantee a consistent user experience, cross-browser compatibility testing is carried out across a number of web browsers, including Chrome, Firefox, Safari, and Edge. Validation of JavaScript functionality, CSS rendering in various browser contexts and screen sizes, and responsive design features using Bootstrap 5 are all part of the testing process. This ensures that the platform remains accessible and functional for both desktop and mobile users across different device specifications.

### 3.1.6 Programming Languages and Technologies

#### Frontend technologies: Hypertext Markup Language (HTML5)

This markup language is the cornerstone for organizing web information. Better accessibility features, better form controls, and improved semantic elements are all included in the most recent version. Semantic tags like `<header>`, `<nav>`, `<main>`, `<section>`, and `<footer>` in HTML5 provide a more meaningful page structure that enhances screen reader compatibility and SEO performance for the CargoFind platform.

#### Cascading Style Sheets (CSS3)

It is used for layout and styling and offers sophisticated features including responsive design, flexbox and grid layouts, animations, and transitions. The project primarily utilizes the Bootstrap 5 framework, which provides a comprehensive set of pre-designed utility classes and components that adhere to contemporary best practices, such as component-based architecture and responsive design that prioritizes mobile devices for driver accessibility.

#### JavaScript (ES6+)

Client-side interaction and dynamic content manipulation are accomplished with modern JavaScript (ECMAScript 2015 and later). For clearer, easier-to-maintain code, the implementation makes use of ES6+ capabilities like arrow functions, restructuring, modules, promises, and async/await. JavaScript, combined with Socket.io and Leaflet.js, manages real-time map updates, form validation, and interactive user experiences.

#### Backend Integration

The program connects with backend services for server-side processing and data persistence through the Flask framework. Through Python server-side scripting, RESTful API endpoints and WebSocket events enable connectivity between the SQLite database and the frontend application, guaranteeing safe and effective data transmission for delivery tracking and user management.

### 3.1.7 Extra Tools for Development

#### Version Control

VS Code integrates the Git version control system for source code management, facilitating change tracking, branch management, and collaborative development across the development lifecycle. This ensures that all modifications to the logistics platform are documented and reversible, maintaining a stable codebase.

#### Package Management

Third-party libraries and Python dependencies are managed using `pip` (the Python Package Installer), which guarantees uniform package versions and simplifies dependency installation through the use of a `requirements.txt` file across different development environments.

#### Build and Deployment Tools

To manage assets and enable sophisticated development capabilities, production-grade tools such as Gunicorn and Eventlet are used. Gunicorn serves as the WSGI HTTP server, while Eventlet provides the necessary concurrency for real-time WebSocket communication, ensuring the platform can handle multiple simultaneous delivery sessions efficiently.

---

© 2026 CargoFind Research & Development Team.
