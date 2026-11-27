"""
Prueba de regresion de H-01 (XSS almacenado) y de la falla segura de H-05.

Carga application/flicket/scripts/markdown_render.py de forma aislada (sin levantar la aplicacion ni la base de
datos) y comprueba que el HTML peligroso se elimina, que el formato legitimo se conserva y que un error del
convertidor no se propaga.

Uso: python security/tests/test_markdown_render.py [ruta/a/markdown_render.py]
"""
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
src = sys.argv[1] if len(sys.argv) > 1 else ROOT / "application/flicket/scripts/markdown_render.py"

spec = importlib.util.spec_from_file_location("markdown_render", src)
mr = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mr)
r = mr.render_markdown

checks = []
out = r('<img src=x onerror="alert(1)">')
checks.append(("img con onerror: se elimina el manejador", "onerror" not in out))
out = r("<script>alert(1)</script> texto")
checks.append(("script: se elimina la etiqueta", "<script" not in out))
out = r("[enlace](javascript:alert(1))")
checks.append(("enlace javascript: se elimina el esquema", "javascript:" not in out))
out = r('<a href="https://ejemplo.test" onclick="x()">a</a>')
checks.append(("atributo onclick: se elimina", "onclick" not in out and "https://ejemplo.test" in out))
out = r("**negrita**, *cursiva* y `codigo`\n\n- uno\n- dos\n\n> cita")
checks.append(("formato permitido se conserva",
               all(t in out for t in ("<strong>", "<em>", "<code>", "<li>", "<blockquote>"))))
out = r("[sitio](https://ejemplo.test)")
checks.append(("enlaces con rel=noopener", 'rel="noopener noreferrer nofollow"' in out))
checks.append(("texto vacio", r("") == "" and r(None) == ""))

# Falla segura: se simula la excepcion que lanza Markdown 3.5.1 con CVE-2025-69534.
mr.logger.disabled = True
original = mr.markdown.markdown
mr.markdown.markdown = lambda text: (_ for _ in ()).throw(AssertionError("simulado"))
out = r("<b>x</b>")
mr.markdown.markdown = original
checks.append(("error al convertir: texto escapado, sin excepcion", out == "<pre>&lt;b&gt;x&lt;/b&gt;</pre>"))

for name, ok in checks:
    print(("PASA " if ok else "FALLA") + "  " + name)
sys.exit(0 if all(ok for _, ok in checks) else 1)
