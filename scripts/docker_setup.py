#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys

# Ensure basedir is in sys.path
basedir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if basedir not in sys.path:
    sys.path.insert(0, basedir)

from application import app, db
from application.commands import (
    create_admin,
    create_notifier,
    create_admin_group,
    create_default_ticket_status,
    create_default_priority_levels,
    create_default_depts,
    set_email_config,
    flicket_config
)
from application.flicket_admin.models.flicket_config import FlicketConfig
from application.flicket.models.flicket_user import FlicketGroup, FlicketUser


def auto_setup():
    with app.app_context():
        admin_username = os.environ.get('FLASK_ADMIN_USERNAME', 'admin')
        # Sin contrasena por defecto: docker-entrypoint.sh ya verifico que la variable exista.
        admin_password = os.environ['FLASK_ADMIN_PASSWORD']
        admin_email = os.environ.get('FLASK_ADMIN_EMAIL', 'admin@example.com')
        base_url = os.environ.get('FLASK_BASE_URL', 'http://localhost:5000')

        print(f"Checking Flicket configuration (Base URL: {base_url})...")
        if FlicketConfig.query.count() == 0:
            set_config = FlicketConfig(
                posts_per_page=flicket_config['posts_per_page'],
                allowed_extensions=', '.join(flicket_config['allowed_extensions']),
                ticket_upload_folder=flicket_config['ticket_upload_folder'],
                avatar_upload_folder=flicket_config['avatar_upload_folder'],
                base_url=base_url,
                application_title='Flicket',
                mail_max_emails=10,
                mail_port=465
            )
            db.session.add(set_config)
            db.session.commit()
            print("Default FlicketConfig created.")

        set_email_config(silent=True)
        create_admin(username=admin_username, password=admin_password, email=admin_email, job_title='admin', silent=False)
        create_notifier()
        create_admin_group(silent=False)

        # Ensure the specified admin user is in flicket_admin and super_user groups
        user = FlicketUser.query.filter_by(username=admin_username).first()
        if user:
            for group_name in [app.config['ADMIN_GROUP_NAME'], app.config['SUPER_USER_GROUP_NAME']]:
                group = FlicketGroup.query.filter_by(group_name=group_name).first()
                if group and user not in group.users:
                    group.users.append(user)

        create_default_ticket_status(silent=False)
        create_default_priority_levels(silent=False)
        create_default_depts(silent=False)

        db.session.commit()
        print("Database setup complete.")


if __name__ == '__main__':
    auto_setup()
