#!/usr/bin/env python
"""Test the get_image_url function fix"""

from cuplock_routes import get_image_url

test_paths = [
    'uploads/abc123_test.jpg',
    'abc123_test.jpg',
    None
]

print('Testing get_image_url() function:')
print('='*70)
for path in test_paths:
    result = get_image_url(path)
    print(f'Input:  {path}')
    print(f'Output: {result}')
    print('-'*70)
