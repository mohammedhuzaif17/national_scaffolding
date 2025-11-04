# National Scaffolding and Fabrications E-Commerce Platform

## Overview
This project is a Flask-based e-commerce platform for National Scaffolding and Fabrications. Its primary purpose is to provide an intuitive online storefront for scaffolding and fabrication products, featuring a modern glassmorphism UI. Key capabilities include a robust shopping cart, dual admin panels for managing different product lines, and integrated QR code payment with server-side validation. The platform aims to streamline the sales process, offer comprehensive product customization, and ensure secure transactions, enhancing market reach and operational efficiency for the business.

## User Preferences
I prefer detailed explanations.
I want iterative development.
Ask before making major changes.
I prefer simple language.
Do not make changes to the folder `Z`.
Do not make changes to the file `Y`.

## System Architecture
The platform is built on a Flask backend with PostgreSQL as the database. The frontend utilizes HTML5, CSS3 with a distinct glassmorphism design, and vanilla JavaScript.

**UI/UX Decisions:**
- **Design:** Professional glassmorphism aesthetic with a royal blue (#1e3a8a) and gold (#d4af37) premium theme, enhanced with refined backdrop blur effects, inset shadows, and shimmer animations.
- **Typography:** Poppins for body text and Playfair Display for branding and titles, with gradient text effects on page titles for premium feel.
- **Interactivity:** Smooth CSS transitions, responsive grid layouts, ripple button effects, hover shimmer animations on product cards, and consistent royal styling across all pages.
- **User Flow:** Enhanced registration, unified login system (admins and users login from same /login page), category-specific product browsing, session-based welcome popup, and streamlined fabrication page with View Details-only workflow.
- **Product Customization:** Extensive use of dropdowns for product specifications (e.g., Aluminium scaffolding dimensions, H-Frame quantities with discount tiers, Cuplock types and sizes).

**Technical Implementations:**
- **Backend:** Flask handles all routes, business logic, and database interactions using Flask-SQLAlchemy.
- **Database:** PostgreSQL stores user, admin, product, order, and order item data.
- **Authentication:** Flask-Login manages user and admin sessions with secure password hashing via Werkzeug. Unified login system where admin usernames (admin_scaffolding, admin_fabrication) are automatically detected at /login and routed to appropriate admin panels.
- **Shopping Cart:** Session-based storage for cart items, storing product IDs and customization metadata. Toast notifications provide feedback when products are added.
- **Payment System:** Integration with PhonePe UPI via static QR codes, dynamically displaying exact payment amounts including 18% GST.
- **Order Processing:** Mandatory UPI Transaction ID entry for order completion, with server-side validation of amount and transaction ID.
- **Admin Panels:** Dual admin system allows separate management of scaffolding and fabrication products with full CRUD operations, dynamic forms, and comprehensive orders dashboard for payment verification.

**Feature Specifications:**
- **User Features:** Enhanced registration, unified login (email/phone/username), product browsing with simplified fabrication page (View Details only), dynamic product customization using dropdowns, session-based welcome popup, shopping cart with toast notifications, PhonePe QR payment verification with UPI transaction ID, and order history.
- **Admin Features:** Unified login from /login page (admin_scaffolding/admin123, admin_fabrication/admin123), automatic panel routing, full CRUD operations on products, category management, and comprehensive orders dashboard showing all customer orders with transaction IDs for payment verification.

**System Design Choices:**
- **Server-Side Price Calculation:** All pricing, including discounts and GST, is calculated server-side to prevent client-side manipulation.
- **Security:** Robust security measures including server-side validation for all inputs, secure session management with environment-based secret keys, password hashing, and separate authentication for users and administrators.
- **Modular Structure:** Clear separation of concerns with `app.py` for routes, `models.py` for database schema, and `seed_data.py` for initial data.

## External Dependencies
- **Database:** PostgreSQL (Neon-backed Replit database)
- **Python Libraries:**
    - Flask
    - Flask-Login
    - Flask-SQLAlchemy
    - Werkzeug (for password hashing)
    - `qrcode` library (for QR code generation, although now using a static image)