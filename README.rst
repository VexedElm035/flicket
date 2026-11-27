Flicket: análisis de seguridad (Proyecto 1, Fundamentos de programación segura)
=================================================================================

Fork de `evereux/flicket <https://github.com/evereux/flicket>`_ usado como caso de estudio en el curso
*Fundamentos de programación segura* (INAOE, MCTS 2026). Contiene el despliegue de laboratorio, las mitigaciones
de los hallazgos priorizados y las evidencias del análisis.

Ramas y commits
---------------

============================  ==========  =========================================================================
Referencia                    Commit      Contenido
============================  ==========  =========================================================================
Línea base (upstream)         ``adcc3f6`` Código analizado, sin cambios (``adcc3f60057ea09872f033b9364ce74a11113253``)
``master``                    ``41a03f8`` Línea base + despliegue con Docker (laboratorio)
``mitigaciones``              (rama)      Un commit por hallazgo mitigado, scripts, evidencias y este documento
============================  ==========  =========================================================================

Hallazgos mitigados en ``mitigaciones``:

==========  ==========  ======================================================================================
Hallazgo    Commit      Mitigación
==========  ==========  ======================================================================================
H-02        ``4d30cd6`` Borrado de respuestas: 403 a no administradores (falla segura)
H-03        ``0171ac6`` Autorización centralizada por rol (``application/flicket/scripts/access.py``)
H-04        ``94d453a`` Restablecimiento con enlace firmado de un solo uso y respuesta uniforme
H-05        ``75c63ce`` Markdown 3.8.2 (CVE-2025-69534)
H-01        ``fae768c`` Filtro ``|markdown`` con sanitización por lista blanca (``nh3``) y falla segura
==========  ==========  ======================================================================================

Los hallazgos H-06 a H-16 están documentados en el informe, pero no se mitigaron en este repositorio.
Los scripts, las pruebas de regresión y los resultados de pip-audit, Bandit y Semgrep (antes y después) están en
``security/`` (ver ``security/README.md``).

Despliegue de laboratorio
-------------------------

Requisitos: Git y Docker con Compose v2.

1. Clonar y elegir la versión::

       git clone https://github.com/VexedElm035/flicket.git
       cd flicket
       git checkout mitigaciones        # o "master" para la versión vulnerable

2. Crear ``.env`` a partir de la plantilla y poner valores propios en cada variable marcada con
   ``cambia-esto`` (por ejemplo con ``python -c "import secrets; print(secrets.token_urlsafe(32))"``)::

       cp .env.example .env

   ``.env`` está en ``.gitignore``. Si falta una variable, o sigue con el valor de la plantilla, ``docker compose``
   o el contenedor ``web`` se detienen con un mensaje de error en lugar de arrancar con valores por defecto.

3. Construir y levantar::

       docker compose up -d --build

   La aplicación queda en ``http://localhost:5050`` (variable ``PORT``), publicada solo en ``127.0.0.1``. La base
   de datos no publica puertos en el anfitrión. El administrador inicial es ``FLASK_ADMIN_USERNAME`` con
   ``FLASK_ADMIN_PASSWORD``.

4. Para cambiar de rama o de credenciales, reconstruir desde cero (borra los datos del laboratorio)::

       docker compose down -v
       docker compose up -d --build

   MariaDB solo aplica ``DB_PASSWORD`` y ``DB_ROOT_PASSWORD`` al crear el volumen; con un volumen existente se
   conservan las credenciales anteriores.

Reproducir el análisis
----------------------

Con PowerShell 7 y Docker, desde la raíz del repositorio::

    pwsh security/scripts/run_scans.ps1
    pwsh security/scripts/run_scans.ps1 -Commit mitigaciones -Out security/evidencias/scans_mitigaciones
    pwsh security/scripts/run_security_tests.ps1

Aviso
-----

Este repositorio es material académico. El despliegue es solo para laboratorio local y no debe exponerse a
Internet: la rama ``master`` contiene vulnerabilidades conocidas a propósito. Varias de ellas siguen presentes en
la versión vigente de upstream; el canal para reportarlas al mantenedor es el indicado en ``SECURITY.md``.

----

Flicket (README original)
=========================

Flicket is a simple web based ticketing system written in Python using
the flask web framework which supports English and French locales. Additional
locales can be added by following the section `Adding Additional Languages`
within this README.


Documentation
-------------

For documentation and screenshots please visit: https://flicket.readthedocs.io/en/latest/


Upgrading From Earlier Versions
-------------------------------

See the changelog for changes and additional steps to take when upgrading.


Requirements
------------
Prior to installing and running Flicket please read these requirements.

* Python =>3.90

* SQL Database server with JSON support (for example PostgreSQL >=9.2,
  MySQL >=5.7, MariaDB >=10.2, SQLite >=3.9)


Production Environment
----------------------

To serve Flicket within a production environment webservers such as Apache
or nginx are typically used.
