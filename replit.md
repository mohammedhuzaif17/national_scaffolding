# National Scaffolding and Fabrications E-Commerce Platform

## Overview
A Flask-based e-commerce platform for National Scaffolding and Fabrications featuring a modern glassmorphism UI design, dual admin panels, shopping cart functionality, and QR code payment integration.

## Recent Changes (November 4, 2025)
### Phase 1 - Initial Setup (November 3, 2025)
- Initial project setup with Flask, PostgreSQL, and all dependencies
- Created complete database schema with Users, Admins, Products, Orders, and OrderItems
- Implemented all frontend templates with glassmorphism design
- Built authentication system with login/register functionality
- **Security fix**: Removed hardcoded SECRET_KEY fallback; app now requires SESSION_SECRET environment variable
- Created dual admin panels for scaffolding and fabrication product management
- Implemented shopping cart with session-based storage
- Added QR code payment integration for checkout
- Seeded database with sample products and admin accounts

### Phase 2 - Enhanced Features & Security (November 4, 2025, Morning)
- **MAJOR SECURITY FIX**: Implemented server-side price calculation for all products
- **Enhanced Authentication**: Login now supports email, phone, or username
- **Enhanced Registration**: Added full_name, phone, and organization fields
- **Category-Specific Customizations**:
  - Aluminium Scaffolding: Width (0.7m/1.4m), Height, Buy/Rent pricing
  - H-Frames: Quantity-based discounts (10+ → 5%, 20+ → 7.5%, 30+ → 10%, 50+ → 12%, 100+ requires contact)
  - Cuplock: Vertical (1-3m, 1-6 cups) and Ledger (0.6-3.0m) with per-kg pricing at ₹78/kg
  - Accessories: Standard quantity-based ordering
- **PhonePe UPI Integration**: QR codes embed exact payment amount with 18% GST
- **Server-Side Validation**: All prices calculated server-side with quantity validation
- **Admin Panel Improvements**: Dynamic forms based on product category selection
- **About Page**: Added company information and branding
- **Product Detail Pages**: Individual pages for each product with customization options

### Phase 3 - UX Improvements & Enhanced Security (November 4, 2025, Afternoon)
- **Payment Verification System**: 
  - Users must enter UPI Transaction ID (minimum 8 characters) before order completion
  - Transaction ID stored in Order model for payment tracking
  - Server-side validation ensures transaction ID is required and valid
  - Amount is calculated entirely server-side (no client manipulation possible)
  - Order.amount_paid field stores server-calculated total for audit trail
- **Separate Admin Login**:
  - Created dedicated `/admin_login` route and `admin_login.html` template
  - Removed admin option from user login page for cleaner UX
  - Admin login requires username, password, and panel type selection
  - Link to admin login available from user login page
- **Dropdown Improvements for Better UX**:
  - Replaced all manual quantity inputs with dropdown selects (1-50 range)
  - H-Frames quantity dropdown shows discount tiers (15, 25, 35, 60, 80 pieces)
  - Aluminium height and width already using dropdowns
  - Cuplock size selections using dropdowns
  - Improved user experience with predefined options
- **Royal Blue & Gold Premium Theme**:
  - Updated color scheme to royal blue (#1e3a8a) and gold (#d4af37)
  - Enhanced navbar with gold branding and better backdrop blur
  - Updated all buttons to use royal gradient (blue to gold)
  - Category buttons with gold borders and hover effects
  - Product cards with gold titles and consistent styling
  - Glass containers with gradient top border (blue-gold-purple)
  - Premium font styling with Poppins and Playfair Display
- **Welcome Popup Enhancement**:
  - Popup now uses sessionStorage to display only once per browser session
  - No longer shows on every category page change
  - Rainbow gradient border maintained for visual appeal
- **Bug Fixes**:
  - Fixed About page "Home" link to redirect to `/national_scaffoldings` instead of non-existent `index.html`
  - Updated page title from "User Login" to clearly distinguish from admin login

## Project Architecture

### Backend (Flask)
- **app.py**: Main Flask application with all routes and logic
- **models.py**: SQLAlchemy database models
- **seed_data.py**: Database seeding script with sample data

### Database (PostgreSQL)
Tables:
- `users`: Customer accounts with authentication (username, email, phone, full_name, organization)
- `admins`: Admin accounts with panel type (scaffolding/fabrication)
- `products`: Product catalog with categories, pricing, and customization options
- `orders`: Order records with status, transaction_id, and amount_paid for payment verification
- `order_items`: Individual items within orders with customization details

### Frontend
- **templates/**: HTML templates using Jinja2
  - `base.html`: Base template with royal blue & gold navbar
  - `login.html`: User login (email/phone/username authentication)
  - `admin_login.html`: Dedicated admin login with panel selection
  - `register.html`: User registration page
  - `dashboard.html`: Main navigation hub
  - `national_scaffoldings.html`: Scaffolding products with session-based welcome popup
  - `fabrications.html`: Fabrication products
  - `product_detail.html`: Individual product pages with dropdown customization
  - `cart.html`: Shopping cart with customization details
  - `qr_scanner.html`: Checkout with PhonePe QR code and transaction ID verification
  - `my_orders.html`: Order history with transaction IDs
  - `admin_scaffoldings.html`: Admin panel for scaffolding products
  - `admin_fabrication.html`: Admin panel for fabrication products
  - `about.html`: Company information and branding

- **static/css/style.css**: Royal blue & gold glassmorphism theme with premium styling

## Features

### User Features
- **Enhanced Registration**: Captures full name, phone, organization, email, and password
- **Flexible Login**: Authenticate using email, phone number, or username (separate from admin login)
- **Product Browsing**: Category-specific pages (All, Aluminium, H-Frames, Cuplock, Accessories)
- **Welcome Popup**: Glassmorphism popup with rainbow gradient border (shows once per session)
- **Product Customization with Dropdowns**:
  - Aluminium: Dropdown select for width, height, purchase type (buy/rent), and quantity (1-50)
  - H-Frames: Dropdown with pre-selected discount quantities (15, 25, 35, 60, 80 pieces)
  - Cuplock: Dropdown selects for type, size, cups, and quantity
  - Accessories: Dropdown quantity selector (1-50)
- **Shopping Cart**: Add/remove items with customization details displayed
- **Payment Verification**: 
  - QR code with embedded PhonePe payment amount including 18% GST
  - Mandatory UPI Transaction ID entry (minimum 8 characters)
  - Server-side amount validation (no client manipulation possible)
- **Order History**: View all completed orders with transaction IDs and details
- **Responsive Design**: Mobile-friendly interface with royal blue and gold theme

### Admin Features
- **Dedicated Admin Login**: Separate `/admin_login` page (not mixed with user login)
- **Panel Type Selection**: Choose between scaffolding and fabrication admin panels
- **Dual Admin System**: Separate admin accounts for scaffolding and fabrication panels
- **Full CRUD Operations**: Add, edit, delete products from admin panels
- **Category Management**: Manage scaffolding product categories
- **Real-time Updates**: Product changes immediately visible to users

### Design
- **Royal Blue & Gold Premium Theme**: Professional color scheme with royal blue (#1e3a8a) and gold (#d4af37)
- **Enhanced Glassmorphism**: Improved backdrop blur effects with gradient borders
- **Premium Typography**: Poppins for body text, Playfair Display for brand name
- **Smooth Animations**: CSS transitions on all interactive elements
- **Rainbow Gradient**: Welcome popup border with multi-color gradient
- **Responsive Grid**: Mobile-friendly layouts across all pages
- **Consistent Styling**: Unified color palette across all pages including About

## Credentials

### Admin Accounts
- **Scaffolding Admin**: Username: `admin_scaffolding`, Password: `admin123`
- **Fabrication Admin**: Username: `admin_fabrication`, Password: `admin123`

### Test User
- Username: `testuser`, Password: `test123`

## Running the Application
The Flask app runs on port 5000 and is configured as a workflow. The database is automatically created and seeded on first run.

## Technology Stack
- **Backend**: Flask 3.1.2, Flask-Login, Flask-SQLAlchemy
- **Database**: PostgreSQL (Neon-backed Replit database)
- **Frontend**: HTML5, CSS3 with Glassmorphism, Vanilla JavaScript
- **Payment**: QR Code generation with qrcode library
- **Security**: Werkzeug password hashing, session-based authentication

## Project Structure
```
.
├── app.py                 # Main Flask application
├── models.py              # Database models
├── seed_data.py           # Database seeding script
├── templates/             # HTML templates
│   ├── base.html
│   ├── login.html
│   ├── register.html
│   ├── dashboard.html
│   ├── national_scaffoldings.html
│   ├── fabrications.html
│   ├── cart.html
│   ├── qr_scanner.html
│   ├── my_orders.html
│   ├── admin_scaffoldings.html
│   └── admin_fabrication.html
└── static/
    └── css/
        └── style.css      # Glassmorphism styling
```

## Key Design Decisions
1. **Server-Side Price Calculation**: All prices computed server-side to prevent manipulation
2. **Session-Based Cart**: Cart stores only product IDs and customization metadata, not prices
3. **Dual Admin System**: Separate admin accounts for scaffolding and fabrication products
4. **Glassmorphism UI**: Modern design with backdrop blur and rainbow gradient accents
5. **PhonePe UPI Integration**: QR codes embed exact payment amounts with GST
6. **PostgreSQL Database**: Persistent storage for all application data
7. **Quantity Validation**: Server-side validation for positive integers and business rules

## Security Features
- **Price Integrity**: All prices calculated server-side from database; client cannot manipulate
- **Payment Amount Security**: Order amount calculated entirely server-side; client only provides transaction ID
- **Transaction ID Validation**: Server-side validation ensures minimum 8-character transaction ID before order completion
- **H-Frame Discounts**: Discount tiers computed server-side based on quantity validation
- **Cuplock Pricing**: Per-kg pricing (₹78/kg) calculated server-side using weight_per_unit
- **Input Validation**: Quantity and customization validated server-side
- **Session Security**: Secure session management with environment-based secret key (SESSION_SECRET required)
- **Password Hashing**: Werkzeug secure password hashing for all user accounts
- **Separate Admin Authentication**: Admin login completely separated from user login with panel type verification
