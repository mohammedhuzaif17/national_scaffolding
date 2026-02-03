#!/usr/bin/env python3
import traceback
from app import app
from cuplock_routes import vertical_edit

print('Debugging vertical_edit directly')

with app.app_context():
    try:
        # create a fake request context
        with app.test_request_context('/admin/vertical/161/edit', method='GET'):
            # set admin session
            from flask import session
            session['user_type'] = 'admin'

            # call the view function directly
            rv = vertical_edit(161)
            print('Returned:', type(rv))
            # If it returned a Response, print status and headers
            try:
                status = getattr(rv, 'status', None)
                print('Status:', status)
                if hasattr(rv, 'headers'):
                    print('Headers:', dict(rv.headers))
                    if 'Location' in rv.headers:
                        print('Redirect Location:', rv.headers['Location'])
            except Exception:
                pass
    except Exception as e:
        print('Exception raised:')
        traceback.print_exc()
