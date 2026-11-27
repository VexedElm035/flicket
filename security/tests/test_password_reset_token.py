"""
Prueba de regresion de H-04 (restablecimiento de contrasena sin verificar al titular).

Carga application/flicket/scripts/password_reset.py con la aplicacion y el modelo de usuario simulados, y comprueba
que el enlace firmado solo es valido para su titular, una sola vez y durante su vigencia.

Uso: python security/tests/test_password_reset_token.py [ruta/a/password_reset.py]
"""
import importlib.util
import sys
import time
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
src = sys.argv[1] if len(sys.argv) > 1 else ROOT / "application/flicket/scripts/password_reset.py"


class FakeUser:
    def __init__(self, uid, pw, disabled=False):
        self.id, self.password, self.disabled = uid, pw, disabled


USERS = {}


class FakeQuery:
    def filter_by(self, id=None):
        self._u = USERS.get(id)
        return self

    def first(self):
        return self._u


app_mod = types.ModuleType("application")
app_mod.app = types.SimpleNamespace(config={"SECRET_KEY": "clave-de-prueba-" + "k" * 16})
user_mod = types.ModuleType("application.flicket.models.flicket_user")
user_mod.FlicketUser = types.SimpleNamespace(query=FakeQuery())
for name, mod in {"application": app_mod,
                  "application.flicket": types.ModuleType("application.flicket"),
                  "application.flicket.models": types.ModuleType("application.flicket.models"),
                  "application.flicket.models.flicket_user": user_mod}.items():
    sys.modules[name] = mod

spec = importlib.util.spec_from_file_location("password_reset", src)
pr = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pr)

u = FakeUser(1, b"$2b$12$hashviejo")
USERS[1] = u
t = pr.generate_reset_token(u)
results = [
    ("token valido devuelve al usuario", pr.user_from_reset_token(t) is u),
    ("token manipulado se rechaza", pr.user_from_reset_token(t[:-2] + "xx") is None),
    ("token basura se rechaza", pr.user_from_reset_token("abc") is None),
]
u.password = b"$2b$12$hashnuevo"
results.append(("token ya usado (cambio de contrasena) se rechaza", pr.user_from_reset_token(t) is None))
t2 = pr.generate_reset_token(u)
u.disabled = True
results.append(("cuenta deshabilitada se rechaza", pr.user_from_reset_token(t2) is None))
u.disabled = False
pr.RESET_TOKEN_MAX_AGE = 1
time.sleep(2.2)
results.append(("token caducado se rechaza", pr.user_from_reset_token(t2) is None))
del USERS[1]
pr.RESET_TOKEN_MAX_AGE = 3600
results.append(("usuario inexistente se rechaza",
                pr.user_from_reset_token(pr.generate_reset_token(FakeUser(1, b"x"))) is None))

for name, ok in results:
    print(("PASA " if ok else "FALLA") + "  " + name)
sys.exit(0 if all(ok for _, ok in results) else 1)
