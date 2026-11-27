"""
Comprobacion de H-05 (CVE-2025-69534 en Python-Markdown < 3.8.1).

Convierte una declaracion incompleta y reporta si el convertidor lanza una excepcion. El resultado depende de la
version de Markdown y tambien de la de CPython (gh-77057, corregido en 3.11.14), por eso se ejecuta con varias
combinaciones; ver security/scripts/run_security_tests.ps1.

Uso: python security/tests/check_markdown_cve.py
"""
import sys

import markdown

try:
    markdown.Markdown().convert("<![")
    result = "sin error"
except Exception as exc:  # noqa: BLE001 - se reporta cualquier excepcion del convertidor
    result = "FALLA (" + type(exc).__name__ + ")"
print("python", sys.version.split()[0], "| markdown", markdown.__version__, "|", result)
