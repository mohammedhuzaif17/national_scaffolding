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

### Phase 2 - Enhanced Features & Security (November 4, 2025)
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

## Project Architecture

### Backend (Flask)
- **app.py**: Main Flask application with all routes and logic
- **models.py**: SQLAlchemy database models
- **seed_data.py**: Database seeding script with sample data

### Database (PostgreSQL)
Tables:
- `users`: Customer accounts with authentication
- `admins`: Admin accounts with panel type (scaffolding/fabrication)
- `products`: Product catalog with categories and pricing
- `orders`: Order records with status tracking
- `order_items`: Individual items within orders

### Frontend
- **templates/**: HTML templates using Jinja2
  - `base.html`: Base template with navbar
  - `login.html`, `register.html`: Authentication pages
  - `dashboard.html`: Main navigation hub
  - `national_scaffoldings.html`: Scaffolding products with welcome popup
  - `fabrications.html`: Fabrication products
  - `cart.html`: Shopping cart
  - `qr_scanner.html`: Checkout with QR code
  - `my_orders.html`: Order history
  - `admin_scaffoldings.html`: Admin panel for scaffolding
  - `admin_fabrication.html`: Admin panel for fabrication

- **static/css/style.css**: Glassmorphism styling with animations

## Features

### User Features
- **Enhanced Registration**: Captures full name, phone, organization, email, and password
- **Flexible Login**: Authenticate using email, phone number, or username
- **Product Browsing**: Category-specific pages (All, Aluminium, H-Frames, Cuplock, Accessories)
- **Welcome Popup**: Glassmorphism popup with rainbow gradient border on first visit
- **Product Customization**:
  - Aluminium: Choose width, height, and buy/rent option
  - H-Frames: Automatic discounts based on quantity
  - Cuplock: Vertical/Ledger type selection with size customization
  - Accessories: Simple quantity selection
- **Shopping Cart**: Add/remove items with customization details displayed
- **PhonePe Payment**: QR code with embedded amount including 18% GST
- **Order History**: View all completed orders with details
- **Responsive Design**: Mobile-friendly interface

### Admin Features
- Separate admin logins for scaffolding and fabrication panels
- Full CRUD operations for products
- Category management for scaffolding products
- Real-time product updates

### Design
- Dark navy blue gradient background
- Glassmorphism effects with backdrop blur
- Smooth CSS animations and transitions
- Rainbow gradient borders on popup
- Orange (#ffa500) accent color for branding
- Responsive grid layouts

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
- **H-Frame Discounts**: Discount tiers computed server-side based on quantity validation
- **Cuplock Pricing**: Per-kg pricing (₹78/kg) calculated server-side using weight_per_unit
- **Input Validation**: Quantity must be positive integer; invalid inputs rejected
- **Session Security**: Secure session management with environment-based secret key
- **Password Hashing**: Werkzeug secure password hashing for all user accounts
