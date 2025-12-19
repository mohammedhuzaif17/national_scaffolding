#!/usr/bin/env python3
import urllib.request
import re
import time
import sys

time.sleep(3)

try:
    print('Fetching homepage...')
    html = urllib.request.urlopen('http://127.0.0.1:5001/', timeout=15).read().decode('utf-8')
    
    # Find all image src attributes with uploads path
    srcs = re.findall(r'src="([^"]*uploads[^"]*)"', html)
    
    bad_paths = [s for s in srcs if ',' in s]
    good_paths = [s for s in srcs if ',' not in s]
    
    print(f'\n=== IMAGE PATH TEST RESULTS ===')
    print(f'Total image paths found: {len(srcs)}')
    print(f'Good paths (no commas): {len(good_paths)}')
    print(f'Bad paths (with commas): {len(bad_paths)}')
    
    if bad_paths:
        print(f'\n✗ FAILED - Malformed paths found:')
        for i, p in enumerate(bad_paths[:3], 1):
            print(f'  {i}. {p[:80]}...')
        sys.exit(1)
    else:
        print(f'\n✓ SUCCESS - All image paths are correctly formatted!')
        print('No comma-separated image URLs in homepage HTML')
        sys.exit(0)
        
except Exception as e:
    print(f'✗ Error: {e}')
    sys.exit(1)
