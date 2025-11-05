# National Scaffolding and Fabrications E-Commerce Platform

## Overview
This project is a Flask-based e-commerce platform for National Scaffolding and Fabrications. Its primary purpose is to provide an intuitive online storefront for scaffolding and fabrication products, featuring a modern glassmorphism UI. Key capabilities include a robust shopping cart, dual admin panels for managing different product lines, and integrated QR code payment with server-side validation. The platform aims to streamline the sales process, offer comprehensive product customization, and ensure secure transactions, enhancing market reach and operational efficiency for the business.

## Recent Changes
**November 4, 2025:**
- Database: Added `transaction_id` and `amount_paid` columns to Order model for payment tracking
- Product Customization: Fixed H-Frame double width dropdown to show all heights (6-16) instead of only even numbers
- Product Customization: Restructured Cuplock customization to make both vertical AND ledger mandatory fields (previously was optional choice)
- Admin Panels: Changed product photo upload from URL input to file upload with camera/device support, including image preview
- Shopping Cart: Added product images to cart display alongside product details with fallback for missing images
- About Page: Completely replaced with comprehensive new HTML file (1814 lines) with enhanced styling and content
- Payment Validation: Implemented real-time UPI Transaction ID validation with visual feedback (green tick for valid 12-35 char IDs, red cross for invalid), payment button disabled until valid ID entered
- Admin Orders Dashboard: Enhanced to display complete customer details (full name, email, phone, organization) instead of just username, with proper fallbacks for missing data
- About Page Navigation: Fixed navigation bar to include all site options (Scaffolding, Fabrications, Cart, My Orders, Dashboard, Login/Logout) with proper Flask routing and authentication-based conditional display
- Landing Page: Created new welcome page with two category cards (National Scaffolding and Fabrications) with responsive styling and smooth animations
- Admin Order Filtering: Scaffolding admin now sees only orders containing scaffolding products; Fabrication admin sees only orders containing fabrication products
- Customer Details Enhancement: Improved admin orders dashboard customer display with cleaner card-style layout, labeled fields, and better readability
- Branding Fix: Corrected final "Crest Technocrat" reference in dashboard.html to "The National Scaffolding" for consistent branding
- Logout Flow: Changed logout redirect from login page to landing page to prevent confusing login/logout loops
- Email Notifications: Installed Flask-Mail and implemented automatic email notifications - customers receive order confirmation emails with complete order details, and admins receive new order alerts with customer information and transaction ID for verification
- About Page Complete Replacement: Replaced entire about.html with comprehensive new content including hero section with stats, expertise bars, client/project journey, board of administrators, detailed user manual, FAQs, privacy policy, and terms of use - all styled with royal blue (#1e3a8a) and gold (#d4af37) theme and fully integrated with Flask routing
- About Page Theme Conversion: Converted about page from light theme to consistent dark glassmorphism design matching main website - added dark gradient background (linear-gradient(135deg, #0a1628 0%, #1e3a8a 50%, #2c5364 100%)), applied backdrop blur effects to all sections (navbar, hero, stats, expertise, administrators, footer), changed all text colors to white/light for readability, updated mobile navigation with dark glass background, and added all necessary CSS variables for theme consistency
- User Manual Download: Added download button in user manual section with gradient royal blue-to-gold styling, implemented JavaScript function to extract and download user manual content as formatted .txt file ("National_Scaffolding_User_Manual.txt") including all sections, tables, and bullet points
- About Page Navigation Fix: Updated navigation to show "Cart" and "My Orders" only when user is authenticated - logged out users see only "Products", "About", and "Login"

**November 5, 2025:**
- Admin Panel Rent Option: Extended rent price field to ALL product categories (aluminium, h-frames, cuplock, accessories) - previously only available for aluminium
- H-Frame Quantity Range: Changed H-Frame quantity dropdown from limited options (1-10, then 15, 25, 35, 60, 80) to complete range 1-100 with automatic discount labels shown directly in dropdown, quantity 100 now works correctly with 12% discount
- Admin Weight Field Fix: Fixed cuplock product editing to properly populate and save weight_per_unit field - added weight parameter to editProduct() function
- Cuplock Dual Customization: Restored cuplock to include BOTH vertical AND ledger specifications as required customization features within single product - vertical section (size, cups, custom length) and ledger section (ledger size) both displayed in separate royal blue glass containers for clear visual separation, quantity dropdown extended to 1-100 range matching H-frames
- Dropdown Scrollability: Added CSS styling for scrollable dropdowns with max-height 250px and custom royal gold scrollbar styling, verified all dropdowns across website show complete number ranges (no even-number-only dropdowns)
- Cuplock Product Consolidation: Deleted separate "Cuplock Ledger System" product from database and renamed "Cuplock Vertical System" to "Cuplock System" - now there is only ONE cuplock product with both vertical and ledger customization options within its detail page
- Customer Address Field: Added complete address field to User model and registration form - users now required to enter full address (Street, City, State, PIN) during registration, address is displayed in admin orders dashboard and included in email notifications for order fulfillment
- Duplicate Transaction ID Prevention: Implemented transaction ID uniqueness validation - each transaction ID can only be used once, preventing fraud where users reuse the same payment screenshot for multiple orders. System checks database before accepting order and shows clear error message: "This Transaction ID has already been used. Each purchase requires a unique payment."
- Phone Number Validation: Added strict phone number validation in registration - phone numbers must start with Indian country code +91 followed by exactly 10 digits (e.g., +919876543210), with both client-side HTML5 validation (pattern, maxlength) and server-side validation to ensure data integrity. The +91 prefix is fixed and displayed separately, users only enter 10 digits starting with 6, 7, 8, or 9 (valid Indian mobile numbers)

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
- **Design:** Clean, modern light theme with royal blue (#2563eb) as the primary color, inspired by Amazon, Netflix, and professional e-commerce platforms. Features white backgrounds, minimal shadows, and simple aesthetics for maximum readability and professionalism.
- **Typography:** Poppins for body text and Playfair Display for branding and titles, with clean hierarchy and excellent readability.
- **Interactivity:** Smooth CSS transitions, responsive grid layouts, ripple button effects, hover shimmer animations on product cards, and consistent royal styling across all pages.
- **User Flow:** Enhanced registration, unified login system (admins and users login from same /login page), category-specific product browsing, session-based welcome popup, and streamlined fabrication page with View Details-only workflow.
- **Product Customization:** Extensive use of dropdowns for product specifications (e.g., Aluminium scaffolding dimensions, H-Frame quantities with discount tiers showing all heights 6-16, Cuplock requiring both vertical and ledger specifications).

**Technical Implementations:**
- **Backend:** Flask handles all routes, business logic, and database interactions using Flask-SQLAlchemy.
- **Database:** PostgreSQL stores user, admin, product, order, and order item data.
- **Authentication:** Flask-Login manages user and admin sessions with secure password hashing via Werkzeug. Unified login system where admin usernames (admin_scaffolding, admin_fabrication) are automatically detected at /login and routed to appropriate admin panels.
- **Shopping Cart:** Session-based storage for cart items, storing product IDs and customization metadata. Toast notifications provide feedback when products are added. Cart displays product images with each item.
- **Payment System:** Integration with PhonePe UPI via static QR codes, dynamically displaying exact payment amounts including 18% GST.
- **Order Processing:** Mandatory UPI Transaction ID entry (12-35 alphanumeric characters) for order completion, with real-time client-side validation showing green tick (valid) or red cross (invalid), and server-side validation of amount and transaction ID.
- **Admin Panels:** Dual admin system allows separate management of scaffolding and fabrication products with full CRUD operations, file upload for product photos from camera/device with preview, dynamic forms, and comprehensive orders dashboard for payment verification.

**Feature Specifications:**
- **User Features:** Enhanced registration, unified login (email/phone/username), product browsing with simplified fabrication page (View Details only), dynamic product customization using dropdowns, session-based welcome popup, shopping cart with product images and toast notifications, PhonePe QR payment verification with real-time UPI transaction ID validation (12-35 chars with visual feedback), and order history.
- **Admin Features:** Unified login from /login page (admin_scaffolding/admin123, admin_fabrication/admin123), automatic panel routing, full CRUD operations on products with file upload from camera/device and image preview, category management, and comprehensive orders dashboard showing all customer orders with transaction IDs for payment verification.

**System Design Choices:**
- **Server-Side Price Calculation:** All pricing, including discounts and GST, is calculated server-side to prevent client-side manipulation.
- **Security:** Robust security measures including server-side validation for all inputs, secure file upload handling with allowed extensions check (.jpg, .jpeg, .png, .gif), secure session management with environment-based secret keys, password hashing, and separate authentication for users and administrators.
- **File Storage:** Product images uploaded by admins are stored in `static/uploads/` directory with secure filename handling.
- **Modular Structure:** Clear separation of concerns with `app.py` for routes, `models.py` for database schema, and `seed_data.py` for initial data.

## External Dependencies
- **Database:** PostgreSQL (Neon-backed Replit database)
- **Python Libraries:**
    - Flask (web framework and file upload handling)
    - Flask-Login (authentication)
    - Flask-Mail (email notifications for orders)
    - Flask-SQLAlchemy (database ORM)
    - Werkzeug (password hashing and secure filename generation)
    - Pillow (image processing for uploaded photos)
    - psycopg2-binary (PostgreSQL adapter)
    - qrcode (QR code generation, currently using static image)

## Email Configuration (Optional)
Email notifications are configured but require SMTP credentials to function. To enable email notifications:

**Required Environment Variables:**
- `MAIL_USERNAME` - Your email address (e.g., [email protected])
- `MAIL_PASSWORD` - Your email password or app-specific password
- `MAIL_DEFAULT_SENDER` - Sender email (defaults to MAIL_USERNAME if not set)
- `ADMIN_EMAIL` - Admin email to receive order notifications (defaults to MAIL_DEFAULT_SENDER if not set)

**Optional Environment Variables:**
- `MAIL_SERVER` - SMTP server (default: smtp.gmail.com)
- `MAIL_PORT` - SMTP port (default: 587)
- `MAIL_USE_TLS` - Use TLS encryption (default: True)

**For Gmail:**
1. Enable 2-Factor Authentication on your Google account
2. Generate an App Password: Google Account → Security → 2-Step Verification → App Passwords
3. Use the generated App Password as MAIL_PASSWORD

**Note:** If email is not configured, the system will continue to work normally - emails just won't be sent. All email functions fail silently without breaking order processing.