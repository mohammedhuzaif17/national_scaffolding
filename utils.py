def get_image_url(image_path):
    if not image_path:
        return 'images/no-image.png'

    # If multiple images exist, take only the first one
    if ',' in image_path:
        image_path = image_path.split(',')[0].strip()

    if not image_path:
        return 'images/no-image.png'

    # Remove static/ if present
    if image_path.startswith('static/'):
        image_path = image_path.replace('static/', '', 1)

    # Valid prefixes
    if image_path.startswith(('uploads/', 'images/')):
        return image_path

    # Plain filename → assume uploads/
    return f'uploads/{image_path}'
