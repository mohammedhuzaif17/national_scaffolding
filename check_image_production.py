#!/usr/bin/env python
"""
Utility to check production image availability and provide fallback strategy
This helps diagnose why images show 404 in production
"""

import os
import sys
from app import app

def check_image_availability():
    """Check if images are available and suggest fixes"""
    with app.app_context():
        upload_folder = app.config.get('UPLOAD_FOLDER', 'static/uploads')
        images_folder = 'static/images'
        
        print("\n" + "="*70)
        print("🖼️  IMAGE AVAILABILITY CHECK")
        print("="*70)
        
        # Check upload folder
        print(f"\n📁 Upload Folder: {upload_folder}")
        if os.path.exists(upload_folder):
            files = os.listdir(upload_folder)
            print(f"   ✅ EXISTS - {len(files)} files found")
        else:
            print(f"   ❌ MISSING - Folder does not exist")
        
        # Check images folder
        print(f"\n📁 Images Folder: {images_folder}")
        if os.path.exists(images_folder):
            files = os.listdir(images_folder)
            print(f"   ✅ EXISTS - {len(files)} files found")
            for f in files:
                print(f"      - {f}")
        else:
            print(f"   ❌ MISSING - Folder does not exist")
        
        print(f"\n💡 PRODUCTION ISSUE ANALYSIS:")
        print(f"   If you're seeing 404 errors for product images in production:")
        print(f"   1. Render.com uses ephemeral file systems - uploaded files are lost on deployment")
        print(f"   2. Solutions:")
        print(f"      - Use a CDN or cloud storage (AWS S3, Cloudinary, etc.)")
        print(f"      - Commit image files to Git (if static)")
        print(f"      - Use database blob storage (not recommended)")
        print(f"   3. For now, ensure no-image.png exists as fallback")
        print(f"\n✅ Fallback Image Status:")
        fallback = 'static/images/no-image.png'
        if os.path.exists(fallback):
            size = os.path.getsize(fallback)
            print(f"   ✅ {fallback} exists ({size} bytes)")
        else:
            print(f"   ❌ {fallback} missing!")
        
        print("\n" + "="*70)

if __name__ == '__main__':
    try:
        check_image_availability()
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
