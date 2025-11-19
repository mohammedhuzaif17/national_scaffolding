from flask import Flask, render_template_string
import os

app = Flask(__name__)

template_path = os.path.join('templates','admin_scaffoldings.html')
if not os.path.exists(template_path):
    print('Template not found:', template_path)
    raise SystemExit(1)

with open(template_path, 'r', encoding='utf-8') as f:
    t = f.read()

with app.test_request_context('/'):
    try:
        # minimal context expected by template
        ctx = {
            'products': [],
            'url_for': lambda *a, **k: '/',
            'current_user': None
        }
        rendered = render_template_string(t, **ctx)
        print('Rendered OK')
    except Exception as e:
        print('Render error:')
        import traceback
        traceback.print_exc()
        raise
