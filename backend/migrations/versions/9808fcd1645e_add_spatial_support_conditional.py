"""add spatial support conditional

Revision ID: 9808fcd1645e
Revises: feec0f5b76b9
Create Date: 2026-10-19 05:03:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = '9808fcd1645e'
down_revision = 'feec0f5b76b9'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    # For MySQL, add geometry column if supported; others keep lat/lon only
    if bind.dialect.name == 'mysql':
        try:
            op.execute("ALTER TABLE weather_observations ADD COLUMN geom POINT SRID 4326 NULL")
            op.execute("CREATE SPATIAL INDEX idx_weather_obs_geom ON weather_observations (geom)")
        except Exception:
            pass


def downgrade():
    bind = op.get_bind()
    if bind.dialect.name == 'mysql':
        try:
            op.execute("DROP INDEX idx_weather_obs_geom ON weather_observations")
            op.execute("ALTER TABLE weather_observations DROP COLUMN geom")
        except Exception:
            pass
