#! usr/bin/python3
# -*- coding: utf-8 -*-
#
# Renderizado seguro de Markdown (H-01 y H-05).
#
# Antes, el filtro |markdown de Flask-Markdown convertia el texto con Python-Markdown, que conserva el
# HTML crudo que escribe el usuario, y marcaba el resultado como seguro, de modo que Jinja2 no lo
# escapaba (XSS almacenado). Ahora:
#   - el HTML generado se limpia con una lista blanca de etiquetas, atributos y esquemas de URL (nh3);
#   - cualquier error al convertir se registra en el servidor y el texto se muestra escapado, para que
#     un contenido mal formado no deje el ticket inaccesible (falla segura).

import logging

import markdown
import nh3
from markupsafe import Markup, escape

logger = logging.getLogger(__name__)

ALLOWED_TAGS = {
    'a', 'abbr', 'b', 'blockquote', 'br', 'code', 'del', 'em', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'hr', 'i',
    'img', 'li', 'ol', 'p', 'pre', 'strong', 'table', 'tbody', 'td', 'th', 'thead', 'tr', 'ul',
}
ALLOWED_ATTRIBUTES = {
    'a': {'href', 'title'},
    'img': {'src', 'alt', 'title'},
    'td': {'align'},
    'th': {'align'},
}
URL_SCHEMES = {'http', 'https', 'mailto'}


def render_markdown(text):
    """
    Filtro de Jinja2 que sustituye al de Flask-Markdown: convierte Markdown a HTML y lo sanitiza.

    :param text: contenido escrito por el usuario.
    :return Markup: HTML seguro para insertar en la plantilla.
    """
    if not text:
        return Markup('')

    try:
        html = markdown.markdown(text)
    except Exception:
        logger.exception('No se pudo convertir el contenido Markdown; se muestra como texto.')
        return Markup('<pre>') + escape(text) + Markup('</pre>')

    clean_html = nh3.clean(html, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRIBUTES, url_schemes=URL_SCHEMES,
                           link_rel='noopener noreferrer nofollow')
    # El contenido ya fue sanitizado con lista blanca antes de marcarlo como seguro.
    return Markup(clean_html)  # nosec B704
