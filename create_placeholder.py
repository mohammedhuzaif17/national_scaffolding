#!/usr/bin/env python
"""Create a proper no-image.png placeholder"""

from PIL import Image, ImageDraw, ImageFont
import os

# Create a simple placeholder image
img = Image.new('RGB', (400, 300), color='#f0f0f0')
draw = ImageDraw.Draw(img)

# Draw a simple camera/image icon
# Draw rectangle border
draw.rectangle([50, 30, 350, 250], outline='#999999', width=2)

# Draw a circle (camera lens)
draw.ellipse([130, 80, 270, 220], outline='#999999', width=2)

# Draw smaller circle (camera focus)
draw.ellipse([160, 110, 240, 190], outline='#cccccc', width=1)

# Draw text
text = "No Image Available"
text_color = '#666666'
# Use default font
draw.text((200, 270), text, fill=text_color, anchor="mm")

# Save the image
output_path = os.path.join(
    os.path.dirname(__file__),
    'static/images/no-image.png'
)

img.save(output_path)
print(f'✓ Created placeholder image: {output_path}')
