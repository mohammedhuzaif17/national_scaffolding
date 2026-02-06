def create_default_admins():
    """
    Create admin accounts with plain text passwords (NOT RECOMMENDED for production)
    Username: admin_scaffolding / admin_fabrication
    Password: admin123 for both
    """
    with app.app_context():
        try:
            app.logger.info("=== Creating/Updating Admin Accounts ===")
            
            # Create scaffolding admin
            scaffolding_admin = Admin.query.filter_by(
                username='admin_scaffolding',
                panel_type='scaffolding'
            ).first()
            
            if not scaffolding_admin:
                scaffolding_admin = Admin(
                    username='admin_scaffolding',
                    panel_type='scaffolding'
                )
                scaffolding_admin.set_password('admin123')
                db.session.add(scaffolding_admin)
                app.logger.info("✅ Created scaffolding admin: admin_scaffolding")
            else:
                # Ensure password is set correctly
                scaffolding_admin.set_password('admin123')
                app.logger.info("✅ Updated scaffolding admin password")
            
            # Create fabrication admin
            fabrication_admin = Admin.query.filter_by(
                username='admin_fabrication',
                panel_type='fabrication'
            ).first()
            
            if not fabrication_admin:
                fabrication_admin = Admin(
                    username='admin_fabrication',
                    panel_type='fabrication'
                )
                fabrication_admin.set_password('admin123')
                db.session.add(fabrication_admin)
                app.logger.info("✅ Created fabrication admin: admin_fabrication")
            else:
                # Ensure password is set correctly
                fabrication_admin.set_password('admin123')
                app.logger.info("✅ Updated fabrication admin password")
            
            db.session.commit()
            
            app.logger.info("=" * 60)
            app.logger.info("ADMIN CREDENTIALS (Plain Text - Change in Production!):")
            app.logger.info("=" * 60)
            app.logger.info("Scaffolding: admin_scaffolding / admin123")
            app.logger.info("Fabrication: admin_fabrication / admin123")
            app.logger.info("=" * 60)
            app.logger.info("✅ Admin creation process completed")
            
        except Exception as e:
            app.logger.error(f"❌ Error creating admins: {e}")
            db.session.rollback()