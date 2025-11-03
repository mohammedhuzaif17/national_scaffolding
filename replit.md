# National Scaffolding and Fabrications E-Commerce Platform

## Overview
A Flask-based e-commerce platform for National Scaffolding and Fabrications featuring a modern glassmorphism UI design, dual admin panels, shopping cart functionality, and QR code payment integration.

## Recent Changes (November 3, 2025)
- Initial project setup with Flask, PostgreSQL, and all dependencies
- Created complete database schema with Users, Admins, Products, Orders, and OrderItems
- Implemented all frontend templates with glassmorphism design matching provided screenshots
- Built authentication system with login/register functionality
- **Security fix**: Removed hardcoded SECRET_KEY fallback; app now requires SESSION_SECRET environment variable
- Created dual admin panels for scaffolding and fabrication product management
- Implemented shopping cart with session-based storage
- Added QR code payment integration for checkout
- Seeded database with sample products and admin accounts

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
- User registration and login with secure password hashing
- Product browsing with category filtering (All, Aluminium, H-Frames, Cuplock)
- Welcome popup on homepage with glassmorphism effect
- Shopping cart with add/remove/quantity management
- QR code checkout with auto-calculated totals
- Order history viewing
- Responsive design with mobile support

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
1. **Session-based cart**: Cart stored in Flask sessions for simplicity
2. **Dual admin system**: Separate admin accounts for different product types
3. **Glassmorphism UI**: Modern design matching provided screenshots
4. **QR code payments**: Simple payment integration without external APIs
5. **PostgreSQL**: Persistent database for all data storage
