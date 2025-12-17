# Hero Background Image Setup - Complete Guide

## What Has Been Done ✅

I've successfully added a **hero section with background image support** to your main webpage. The changes include:

### 1. **CSS Styling Added**
- `.hero-section` - Full-width hero container with background image support
- `.hero-content` - Centered content with animation
- Responsive design for desktop, tablet, and mobile devices
- Dark overlay (65% opacity) to ensure text readability over the image
- Smooth fade-in animation when page loads

### 2. **HTML Structure Updated**
- New hero section with:
  - Main title: "The National Scaffolding"
  - Tagline: "Since 2015"
  - Description text
  - "Go to Fabrications" button with gold styling
  
### 3. **Responsive Features**
- **Desktop**: Full hero section with background-attachment: fixed (parallax effect)
- **Tablet (768px)**: Slightly smaller, background-attachment: scroll
- **Mobile (480px)**: Compact version with proper padding

## How to Complete Setup 📸

### Step 1: Prepare Your Image
1. Open your scaffolding image (Image 2 from your screenshots)
2. Ensure it's in landscape orientation (wider than tall)
3. Recommended size: 1600px wide × 900px tall or similar ratio
4. Save as JPEG for best performance

### Step 2: Save the Image File
1. Navigate to: `c:\Users\smary\Downloads\final\static\images\`
2. Save your image with the filename: **scaffolding-hero.jpg**
3. File should be ready to use!

### Step 3: Test on Website
1. Restart Flask server (or refresh if auto-reload is on)
2. Visit: http://127.0.0.1:5001
3. You should see the hero section at the top with the scaffolding image as background

## Visual Layout 🎨

```
┌─────────────────────────────────────────┐
│                                         │
│    🖼️  Scaffolding Background Image     │
│         (Landscape Mode)                │
│                                         │
│    The National Scaffolding             │
│    Since 2015                           │
│    "Wide Range of Manufacturers..."     │
│                                         │
│    [Go to Fabrications Button]          │
│                                         │
└─────────────────────────────────────────┘
        ↓
┌─────────────────────────────────────────┐
│    Our Products                         │
│                                         │
│  [ALL PRODUCTS] [ALUMINIUM] [H FRAMES] │
│  [CUPLOCK] [ACCESSORIES]               │
│                                         │
│  Product Grid Below...                  │
└─────────────────────────────────────────┘
```

## File Changes Made 📝

### Modified Files:
- **templates/national_scaffoldings.html**
  - Added hero section CSS (150+ lines)
  - Added hero section HTML structure
  - Removed duplicate page header content
  - Moved "Our Products" content below hero

## Key Features 🌟

✅ **Full-width landscape background image** - Spans entire browser width
✅ **Dark overlay** - 65% opacity ensures text is always readable
✅ **Responsive design** - Works on all devices
✅ **Smooth animations** - Fade-in effect on page load
✅ **Professional styling** - Matches your website's royal blue & gold theme
✅ **Parallax effect** - Background stays fixed while scrolling on desktop
✅ **Mobile optimized** - Smaller hero on mobile for better performance

## Styling Details 🎯

- **Hero Height**: 450px (desktop), 350px (tablet), 300px (mobile)
- **Text Color**: White with text shadow for readability
- **Button**: Gold gradient matching your site theme
- **Overlay**: Linear gradient from darker to lighter blue
- **Font Size**: 3.5rem on desktop, responsive on smaller screens

## If Image Doesn't Show 🔍

Check these things:
1. ✓ File exists: `static/images/scaffolding-hero.jpg`
2. ✓ Filename is exactly correct (case-sensitive on some systems)
3. ✓ Image format is .jpg or .png
4. ✓ Server has been restarted
5. ✓ Browser cache cleared (Ctrl+Shift+Delete)
6. ✓ File size is reasonable (< 1MB)

## Customization Options 🛠️

### To Change Image Path:
Edit line in national_scaffoldings.html:
```
background: linear-gradient(...), url('{{ url_for("static", filename="images/scaffolding-hero.jpg") }}');
```

### To Adjust Overlay Darkness:
Change the opacity (currently 0.65):
```
background: linear-gradient(rgba(0, 29, 61, 0.65), rgba(0, 29, 61, 0.65)), url(...);
```
Lower value = lighter overlay, higher = darker

### To Remove Parallax Effect:
Change `background-attachment: fixed;` to `scroll;`

### To Change Hero Height:
Modify `min-height: 450px;` in `.hero-section`

## Browser Support ✅

Works on all modern browsers:
- Chrome/Chromium
- Firefox
- Safari
- Edge
- Mobile browsers

---

**Status**: Ready to use! Just add your image file and refresh your website. 🚀
