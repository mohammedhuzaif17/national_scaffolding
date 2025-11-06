# National Scaffolding and Fabrications E-Commerce Platform

## Overview
This project is a Flask-based e-commerce platform for National Scaffolding and Fabrications. Its primary purpose is to provide an intuitive online storefront for scaffolding and fabrication products, featuring a premium Royal Blue and Gold design theme that conveys luxury, trust, and professionalism. Key capabilities include a robust shopping cart, dual admin panels for managing different product lines, and integrated QR code payment with server-side validation. The platform aims to streamline the sales process, offer comprehensive product customization, and ensure secure transactions, enhancing market reach and operational efficiency for the business.

## User Preferences
I prefer detailed explanations.
I want iterative development.
Ask before making major changes.
I prefer simple language.
Do not make changes to the folder `Z`.
Do not make changes to the file `Y`.

## System Architecture
The platform is built on a Flask backend with PostgreSQL as the database. The frontend utilizes HTML5, CSS3 with a premium Royal Blue and Gold design system, and vanilla JavaScript. All styling is centralized in a single style.css file with no inline styles, ensuring maintainability and consistency across all pages.

**UI/UX Decisions:**
- **Design:** Premium ecommerce theme with Royal Blue and Gold color scheme. Features luxurious visual identity with elegant navigation, gold-accented buttons, sophisticated shadows, and professional layout with strong visual hierarchy. Royal Blue (#1e3a8a) serves as the primary brand color, while Gold (#d4af37) provides premium accents and highlights.
- **Typography:** Combination of Playfair Display for headings (elegant serif) and Poppins for body text (clean sans-serif), creating a luxurious yet readable appearance with excellent hierarchy and professional feel.
- **Interactivity:** Smooth CSS transitions with premium animations including fade-in effects, scale transformations, gold glow effects on hover, elegant underline animations on navigation links, and subtle ripple effects on buttons. All animations are classy and refined, not flashy.
- **Color Palette:** Royal Blue gradient backgrounds, Gold highlights on interactive elements, white/cream content areas for elegant contrast, gold borders on premium cards and sections, and soft shadows with royal blue tints.
- **User Flow:** Enhanced registration, unified login for admins and users, category-specific product browsing, session-based welcome popup with gold-bordered design, and streamlined fabrication page with "View Details"-only workflow.
- **Product Customization:** Extensive use of dropdowns for product specifications (e.g., Aluminium scaffolding dimensions, H-Frame quantities with discount tiers, Cuplock requiring both vertical and ledger specifications).

**Technical Implementations:**
- **Backend:** Flask handles all routes, business logic, and database interactions using Flask-SQLAlchemy.
- **Database:** PostgreSQL stores user, admin, product, order, and order item data.
- **Authentication:** Flask-Login manages user and admin sessions with secure password hashing via Werkzeug. Features a unified login system that routes to appropriate admin panels based on credentials.
- **Shopping Cart:** Session-based storage for cart items, storing product IDs and customization metadata, with toast notifications and product images displayed.
- **Payment System:** Integration with PhonePe UPI via static QR codes, dynamically displaying exact payment amounts including 18% GST. Mandatory UPI Transaction ID entry for order completion, with real-time client-side and server-side validation.
- **Admin Panels:** Dual admin system for separate management of scaffolding and fabrication products with full CRUD operations, file upload for product photos from camera/device with preview, dynamic forms, and comprehensive orders dashboard for payment verification.
- **Email Notifications:** Implemented automatic email notifications for order confirmations to customers and new order alerts to admins using Flask-Mail.

**Feature Specifications:**
- **User Features:** Enhanced registration, unified login, product browsing, dynamic product customization, session-based welcome popup, shopping cart, PhonePe QR payment verification with real-time UPI transaction ID validation, and order history.
- **Admin Features:** Unified login with automatic panel routing, full CRUD operations on products with file upload and image preview, category management, and comprehensive orders dashboard with transaction IDs for payment verification.

**System Design Choices:**
- **Server-Side Price Calculation:** All pricing, including discounts and GST, is calculated server-side to prevent client-side manipulation.
- **Security:** Robust security measures including server-side validation for all inputs, secure file upload handling, secure session management, password hashing, and separate authentication for users and administrators. Implemented transaction ID uniqueness validation to prevent fraud.
- **File Storage:** Product images uploaded by admins are stored in `static/uploads/` directory with secure filename handling.
- **Modular Structure:** Clear separation of concerns with `app.py` for routes, `models.py` for database schema, and `seed_data.py` for initial data.

## External Dependencies
- **Database:** PostgreSQL (Neon-backed Replit database)
- **Python Libraries:**
    - Flask
    - Flask-Login
    - Flask-Mail
    - Flask-SQLAlchemy
    - Werkzeug
    - Pillow
    - psycopg2-binary
    - qrcode (for static QR image)