"""Helpers for current Race selection and write guards."""
from __future__ import annotations

from functools import wraps

from flask import jsonify, session
from flask_login import current_user

from models.race import Race, RACE_STATUS_ACTIVE

SESSION_RACE_KEY = 'current_race_id'


def list_races():
    """Return races ordered for UI: active first, then by created_at desc."""
    return Race.query.order_by(
        Race.status.asc(),  # 'active' before 'archived'
        Race.created_at.desc(),
    ).all()


def resolve_default_race():
    """Prefer most recent non-archived race; else most recent race overall."""
    race = (
        Race.query.filter_by(status=RACE_STATUS_ACTIVE)
        .order_by(Race.created_at.desc())
        .first()
    )
    if race is not None:
        return race
    return Race.query.order_by(Race.created_at.desc()).first()


def get_current_race():
    """Return the Race for this session, repairing an invalid session id."""
    if not current_user.is_authenticated:
        return None

    race_id = session.get(SESSION_RACE_KEY)
    race = Race.query.get(race_id) if race_id else None
    if race is None:
        race = resolve_default_race()
        if race is not None:
            session[SESSION_RACE_KEY] = race.id
    return race


def get_current_race_id():
    race = get_current_race()
    return race.id if race else None


def set_current_race(race_id: str) -> Race | None:
    race = Race.query.get(race_id)
    if race is None:
        return None
    session[SESSION_RACE_KEY] = race.id
    return race


def require_writable_race(race=None):
    """
    Ensure the given (or current) race exists and is writable.

    Returns (race, error_response_or_None).
    """
    if race is None:
        race = get_current_race()
    if race is None:
        return None, (jsonify({'error': 'No race selected. Create a race in Admin first.'}), 400)
    if race.is_archived:
        return race, (jsonify({'error': 'This race is archived and read-only.'}), 403)
    return race, None


def require_writable_race_for_row(row):
    """Guard writes against a row that has race_id / race relationship."""
    race = getattr(row, 'race', None)
    if race is None and getattr(row, 'race_id', None):
        race = Race.query.get(row.race_id)
    if race is None:
        return None, (jsonify({'error': 'Race not found for this record.'}), 400)
    if race.is_archived:
        return race, (jsonify({'error': 'This race is archived and read-only.'}), 403)
    return race, None


def apply_race_filter(query, model, race_id=None):
    """Filter a SQLAlchemy query to the current (or provided) race."""
    if race_id is None:
        race_id = get_current_race_id()
    if race_id is None:
        return query.filter(False)
    return query.filter(model.race_id == race_id)


def writable_race_required(f):
    """Decorator for mutating routes that operate on the current race."""
    @wraps(f)
    def decorated(*args, **kwargs):
        _race, err = require_writable_race()
        if err is not None:
            return err
        return f(*args, **kwargs)
    return decorated
