#!/usr/bin/env python
"""Test if vertical product pages render correctly with images"""

from app import app

def test_vertical_product_rendering():
    with app.app_context():
        with app.test_client() as client:
            print("\n" + "="*70)
            print("🧪 TESTING VERTICAL PRODUCT PAGE RENDERING")
            print("="*70)
            
            for product_id in [161, 162]:
                print(f"\n📦 Testing Product {product_id}...")
                response = client.get(f'/cuplock/product/vertical/{product_id}')
                
                print(f"   Status: {response.status_code}")
                
                if response.status_code == 200:
                    html = response.get_data(as_text=True)
                    
                    # Check if image src is in the HTML
                    if 'vertical_product_161.jpg' in html or 'vertical_product_162.jpg' in html:
                        print(f"   ✅ Image filename found in HTML")
                    else:
                        print(f"   ⚠️  Image filename NOT found in HTML")
                    
                    # Check for the display_image_url path
                    if '/static/images/vertical_product_' in html:
                        print(f"   ✅ Correct image path in HTML")
                    else:
                        print(f"   ❌ Image path not rendered correctly")
                    
                    # Look for "No Image Available" text
                    if "No Image Available" in html or "No Image" in html:
                        print(f"   ❌ 'No Image' fallback found - image not loading")
                    else:
                        print(f"   ✅ No 'No Image' fallback - good!")
                else:
                    print(f"   ❌ Page returned {response.status_code}")

if __name__ == '__main__':
    test_vertical_product_rendering()
