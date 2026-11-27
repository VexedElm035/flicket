#! usr/bin/python3
# -*- coding: utf-8 -*-
#
# Flicket - copyright Paul Bourne: evereux@gmail.com

from urllib.parse import urlparse, urljoin

from flask import flash
from flask import g
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for
from flask_login import current_user
from flask_login import login_user
from flask_login import logout_user
from flask_principal import Identity
from flask_principal import identity_changed
from flask_babel import gettext
from sqlalchemy import func
from sqlalchemy import or_

from application import app, lm, db, flicket_bp
from application import __version__
from application.flicket_admin.models.flicket_config import FlicketConfig
from application.flicket.forms.form_login import LogInForm
from application.flicket.forms.form_login import PasswordResetForm, PasswordResetConfirmForm
from application.flicket.models.flicket_user import FlicketUser
from application.flicket.scripts.email import FlicketMail
from application.flicket.scripts.flicket_config import set_flicket_config
from application.flicket.scripts.functions_login import check_password_format, password_requirements
from application.flicket.scripts.hash_password import hash_password
from application.flicket.scripts.password_reset import (RESET_TOKEN_MAX_AGE,
                                                       generate_reset_token,
                                                       user_from_reset_token)


# functions for redirecting user back from whence they came.
def is_safe_url(target):
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc


def get_redirect_target():
    for target in request.values.get('next'), request.referrer:
        if not target:
            continue
        if is_safe_url(target):
            return target


@lm.user_loader
def load_user(user_id):
    return FlicketUser.query.get(int(user_id))


# before any view is generated the user must be checked and application configuration details pulled from the database.
@app.before_request
def before_request():
    set_flicket_config()
    g.user = current_user

    # reset the user token if the user is authenticated and token is expired.
    if g.user.is_authenticated and hasattr(g.user, 'token') and not g.user.disabled:
        if FlicketUser.check_token(g.user.token) is None:
            g.user.get_token()
            db.session.commit()

    # used in the page footer
    g.__version__ = __version__

    # page title
    application_title = FlicketConfig.query.first().application_title

    g.application_title = application_title


# add 403 error handler
@app.errorhandler(403)
def not_found_error(error):
    return render_template('403.html'), 403


# add 404 error handler
@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404


# handle unexpected errors
@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500


# login page
@flicket_bp.route(app.config['WEBHOME'] + 'login', methods=['GET', 'POST'])
def login():
    # if the user is already logged in redirect to homepage.
    if g.user is not None and g.user.is_authenticated:
        return redirect(url_for('flicket_bp.index'))
    # load the LogInForm from forms.py
    form = LogInForm()

    if form.validate_on_submit():
        user = FlicketUser.query.filter(
            or_(FlicketUser.username == form.username.data,
                func.lower(FlicketUser.email) == form.username.data.lower())).first()
        identity_changed.send(app, identity=Identity(user.id))
        login_user(user, remember=form.remember_me.data)
        # set the user token, authentication token is required for api use.
        user.get_token()
        db.session.commit()
        if user.email is None or user.email == '':
            flash(gettext('Please set your email and job title.'), category='danger')
            return redirect(url_for('flicket_bp.user_details'))
        else:
            flash(gettext('You were logged in successfully.'), category='success')
        return redirect(url_for('flicket_bp.index'))

    return render_template('flicket_login.html', title='Log In', form=form)


# logout page
@flicket_bp.route(app.config['WEBHOME'] + 'logout')
def logout():
    g.user.revoke_token()
    db.session.commit()
    logout_user()
    flash(gettext('You were logged out successfully.'), category='success')
    return redirect(url_for('flicket_bp.index'))


# reset users password
@flicket_bp.route(app.config['WEBHOME'] + 'password_reset', methods=['GET', 'POST'])
def password_reset():
    form = PasswordResetForm()

    if form.validate_on_submit():
        # H-04: la solicitud ya no cambia la contrasena. Solo se envia un enlace firmado al titular,
        # y la respuesta es identica exista o no el correo (sin oraculo de enumeracion ni error 500).
        user = FlicketUser.query.filter_by(email=form.email.data).first()
        if user is not None and not user.disabled:
            try:
                email = FlicketMail()
                reset_url = app.config['base_url'] + url_for('flicket_bp.password_reset_confirm',
                                                             token=generate_reset_token(user))
                email.password_reset(user, reset_url, RESET_TOKEN_MAX_AGE // 60)
            except Exception:
                # Falla segura: el error se registra en el servidor y el usuario ve la misma respuesta.
                app.logger.exception('No se pudo enviar el correo de restablecimiento.')

        flash(gettext('If the address is registered, you will receive an email with a link to reset your '
                      'password.'))
        return redirect(url_for('flicket_bp.login'))

    title = 'Password Reset'
    return render_template('flicket_password_reset.html', form=form, title=title)


# H-04: el titular abre el enlace firmado y elige su nueva contrasena
@flicket_bp.route(app.config['WEBHOME'] + 'password_reset/<token>', methods=['GET', 'POST'])
def password_reset_confirm(token):
    user = user_from_reset_token(token)
    if user is None:
        flash(gettext('The password reset link is invalid or has expired.'), category='warning')
        return redirect(url_for('flicket_bp.password_reset'))

    form = PasswordResetConfirmForm()

    if form.validate_on_submit():
        if not check_password_format(form.password.data, user.username, user.email):
            flash(password_requirements, category='warning')
        else:
            # Al cambiar la contrasena cambia su huella, por lo que el enlace deja de ser valido.
            user.password = hash_password(form.password.data)
            db.session.commit()
            flash(gettext('Your password has been changed. Please log in.'), category='success')
            return redirect(url_for('flicket_bp.login'))

    title = 'Set New Password'
    return render_template('flicket_password_reset_confirm.html', form=form, title=title)
