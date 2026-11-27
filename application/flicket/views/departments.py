#! usr/bin/python3
# -*- coding: utf-8 -*-
#
# Flicket - copyright Paul Bourne: evereux@gmail.com

from flask import abort, flash, g, redirect, request, url_for, render_template
from flask_babel import gettext
from flask_login import login_required

from . import flicket_bp
from application import app, db
from application.flicket.forms.flicket_forms import DepartmentForm
from application.flicket.models.flicket_models import FlicketDepartment
from application.flicket.scripts.access import is_staff, staff_required


# create ticket
@flicket_bp.route(app.config['FLICKET'] + 'departments/', methods=['GET', 'POST'])
@flicket_bp.route(app.config['FLICKET'] + 'departments/<int:page>/', methods=['GET', 'POST'])
@login_required
def departments(page=1):
    # H-03: cualquier usuario puede consultar la lista, pero solo el personal puede crear departamentos.
    if request.method == 'POST' and not is_staff(g.user):
        abort(403)

    form = DepartmentForm()

    query = FlicketDepartment.query.order_by(FlicketDepartment.department.asc())

    if form.validate_on_submit():
        add_department = FlicketDepartment(department=form.department.data)
        db.session.add(add_department)
        db.session.commit()
        flash(gettext('New department "{}" added.'.format(form.department.data)), category='success')
        return redirect(url_for('flicket_bp.departments'))

    _departments = query.paginate(page=page, per_page=app.config['posts_per_page'])

    title = gettext('Departments')

    return render_template('flicket_departments.html',
                           title=title,
                           form=form,
                           page=page,
                           departments=_departments)


@flicket_bp.route(app.config['FLICKET'] + 'department_edit/<int:department_id>/', methods=['GET', 'POST'])
@login_required
@staff_required  # H-03: solo el personal puede editar departamentos
def department_edit(department_id=False):
    if department_id:

        form = DepartmentForm()
        query = FlicketDepartment.query.filter_by(id=department_id).first()
        if query is None:
            abort(404)

        if form.validate_on_submit():
            query.department = form.department.data
            db.session.commit()
            flash(gettext('Department "%(value)s" edited.', value=form.department.data), category='success')
            return redirect(url_for('flicket_bp.departments'))

        form.department.data = query.department

        return render_template('flicket_department_edit.html',
                               title='Edit Department',
                               form=form,
                               department=query
                               )

    return redirect(url_for('flicket_bp.departments'))
