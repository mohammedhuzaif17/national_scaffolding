# The National Scaffolding - Setup Instructions

## 🚀 Quick Start Guide

This is the complete, latest version of The National Scaffolding e-commerce website with all upgrades and features.

---

## 📋 Prerequisites

Before running the website, make sure you have:

1. **Python 3.10+** installed
2. **PostgreSQL database** (we use Neon - get free account at https://neon.tech)
3. **Git** (optional, for version control)

---

## 🔧 Installation Steps

### Step 1: Extract the Archive

Extract all files from the archive to your desired folder.

### Step 2: Create Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Mac/Linux
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install flask flask-login flask-mail flask-sqlalchemy pillow psycopg2-binary python-dotenv qrcode werkzeug
```

### Step 4: Configure Environment Variables

1. **Rename** `ENV_TEMPLATE.txt` to `.env`
2. **Edit** the `.env` file and add your values:

```env
SESSION_SECRET=your_random_secret_key_here
DATABASE_URL=postgresql://username:password@host:port/database?sslmode=require
```

**Get your DATABASE_URL:**
- Sign up at https://console.neon.tech
- Create a new project
- Copy the connection string
- **IMPORTANT:** Add `?sslmode=require` at the end!

**Generate SESSION_SECRET:**
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### Step 5: Run the Website

```bash
python app.py
```

The website will start at: **http://127.0.0.1:5000**

---

## 👤 Default Admin Credentials

**Scaffolding Admin:**
- Username: `admin_scaffolding`
- Password: `admin123`

**Fabrication Admin:**
- Username: `admin_fabrication`
- Password: `admin123`

**⚠️ CHANGE THESE PASSWORDS IN PRODUCTION!**

---

## ✨ Latest Features Included

### 1. **Welcome Popup**
- Appears immediately when website opens
- Beautiful glassmorphism design
- Session-based (shows once per session)

### 2. **Landing Page**
- Two category cards: Scaffolding & Fabrications
- Smooth animations and hover effects

### 3. **Phone Number Validation**
- Fixed +91 prefix for Indian numbers
- Users enter only 10 digits (starting with 6, 7, 8, or 9)
- Client and server-side validation

### 4. **Customer Address**
- Complete address collection during registration
- Displayed in admin orders dashboard
- Included in email notifications

### 5. **Transaction ID Validation**
- Unique transaction ID enforcement
- Prevents payment fraud
- Real-time validation with visual feedback

### 6. **Email Notifications** (Optional)
- Order confirmation emails to customers
- New order alerts to admin
- Configure in .env file

### 7. **Product Management**
- File upload for product images (camera/device support)
- Image preview before upload
- Rent/Buy options for products

### 8. **Shopping Cart**
- Session-based cart storage
- Product images in cart
- Toast notifications

### 9. **Admin Panels**
- Separate dashboards for Scaffolding & Fabrication
- Complete CRUD operations
- Order filtering by product category
- Transaction ID verification

---

## 📂 Project Structure

```
national-scaffolding/
├── app.py                    # Main Flask application
├── models.py                 # Database models
├── seed_data.py              # Initial data setup
├── templates/                # HTML templates
│   ├── landing.html         # Landing page with popup
│   ├── register.html        # User registration
│   ├── login.html           # User/admin login
│   ├── cart.html            # Shopping cart
│   ├── product_detail.html  # Product customization
│   ├── admin_*.html         # Admin panels
│   └── ...
├── static/                   # Static files
│   ├── css/style.css        # Global styles
│   ├── images/              # Images
│   └── uploads/             # User-uploaded product images
├── .env                      # Environment variables (YOU CREATE THIS)
├── ENV_TEMPLATE.txt         # Template for .env file
└── SETUP_INSTRUCTIONS.md    # This file
```

---

## 🔒 Security Notes

1. **Never commit .env to Git** - Add it to .gitignore
2. **Change default admin passwords** immediately
3. **Use strong SESSION_SECRET** - Random and long
4. **Keep DATABASE_URL secret** - Contains password
5. **Use HTTPS in production** - For secure transactions

---

## 📧 Email Configuration (Optional)

To enable email notifications:

1. **For Gmail:**
   - Enable 2-Factor Authentication
   - Generate App Password: https://myaccount.google.com/apppasswords
   - Add to .env:
     ```env
     MAIL_USERNAME=your_email@gmail.com
     MAIL_PASSWORD=your_app_password
     ```

2. **For other providers:**
   - Update MAIL_SERVER and MAIL_PORT in .env

---

## 🐛 Troubleshooting

### Database Connection Error
```
Error: connection to server failed
```
**Solution:** 
- Check DATABASE_URL is correct
- Ensure `?sslmode=require` is at the end
- Verify password is correct

### Port Already in Use
```
Error: Address already in use
```
**Solution:**
```bash
# Windows
netstat -ano | findstr :5000
taskkill /PID <PID> /F

# Mac/Linux
lsof -ti:5000 | xargs kill -9
```

### Module Not Found
```
ModuleNotFoundError: No module named 'flask'
```
**Solution:**
- Activate virtual environment
- Run: `pip install -r requirements.txt` (if provided)
- Or install packages manually

---

## 📱 Contact & Support

For issues or questions about The National Scaffolding website, please refer to:
- `ADMIN_GUIDE.md` - Admin panel usage guide
- `replit.md` - Technical architecture documentation

---

## 🎉 You're All Set!

Your National Scaffolding website is ready to go! Visit http://127.0.0.1:5000 and you'll see the welcome popup appear first, then explore the scaffolding and fabrication products.

**Happy Selling! 🚀**
