# National Scaffolding and Fabrications E-Commerce Platform

## Overview
This project is a Flask-based e-commerce platform for National Scaffolding and Fabrications. Its primary purpose is to provide an intuitive online storefront for scaffolding and fabrication products, featuring a premium Deep Blue and Gold design theme that conveys luxury, trust, and professionalism. Key capabilities include a robust shopping cart, dual admin panels for managing different product lines, and integrated QR code payment with server-side validation. The platform aims to streamline the sales process, offer comprehensive product customization, and ensure secure transactions, enhancing market reach and operational efficiency for the business.

## User Preferences
I prefer detailed explanations.
I want iterative development.
Ask before making major changes.
I prefer simple language.
Do not make changes to the folder `Z`.
Do not make changes to the file `Y`.

## System Architecture
The platform is built on a Flask backend with PostgreSQL as the database. The frontend utilizes HTML5, CSS3 with a premium Deep Blue (#001d3d) and Gold design system, and vanilla JavaScript. All styling is centralized in a single style.css file with no inline styles, ensuring maintainability and consistency across all pages.

**UI/UX Decisions:**
- **Design:** Premium ecommerce theme with Deep Blue and Gold color scheme. Features luxurious visual identity with elegant navigation, gold-accented buttons, sophisticated shadows, and professional layout with strong visual hierarchy. Deep Blue (#001d3d) serves as the primary brand color, while Gold (#d4af37) provides premium accents and highlights.
- **Typography:** Combination of Montserrat for headings (modern sans-serif) and Inter for body text and numerical values (clean sans-serif), creating a luxurious yet readable appearance with excellent hierarchy and professional feel. All numbers use professional Inter font for clarity.
- **Interactivity:** Smooth CSS transitions with premium animations including fade-in effects, scale transformations, gold glow effects on hover, elegant underline animations on navigation links, subtle ripple effects on buttons, and beautiful modal/popup animations with backdrop blur and slide-down effects. All animations are classy and refined, not flashy. Admin navigation features "Business Analytics" button instead of "Back to Home" for better workflow.
- **Color Palette:** Deep Blue (#001d3d) gradient backgrounds, Gold highlights on interactive elements, white/cream content areas for elegant contrast, gold borders on premium cards and sections, and soft shadows with deep blue tints.
- **User Flow:** Enhanced registration, unified login for admins and users, landing page displays National Scaffolding products directly with category filtering (Aluminium, H-Frames, Cuplock, Accessories), streamlined fabrication page with "View Details"-only workflow, and expandable Privacy Policy and Terms of Use sections in footer. Welcome popup removed from entire website for cleaner user experience.
- **Product Customization:** Extensive use of dropdowns for product specifications:
  - **Aluminium:** Width (0.7m/1.4m) and height (2m-16m) selections with buy/rent options
  - **H-Frames:** Quantity selector up to 200 sets with buy/rent options (no discount tiers)
  - **Cuplock:** Contact-only products - Vertical shows vertical specs, Ledger shows ledger specs, no purchasing options
  - **Accessories:** Full buy/rent options with quantity selection

**Technical Implementations:**
- **Backend:** Flask handles all routes, business logic, and database interactions using Flask-SQLAlchemy.
- **Database:** PostgreSQL stores user, admin, product, order, and order item data.
- **Authentication:** Flask-Login manages user and admin sessions with secure password hashing via Werkzeug. Features a unified login system that routes to appropriate admin panels based on credentials.
- **Shopping Cart:** Session-based storage for cart items, storing product IDs and customization metadata, with toast notifications and product images displayed.
- **Payment System:** Integration with PhonePe UPI via static QR codes, dynamically displaying exact payment amounts including 18% GST. Mandatory UPI Transaction ID entry for order completion, with real-time client-side and server-side validation.
- **Admin Panels:** Dual admin system for separate management of scaffolding and fabrication products with full CRUD operations via popup modals, file upload for product photos from camera/device with preview, category-specific dynamic form fields, comprehensive orders dashboard for payment verification, and business analytics dashboard with Chart.js visualizations showing revenue trends, order counts, and category breakdowns.
- **Email Notifications:** Implemented automatic email notifications for order confirmations to customers and new order alerts to admins using Flask-Mail.
- **Data Visualization:** Interactive business analytics dashboard featuring key metrics cards (total revenue, total orders, average order value), monthly revenue trend line chart, yearly revenue bar chart, category-wise revenue doughnut chart, and monthly orders count bar chart. All charts use the premium Deep Blue and Gold color scheme and are fully responsive.

**Feature Specifications:**
- **User Features:** Enhanced registration, unified login, product browsing, dynamic product customization, session-based welcome popup, shopping cart, PhonePe QR payment verification with real-time UPI transaction ID validation, and order history.
- **Admin Features:** Unified login with automatic panel routing, full CRUD operations on products via elegant popup/modal forms with category-specific fields (Aluminium: pricing matrix indicators and dimension notes; H-Frames: set quantities with buy/rent pricing; Cuplock: simplified form with only name, description, and images; Accessories: buy/rent pricing with material info), file upload with image preview, comprehensive pricing matrix management for Aluminium, H-Frames, and Accessories with separate admin panels, comprehensive orders dashboard with transaction IDs for payment verification, and business analytics dashboard with interactive charts showing monthly/yearly revenue trends, order counts, and category-wise breakdown powered by Chart.js.

**System Design Choices:**
- **Server-Side Price Calculation:** All pricing, including discounts and GST, is calculated server-side to prevent client-side manipulation. Aluminium scaffolding uses a comprehensive pricing matrix that considers both width (0.7m or 1.4m) and height (2m-16m) dimensions, with rent prices calculated as 20% of purchase prices.
- **Pricing Matrix System:**
  - **Aluminium Scaffolding:** Dynamic pricing organized by width (0.7m Single/1.4m Double) and height (2m-16m). Admins set separate buy and rent prices for each width/height combination via dedicated pricing matrix admin panel.
  - **H-Frames:** Pricing organized by quantity sets (1, 5, 10, 20, 30, 40, 50, 75, 100, 150, 200 sets). Admins manage buy and rent prices for each set quantity across all H-Frame products. No discount tiers - simple buy/rent pricing model.
  - **Accessories:** Simple buy/rent pricing for each accessory product. Admins manage pricing for all accessories in dedicated pricing matrix panel.
  - **Cuplock:** Contact-only products with no online pricing or purchasing. Product pages display specifications and contact information for quotes.
  - All pricing matrices stored in database as JSON in product.customization_options field
  - Frontend and backend load pricing dynamically from database to ensure consistency
  - Admins access pricing matrices via dedicated gold-accented buttons in admin panel
- **Security:** Robust security measures including server-side validation for all inputs, secure file upload handling, secure session management, password hashing, and separate authentication for users and administrators. Implemented transaction ID uniqueness validation to prevent fraud. Orders created with 'pending_verification' status require admin approval after verifying actual payment amount.
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
- **Frontend Libraries:**
    - Chart.js v4.4.0 (CDN) - For business analytics data visualization with interactive charts