#! usr/bin/python3
# -*- coding: utf-8 -*-
#
# Restablecimiento de contrasena con enlace firmado de un solo uso (H-04).
#
# El flujo original cambiaba la contrasena en cuanto alguien escribia un correo y enviaba la nueva
# contrasena en claro. Ahora solo se envia un enlace firmado con SECRET_KEY que:
#   - caduca a los RESET_TOKEN_MAX_AGE segundos;
#   - incluye una huella de la contrasena actual, de modo que deja de ser valido en cuanto se usa
#     (al cambiar la contrasena cambia la huella) y no puede reutilizarse;
#   - no da acceso a cuentas deshabilitadas.

import hashlib
import hmac

from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from application import app
from application.flicket.models.flicket_user import FlicketUser

RESET_TOKEN_MAX_AGE = 3600  # una hora
_SALT = 'flicket-password-reset'


def _serializer():
    return URLSafeTimedSerializer(app.config['SECRET_KEY'], salt=_SALT)


def _password_fingerprint(user):
    """Huella corta del hash de la contrasena actual; cambia cuando cambia la contrasena."""
    password_hash = user.password if isinstance(user.password, bytes) else str(user.password).encode('utf-8')
    return hashlib.sha256(password_hash).hexdigest()[:16]


def generate_reset_token(user):
    """
    :param user: FlicketUser
    :return str: token firmado para incluir en el enlace de restablecimiento.
    """
    return _serializer().dumps({'id': user.id, 'fp': _password_fingerprint(user)})


def user_from_reset_token(token):
    """
    Devuelve el usuario si el token es valido, no ha caducado y no se ha usado; en cualquier otro
    caso devuelve None (falla cerrada, sin distinguir el motivo).

    :param token: str
    :return FlicketUser or None:
    """
    try:
        data = _serializer().loads(token, max_age=RESET_TOKEN_MAX_AGE)
    except (BadSignature, SignatureExpired):
        return None

    if not isinstance(data, dict):
        return None

    user = FlicketUser.query.filter_by(id=data.get('id')).first()
    if user is None or user.disabled:
        return None

    if not hmac.compare_digest(str(data.get('fp', '')), _password_fingerprint(user)):
        return None

    return user
