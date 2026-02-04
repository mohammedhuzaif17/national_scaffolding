# 🚀 QUICK START: ADMIN LOGIN & ORDERS

## 🔐 Admin Login Credentials

```
Username: admin
Password: admin123
```

## 📋 How to Access Admin Orders

### Step 1: Go to Login Page
Visit: `/admin_login`

### Step 2: Enter Credentials
- **Username:** `admin`
- **Password:** `admin123`
- **Select Panel:** 
  - Choose "National Scaffolding Admin" for Scaffolding orders
  - Choose "Fabrication Admin" for Fabrication orders

### Step 3: Receive OTP
An OTP will be sent to: `{YOUR_ADMIN_EMAIL}`

### Step 4: Enter OTP
Check your email and enter the 6-digit OTP

### Step 5: View Orders
You'll be redirected to the dashboard. Click "View Transactions" or go to `/admin_orders`

---

## 📊 What You'll See

### All Orders (23 Total)
- **Pending Verification:** Orders waiting for payment confirmation
- **Completed:** Orders that have been verified and paid
- **Rejected:** Orders that were rejected

### For Each Order:
- Order ID and date
- Customer name and contact details
- Items purchased (if any)
- Total amount
- Payment status
- Action buttons to verify or reject payment

---

## 🎯 Common Tasks

### Verify a Payment
1. Click "Verify Payment" button on pending order
2. Confirm the amount received
3. Click "Verify" to complete

### Reject a Payment
1. Click "Reject" button on pending order
2. Enter reason for rejection
3. Click "Reject" to deny order

### View Order Details
1. Click "View Details" button
2. See customer information and items
3. View payment history

---

## ⚠️ Important Notes

### OTP Expiration
- OTP valid for: 5 minutes
- Maximum attempts: 3
- After 3 failed attempts, login again

### Both Admin Types
- Same username/password for both panels
- Select the correct panel during login
- Each panel shows different category orders

### What's Different Between Panels?

**Scaffolding Admin sees:**
- Aluminium products
- H-Frames products
- Cuplock products
- Accessories
- Vertical Cuplock

**Fabrication Admin sees:**
- Steel products
- Custom fabrication
- Fabrication parts
- Custom work

---

## 🔄 Database Status

✅ **PostgreSQL:** Connected and working
✅ **Admin Accounts:** Created (both scaffolding and fabrication)
✅ **Orders:** All 23 orders visible and accessible
✅ **OrderItems:** 3 orders with items (new orders), 20 test orders

---

## 🐛 Troubleshooting

### "Admin not found" error
- Check username: `admin`
- Check password: `admin123`
- Select a panel (Scaffolding or Fabrication)

### "OTP not received"
- Check ADMIN_OTP_EMAIL env variable is set
- Check spam folder
- Request new OTP (login again)

### "Orders not showing"
- Make sure you selected the correct panel
- Refresh the page
- Check OTP verification was successful

---

## 📞 Need Help?

All issues have been resolved. If you encounter any problems:

1. Check the ADMIN_FIXES_REPORT.md file for detailed information
2. Run `python verify_all_fixes.py` to test the system
3. Check the database logs for errors

---

**Last Updated:** February 4, 2026
**Status:** ✅ Ready to Use
