#!/usr/bin/env python3
import traceback
from app import app, db
from models import Admin, Product
from flask_login import login_user

print('Debugging admin login and vertical_edit')

with app.app_context():
    admin = Admin.query.first()
    if not admin:
        print('No admin found — creating temporary admin')
        admin = Admin(username='devadmin', panel_type='main')
        admin.set_password('devpass')
        db.session.add(admin)
        db.session.commit()
        print('Created admin id', admin.id)
    else:
        print('Found admin', admin.username, 'id', admin.id)

    try:
        with app.test_request_context('/admin/vertical/161/edit', method='GET'):
            from flask import session
            # login admin
            login_user(admin)
            session['user_type'] = 'admin'
            # Now call the view
            from cuplock_routes import vertical_edit
            try:
                rv = vertical_edit(161)
                print('Returned:', type(rv))
                if hasattr(rv, 'status'):
                    print('Status:', rv.status)
                if hasattr(rv, 'headers'):
                    print('Headers:', dict(rv.headers))
            except Exception as e:
                print('Exception while calling vertical_edit:')
                traceback.print_exc()
    except Exception as e:
        print('Exception in test_request_context:')
        traceback.print_exc()
