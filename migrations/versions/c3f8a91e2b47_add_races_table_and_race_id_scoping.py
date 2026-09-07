"""add races table and race_id scoping

Revision ID: c3f8a91e2b47
Revises: ab6c1b153471
Create Date: 2026-09-06 20:05:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c3f8a91e2b47'
down_revision = 'ab6c1b153471'
branch_labels = None
depends_on = None

DEFAULT_RACE_ID = '00000000-0000-4000-8000-000000000001'


def upgrade():
    op.create_table(
        'races',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('starts_at', sa.DateTime(), nullable=True),
        sa.Column('ends_at', sa.DateTime(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )

    # Seed default race for existing data
    races = sa.table(
        'races',
        sa.column('id', sa.String),
        sa.column('name', sa.String),
        sa.column('starts_at', sa.DateTime),
        sa.column('ends_at', sa.DateTime),
        sa.column('status', sa.String),
        sa.column('created_at', sa.DateTime),
    )
    op.execute(
        races.insert().values(
            id=DEFAULT_RACE_ID,
            name='Default Race',
            starts_at=None,
            ends_at=None,
            status='active',
            created_at=sa.func.now(),
        )
    )

    with op.batch_alter_table('events', schema=None) as batch_op:
        batch_op.add_column(sa.Column('race_id', sa.String(length=36), nullable=True))
    op.execute(sa.text(f"UPDATE events SET race_id = '{DEFAULT_RACE_ID}'"))
    with op.batch_alter_table('events', schema=None) as batch_op:
        batch_op.alter_column('race_id', existing_type=sa.String(length=36), nullable=False)
        batch_op.create_index('ix_events_race_id', ['race_id'], unique=False)
        batch_op.create_foreign_key('fk_events_race_id', 'races', ['race_id'], ['id'])

    with op.batch_alter_table('observations', schema=None) as batch_op:
        batch_op.add_column(sa.Column('race_id', sa.String(length=36), nullable=True))
    op.execute(sa.text(f"UPDATE observations SET race_id = '{DEFAULT_RACE_ID}'"))
    with op.batch_alter_table('observations', schema=None) as batch_op:
        batch_op.alter_column('race_id', existing_type=sa.String(length=36), nullable=False)
        batch_op.create_index('ix_observations_race_id', ['race_id'], unique=False)
        batch_op.create_foreign_key('fk_observations_race_id', 'races', ['race_id'], ['id'])

    with op.batch_alter_table('status_reports', schema=None) as batch_op:
        batch_op.add_column(sa.Column('race_id', sa.String(length=36), nullable=True))
    op.execute(sa.text(f"UPDATE status_reports SET race_id = '{DEFAULT_RACE_ID}'"))
    with op.batch_alter_table('status_reports', schema=None) as batch_op:
        batch_op.alter_column('race_id', existing_type=sa.String(length=36), nullable=False)
        batch_op.create_index('ix_status_reports_race_id', ['race_id'], unique=False)
        batch_op.create_foreign_key('fk_status_reports_race_id', 'races', ['race_id'], ['id'])

    with op.batch_alter_table('chat_rooms', schema=None) as batch_op:
        batch_op.add_column(sa.Column('race_id', sa.String(length=36), nullable=True))
    op.execute(sa.text(f"UPDATE chat_rooms SET race_id = '{DEFAULT_RACE_ID}'"))
    with op.batch_alter_table('chat_rooms', schema=None) as batch_op:
        batch_op.alter_column('race_id', existing_type=sa.String(length=36), nullable=False)
        batch_op.create_index('ix_chat_rooms_race_id', ['race_id'], unique=False)
        batch_op.create_foreign_key('fk_chat_rooms_race_id', 'races', ['race_id'], ['id'])

    with op.batch_alter_table('staffer_aro_volunteers', schema=None) as batch_op:
        batch_op.add_column(sa.Column('race_id', sa.String(length=36), nullable=True))
        batch_op.drop_constraint('uq_staffer_aro_volunteers_callsign', type_='unique')
    op.execute(sa.text(f"UPDATE staffer_aro_volunteers SET race_id = '{DEFAULT_RACE_ID}'"))
    with op.batch_alter_table('staffer_aro_volunteers', schema=None) as batch_op:
        batch_op.alter_column('race_id', existing_type=sa.String(length=36), nullable=False)
        batch_op.create_index('ix_staffer_aro_volunteers_race_id', ['race_id'], unique=False)
        batch_op.create_foreign_key('fk_staffer_aro_volunteers_race_id', 'races', ['race_id'], ['id'])
        batch_op.create_unique_constraint(
            'uq_staffer_aro_volunteers_race_callsign',
            ['race_id', 'callsign'],
        )


def downgrade():
    with op.batch_alter_table('staffer_aro_volunteers', schema=None) as batch_op:
        batch_op.drop_constraint('uq_staffer_aro_volunteers_race_callsign', type_='unique')
        batch_op.drop_constraint('fk_staffer_aro_volunteers_race_id', type_='foreignkey')
        batch_op.drop_index('ix_staffer_aro_volunteers_race_id')
        batch_op.drop_column('race_id')
        batch_op.create_unique_constraint('uq_staffer_aro_volunteers_callsign', ['callsign'])

    with op.batch_alter_table('chat_rooms', schema=None) as batch_op:
        batch_op.drop_constraint('fk_chat_rooms_race_id', type_='foreignkey')
        batch_op.drop_index('ix_chat_rooms_race_id')
        batch_op.drop_column('race_id')

    with op.batch_alter_table('status_reports', schema=None) as batch_op:
        batch_op.drop_constraint('fk_status_reports_race_id', type_='foreignkey')
        batch_op.drop_index('ix_status_reports_race_id')
        batch_op.drop_column('race_id')

    with op.batch_alter_table('observations', schema=None) as batch_op:
        batch_op.drop_constraint('fk_observations_race_id', type_='foreignkey')
        batch_op.drop_index('ix_observations_race_id')
        batch_op.drop_column('race_id')

    with op.batch_alter_table('events', schema=None) as batch_op:
        batch_op.drop_constraint('fk_events_race_id', type_='foreignkey')
        batch_op.drop_index('ix_events_race_id')
        batch_op.drop_column('race_id')

    op.drop_table('races')
