#! usr/bin/python3
# -*- coding: utf-8 -*-
#
# Autorizacion centralizada (H-03).
#
# Antes, cada vista decidia por su cuenta si comprobaba el rol, y varias acciones de gestion no lo
# comprobaban. Aqui se concentra la regla para que se aplique igual en todas las vistas y que la
# denegacion detenga la peticion (fallar de forma segura).

from functools import wraps

from flask import abort, g


def is_staff(user):
    """
    Personal de soporte: administradores (grupo flicket_admin) y agentes (grupo super_user).

    :param user: usuario de la sesion (g.user).
    :return bool:
    """
    if user is None or not user.is_authenticated:
        return False
    return bool(user.is_admin or user.is_super_user)


def staff_required(view):
    """
    Decorador: solo el personal puede ejecutar la vista; cualquier otro usuario recibe 403.
    Debe colocarse despues de @login_required.
    """

    @wraps(view)
    def wrapper(*args, **kwargs):
        if not is_staff(g.user):
            abort(403)
        return view(*args, **kwargs)

    return wrapper
