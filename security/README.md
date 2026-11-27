# Evidencias de seguridad (Proyecto 1, Evaluación 2)

Scripts y resultados del análisis de seguridad de Flicket.

- **Línea base:** `adcc3f60057ea09872f033b9364ce74a11113253` (upstream `evereux/flicket`).
- **Despliegue de laboratorio:** `41a03f8` (rama `master`).
- **Mitigaciones:** rama `mitigaciones`, un commit por hallazgo.

| Hallazgo | Commit | Mitigación |
|---|---|---|
| H-02 Borrado de respuestas con falla abierta (CWE-862/636) | `4d30cd6` | `delete_post` devuelve 403 a no administradores y 404 si no existe |
| H-03 Acciones de gestión sin control de rol (CWE-862) | `0171ac6` | Autorización centralizada `access.py` (`staff_required`) |
| H-04 Restablecimiento sin verificar al titular (CWE-640/338/204) | `94d453a` | Enlace firmado de un solo uso con caducidad, respuesta uniforme, `secrets` |
| H-05 Markdown 3.5.1, CVE-2025-69534 | `75c63ce` | Markdown 3.8.2; falla segura en el filtro (ver H-01) |
| H-01 XSS almacenado vía `\|markdown` (CWE-79) | `fae768c` | Filtro propio con sanitización por lista blanca (`nh3`) y falla segura |

## Contenido

```
security/
├── scripts/
│   ├── run_scans.ps1             pip-audit, Bandit y Semgrep sobre un commit (contenedores desechables, código en solo lectura)
│   └── run_security_tests.ps1    pruebas de regresión de H-01, H-04 y H-05
├── tests/
│   ├── test_markdown_render.py       H-01 y falla segura de H-05 (8 casos)
│   ├── test_password_reset_token.py  H-04 (7 casos)
│   └── check_markdown_cve.py         H-05, matriz CPython × Markdown
└── evidencias/
    ├── scans_linea_base/     resultados sobre adcc3f6
    ├── scans_mitigaciones/   resultados sobre fae768c
    └── pruebas/              salida de las pruebas de regresión
```

Cada carpeta de evidencias incluye `commit.txt` con el commit analizado y `*_version.txt` con la versión de la herramienta.

## Reproducción

Requisitos: Git, PowerShell 7 y Docker. Desde la raíz del repositorio:

```powershell
pwsh security/scripts/run_scans.ps1
pwsh security/scripts/run_scans.ps1 -Commit mitigaciones -Out security/evidencias/scans_mitigaciones
pwsh security/scripts/run_security_tests.ps1
```

Versiones fijadas: pip-audit 2.9.0, Bandit 1.8.6, Semgrep 1.140.0 e imágenes `python:3.11-slim`.

## Comparativo de herramientas

| Herramienta | Línea base (`adcc3f6`) | Mitigaciones (`fae768c`) | Cambio |
|---|---|---|---|
| pip-audit | 7 paquetes, 17 avisos | 6 paquetes, 16 avisos | Desaparece Markdown 3.5.1 (H-05). Siguen cryptography, jinja2, flask, flask-httpauth, python-dotenv y werkzeug (documentados, fuera del alcance de las 5 mitigaciones). |
| Bandit | 5 | 4 | Desaparece un B311 (`random` en `generate_password`, H-04). |
| Semgrep | 18 | 20 | Dos alertas nuevas, revisadas y descartadas (abajo). |

**Alertas nuevas de Semgrep, validadas manualmente como falsos positivos:**

- `explicit-unescape-with-markup` en `markdown_render.py:53`. El `Markup()` se aplica sólo después de sanitizar con lista blanca; ese es justamente el control de H-01. Las pruebas de `test_markdown_render.py` lo verifican.
- `var-in-href` en `email_password_reset.html:11`. El enlace lo arma el servidor (`base_url` de la configuración del administrador + `url_for` + token firmado, en `views/login.py`); no contiene datos que controle el usuario que pide el restablecimiento.

Las herramientas automáticas no detectaron H-02, H-03 ni H-04 (fallas de lógica de autorización y de diseño); se encontraron con revisión manual y se confirmaron con pruebas de concepto en el laboratorio.
