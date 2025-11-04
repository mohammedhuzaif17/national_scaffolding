# Admin Guide - The National Scaffolding E-Commerce Platform

## Admin Credentials

### National Scaffolding Admin
- **Username:** `admin_scaffolding`
- **Password:** `admin123`
- **Panel Type:** Scaffolding
- **Access URL:** `https://your-domain.com/admin_login`

### Fabrication Admin
- **Username:** `admin_fabrication`
- **Password:** `admin123`
- **Panel Type:** Fabrication
- **Access URL:** `https://your-domain.com/admin_login`

---

## How to Login as Admin

1. Navigate to `/admin_login` (this URL is hidden from regular users)
2. Enter your admin username
3. Enter your admin password
4. Select the correct panel type:
   - Choose "National Scaffolding Admin" for scaffolding products
   - Choose "Fabrication Admin" for fabrication products
5. Click "Admin Login"

**Note:** Admin login is completely separate from user login. Regular users cannot see the admin login link.

---

## Admin Features

### 1. **Product Management**
- Add new products with multiple images
- Edit existing products
- Delete products
- Manage product categories and pricing
- Set rent prices for aluminium scaffolding
- Set weight-based pricing for cuplock systems

### 2. **Order Verification & Payment Tracking**

#### How Payment Verification Works:

When customers place an order, they follow this process:
1. Add products to cart
2. Proceed to checkout
3. See the PhonePe QR code with the exact amount to pay
4. Scan and pay via PhonePe app
5. **Enter their UPI Transaction ID** (minimum 8 characters)
6. Submit order

#### As an Admin, You Can:

1. **View All Orders:**
   - Click "📋 View All Orders" button in the admin panel
   - See complete order history from all customers

2. **Verify Payments:**
   Each order shows:
   - **Order ID:** Unique identifier
   - **Customer Name:** Who placed the order
   - **Date & Time:** When the order was placed
   - **Total Amount:** How much should have been paid
   - **Transaction ID:** The UPI transaction ID entered by the customer
   - **Status:** Order status (Completed, Pending, etc.)

3. **Validate Transaction IDs:**
   - Transaction IDs are shown in a special monospace font for easy reading
   - You can copy these IDs and verify them in your PhonePe merchant dashboard
   - Cross-check the amount paid matches the order total

#### Payment Verification Steps:

1. Go to Admin Panel → Click "📋 View All Orders"
2. Find the order you want to verify
3. Note the **Transaction ID** and **Total Amount**
4. Log into your PhonePe merchant account
5. Search for the transaction ID
6. Verify:
   - ✅ Transaction ID matches
   - ✅ Amount matches the order total
   - ✅ Payment status is "Success"
   - ✅ Customer details match
7. If everything matches, proceed with order fulfillment and delivery

#### What if Transaction ID is Invalid?

- Contact the customer using their registered email/phone
- Ask for proof of payment (screenshot)
- Request the correct transaction ID
- Update the order status accordingly

---

## Order Management

### Viewing Order Details:
1. In the Admin Orders page, click "View Items" button for any order
2. See all items in the order with:
   - Product names
   - Quantities
   - Unit prices
   - Customization details (width, height, type, etc.)
   - Item totals

### Order Status:
- **Completed:** ✓ Payment verified, ready for delivery
- **Pending:** Awaiting verification
- **Other:** Custom status as needed

---

## Security Best Practices

1. **Keep Credentials Secure:**
   - Change default passwords after first login
   - Don't share admin credentials
   - Use strong, unique passwords

2. **Always Verify Payments:**
   - Never ship without verifying the transaction ID
   - Check PhonePe dashboard for each order
   - Maintain payment records

3. **Regular Audits:**
   - Review orders periodically
   - Check for suspicious patterns
   - Keep transaction records for accounting

---

## Common Admin Tasks

### Adding a New Product:
1. Click "+ Add New Product"
2. Fill in product details
3. Add multiple image URLs (one per line)
4. Set pricing and categories
5. Click "Save"

### Viewing Customer Orders:
1. Click "📋 View All Orders"
2. Browse all orders sorted by date (newest first)
3. Click "View Items" to see order details
4. Note transaction IDs for verification

### Managing Products:
1. View product list in admin panel
2. Click "Edit" to modify product details
3. Click "Delete" to remove products (confirm first)

---

## Technical Notes

- All prices are calculated server-side for security
- GST (18%) is automatically added at checkout
- Orders are auto-confirmed after transaction ID submission
- Database is automatically backed up via Replit
- Connection pooling ensures stable database performance

---

## Support

For technical issues or questions:
- Check application logs
- Review database connection status
- Ensure all environment variables are set
- Contact development team if needed

---

**Important:** This admin system provides full visibility into customer payments through transaction IDs, allowing you to verify each payment before fulfilling orders. Always cross-check transaction IDs in your PhonePe merchant dashboard before shipping products.
