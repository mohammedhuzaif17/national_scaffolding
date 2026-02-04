# ADMIN LOGIN - USING NEON DATABASE CREDENTIALS

## Important Change

All hardcoded test credentials have been removed. The application now uses **only the credentials stored in your Neon PostgreSQL database**.

---

## Current Admin Accounts in Neon Database

```
Panel: SCAFFOLDING
  Username: admin
  Panel Type: scaffolding

Panel: FABRICATION
  Username: admin
  Panel Type: fabrication
```

---

## How to Login

### Step 1: Get Your Credentials
Your admin credentials are stored in **Neon Database**, not hardcoded.

Check your Neon console at: https://console.neon.tech

### Step 2: Go to Admin Login
Visit: `/admin_login`

### Step 3: Enter Neon Database Credentials
- **Username:** (from your Neon database)
- **Password:** (from your Neon database setup)
- **Panel:** Select "Scaffolding Admin" or "Fabrication Admin"

### Step 4: Click "Admin Login"
OTP will be sent to: `Cresttechnocrat@gmail.com`

### Step 5: Enter OTP
Check your email and enter the 6-digit code

### Step 6: Success!
You're now logged into your admin panel

---

## About Your Credentials

### Where They're Stored
- **Location:** Neon PostgreSQL database
- **Table:** `admins`
- **Not stored:** In application code or .env files
- **Security:** Passwords are bcrypt hashed

### Database Connection
```
Host: ep-late-poetry-a1qg9sf1-pooler.ap-southeast-1.aws.neon.tech
Database: neondb
User: neondb_owner
Region: AP Southeast (Singapore)
```

### If You Need to Change Credentials

**Option 1: Use Neon Console**
1. Go to https://console.neon.tech
2. Query the `admins` table
3. Update username/password directly

**Option 2: Use SQL Command**
```sql
UPDATE admins SET password_hash = '[new_hash]' 
WHERE username = 'admin' AND panel_type = 'scaffolding';
```

---

## What's Different Now

### Before (Removed)
❌ Hardcoded credentials in scripts
❌ Username/password: admin/admin123
❌ Test data in application code

### Now (Production Ready)
✅ Credentials in secure Neon database
✅ Your actual credentials from Neon setup
✅ No hardcoded secrets in code
✅ Follows security best practices

---

## Key Files

1. **app.py**
   - `create_default_admins()` function reads from environment variables
   - `admin_login()` route verifies against Neon database
   - `admin_otp()` route handles OTP verification

2. **models.py**
   - `Admin` model with username + panel_type unique constraint
   - Password hashing using werkzeug security

3. **.env**
   - DATABASE_URL connects to Neon
   - ADMIN_OTP_EMAIL for OTP delivery
   - Other configuration

---

## Security Notes

1. **Never commit credentials** to version control
2. **Neon database is secure** - credentials are hashed
3. **OTP provides 2FA** - additional layer of security
4. **Environment variables** should not contain raw passwords

---

## Troubleshooting

### "Invalid credentials"
- Check username in Neon database matches what you're entering
- Verify password against Neon database hash
- Try resetting in Neon console

### "OTP not received"
- Check email: Cresttechnocrat@gmail.com
- Look in spam folder
- OTP valid for 5 minutes only

### "Database connection failed"
- Verify DATABASE_URL in .env
- Check Neon database is online
- Verify firewall allows connection

---

## Next Steps

1. ✅ Remove hardcoded credentials from code
2. ✅ Keep credentials in Neon database only
3. ✅ Use Neon credentials to login
4. ✅ Test both admin panels work

**Status:** ✅ USING NEON DATABASE CREDENTIALS ONLY

Generated: February 4, 2026
