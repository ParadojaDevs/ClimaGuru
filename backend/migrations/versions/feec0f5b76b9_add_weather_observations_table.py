"""add weather_observations table

Revision ID: feec0f5b76b9
Revises: 281e30e1c663
Create Date: 2026-10-19 04:21:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'feec0f5b76b9'
down_revision = '281e30e1c663'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('weather_observations',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('fuente', sa.Enum('ideam_radar', 'sab_lluvias', name='fuente_observacion_enum'), nullable=False),
    sa.Column('estacion', sa.String(length=100), nullable=True),
    sa.Column('ciudad', sa.String(length=100), nullable=True),
    sa.Column('latitud', sa.Numeric(precision=10, scale=8), nullable=True),
    sa.Column('longitud', sa.Numeric(precision=11, scale=8), nullable=True),
    sa.Column('timestamp_observacion', sa.DateTime(), nullable=False),
    sa.Column('tipo_dato', sa.String(length=50), nullable=False),
    sa.Column('valor', sa.Numeric(precision=12, scale=4), nullable=True),
    sa.Column('unidad', sa.String(length=20), nullable=True),
    sa.Column('calidad', sa.String(length=20), nullable=True),
    sa.Column('metadatos', sa.JSON(), nullable=True),
    sa.Column('datos_crudos', sa.JSON(), nullable=True),
    sa.Column('procesado_en', sa.DateTime(), nullable=True),
    sa.Column('actualizado_en', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('weather_observations', schema=None) as batch_op:
        batch_op.create_index('idx_fuente', ['fuente'], unique=False)
        batch_op.create_index('idx_ciudad', ['ciudad'], unique=False)
        batch_op.create_index('idx_coordenadas', ['latitud', 'longitud'], unique=False)
        batch_op.create_index('idx_timestamp', ['timestamp_observacion'], unique=False)
        batch_op.create_index('idx_tipo_dato', ['tipo_dato'], unique=False)
        batch_op.create_index('idx_fuente_timestamp', ['fuente', 'timestamp_observacion'], unique=False)


def downgrade():
    with op.batch_alter_table('weather_observations', schema=None) as batch_op:
        batch_op.drop_index('idx_fuente_timestamp')
        batch_op.drop_index('idx_tipo_dato')
        batch_op.drop_index('idx_timestamp')
        batch_op.drop_index('idx_coordenadas')
        batch_op.drop_index('idx_ciudad')
        batch_op.drop_index('idx_fuente')

    op.drop_table('weather_observations')
    op.execute('DROP TYPE IF EXISTS fuente_observacion_enum')
