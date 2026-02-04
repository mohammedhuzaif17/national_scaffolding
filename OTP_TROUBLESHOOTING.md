# OTP NOT WORKING - TROUBLESHOOTING GUIDE

## Common Issues & Solutions

### Issue 1: OTP Email Not Received
**Symptoms:** 
- You click "Admin Login" but don't receive an email with OTP
- Email arrives late or not at all

**Solutions:**
1. **Check spam folder** - Look in your email's spam/junk folder
2. **Verify email config in .env:**
   ```
   MAIL_SERVER=smtp.gmail.com
   MAIL_PORT=587
   MAIL_USE_TLS=True
   MAIL_USERNAME=Cresttechnocrat@gmail.com
   MAIL_PASSWORD=wwxanavjnwjteuvf
   ADMIN_OTP_EMAIL=Cresttechnocrat@gmail.com
   ```
3. **Request new OTP** - Click "Back to Login" and try again

---

### Issue 2: OTP Entry Shows "Invalid OTP" Even When Correct
**Symptoms:**
- You enter the exact OTP from email
- System says "Invalid OTP"
- Error: "0 attempts remaining" or "Invalid OTP. 2 attempts remaining."

**Root Causes & Fixes:**

#### A. OTP Expired
- **What it is:** OTPs are only valid for 5 minutes
- **Fix:** 
  1. Go back to login
  2. Login again to get a NEW OTP
  3. Enter the new OTP immediately (within 5 minutes)

#### B. Extra Spaces or Formatting
- **What it is:** Accidental spaces in OTP entry
- **Fix:**
  1. The system automatically strips spaces, so this shouldn't be an issue
  2. But you can try: type OTP carefully, check for leading/trailing spaces

#### C. Email Not Received (but thinks it was)
- **What it is:** System says OTP was sent, but you never got the email
- **Fix:**
  1. Check spam folder
  2. Try with a different email
  3. Check the email configuration in .env file

#### D. Browser Cache Issue
- **What it is:** Old OTP session cached in browser
- **Fix:**
  1. Clear browser cache (Ctrl+Shift+Delete)
  2. Close and reopen browser
  3. Try incognito/private browsing

---

### Issue 3: OTP Entry Form Not Accepting Input
**Symptoms:**
- Can't type in the OTP field
- Field is grayed out or disabled

**Causes:**
- OTP has expired (timer reached 0)
- You made 3 wrong attempts

**Fix:**
1. Go back to login (click "Back to Login" button)
2. Login again to get a fresh OTP
3. Try entering the new OTP

---

## How OTP Process Should Work

### Step-by-Step:

```
1. Go to /admin_login
   ↓
2. Enter:
   - Username: admin
   - Password: admin123
   - Panel: Select Scaffolding or Fabrication
   ↓
3. Click "Admin Login"
   ↓
4. OTP generated and sent to email (Cresttechnocrat@gmail.com)
   ↓
5. Redirected to /admin_otp page
   ↓
6. You receive email with OTP (e.g., "Your OTP is: 123456")
   ↓
7. Enter OTP in form and click "Verify OTP"
   ↓
8. System verifies OTP
   ↓
9. If correct → Login successful, redirected to admin dashboard
   If wrong → Shows error, allows 3 attempts total
   ↓
10. If all 3 attempts fail → Go back and start over
```

---

## Testing in Development Mode

### How to Check OTP Without Email

In **development mode**, the OTP is logged to the console for testing:

1. Look at your terminal/console where Flask is running
2. After clicking "Admin Login", look for:
   ```
   [DEV MODE] OTP for testing: 123456
   ```
3. Use that OTP to login

### To Enable Development Mode:
Make sure your .env has:
```
FLASK_ENV=development
```

---

## Verification Checklist

### Before Login:
- [ ] Username is correct: `admin`
- [ ] Password is correct: `admin123`
- [ ] You selected a panel (Scaffolding or Fabrication)

### When Entering OTP:
- [ ] OTP is from the email you received
- [ ] OTP hasn't expired (5 minute limit)
- [ ] No extra spaces before/after OTP
- [ ] You haven't exceeded 3 attempts

### If Still Having Issues:
- [ ] Check email in spam folder
- [ ] Check .env email configuration
- [ ] Clear browser cache and cookies
- [ ] Try in incognito/private mode
- [ ] Restart the Flask application

---

## Email Configuration Troubleshooting

### Gmail SMTP Settings:

If using Gmail, you need an **App Password**, not your regular password.

**To Get App Password:**
1. Go to: https://myaccount.google.com/apppasswords
2. Select "Mail" and "Windows Computer"
3. Copy the 16-character password
4. Paste in .env as `MAIL_PASSWORD`

**Current .env Config:**
```
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=Cresttechnocrat@gmail.com
MAIL_PASSWORD=wwxanavjnwjteuvf
ADMIN_OTP_EMAIL=Cresttechnocrat@gmail.com
```

---

## Emergency Access

If you absolutely cannot receive the OTP:

**Option 1: Disable OTP Temporarily**
Edit `app.py` and comment out the OTP verification section:
```python
# Skip OTP in emergency
# if not check_password_hash(otp_entry.otp_hash, otp):
#     return render_template(...)
# 
# Just login directly:
login_user(admin)
```

**Option 2: Use Test Credentials**
Test user accounts are available for normal logins (not admin):
- Username: test_user
- Go to /login instead of /admin_login

---

## Contact Information

If none of these solutions work:
1. Check the application logs for error messages
2. Verify email configuration in .env
3. Ensure Gmail "Less secure app access" is enabled (if using Gmail)

---

**Last Updated:** February 4, 2026
**Status:** OTP Logic Verified Working ✅
