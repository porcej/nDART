from datetime import datetime

from flask import render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user

from extensions import db
from models import Race, RACE_STATUS_ACTIVE, RACE_STATUS_ARCHIVED
from blueprints.race_context import set_current_race, list_races
from . import admin_bp
from .utils import admin_required


def _parse_optional_datetime(value):
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


@admin_bp.route('/races')
@login_required
@admin_required
def races():
    """List and manage races."""
    return render_template(
        'admin/races.html',
        races=list_races(),
        username=current_user.name,
        is_admin=True,
        is_manager=current_user.is_manager,
    )


@admin_bp.route('/races', methods=['POST'])
@login_required
@admin_required
def create_race():
    """Create a new race occurrence."""
    name = (request.form.get('name') or '').strip()
    if not name:
        flash('Race name is required.', 'error')
        return redirect(url_for('admin.races'))

    race = Race(
        name=name,
        starts_at=_parse_optional_datetime(request.form.get('starts_at')),
        ends_at=_parse_optional_datetime(request.form.get('ends_at')),
        status=RACE_STATUS_ACTIVE,
    )
    db.session.add(race)
    db.session.commit()
    flash(f'Created race “{race.name}”.', 'success')
    return redirect(url_for('admin.races'))


@admin_bp.route('/races/<race_id>', methods=['POST'])
@login_required
@admin_required
def update_race(race_id):
    """Update race metadata or archive/unarchive."""
    race = Race.query.get_or_404(race_id)
    action = request.form.get('action') or 'update'

    if action == 'archive':
        race.status = RACE_STATUS_ARCHIVED
        db.session.commit()
        flash(f'Archived “{race.name}”. It is now read-only.', 'success')
        return redirect(url_for('admin.races'))

    if action == 'unarchive':
        race.status = RACE_STATUS_ACTIVE
        db.session.commit()
        flash(f'Unarchived “{race.name}”.', 'success')
        return redirect(url_for('admin.races'))

    if action == 'select':
        set_current_race(race.id)
        flash(f'Switched to “{race.name}”.', 'success')
        return redirect(url_for('admin.races'))

    name = (request.form.get('name') or '').strip()
    if not name:
        flash('Race name is required.', 'error')
        return redirect(url_for('admin.races'))

    race.name = name
    race.starts_at = _parse_optional_datetime(request.form.get('starts_at'))
    race.ends_at = _parse_optional_datetime(request.form.get('ends_at'))
    db.session.commit()
    flash(f'Updated “{race.name}”.', 'success')
    return redirect(url_for('admin.races'))


@admin_bp.route('/races/<race_id>', methods=['GET'])
@login_required
@admin_required
def get_race(race_id):
    race = Race.query.get_or_404(race_id)
    return jsonify(race.to_dict())
