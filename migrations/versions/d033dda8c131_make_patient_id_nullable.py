"""Make patient_id nullable in Payment model

Revision ID: d033dda8c131
Revises: d033dda8c130
Create Date: 2025-04-24

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'd033dda8c131'
down_revision = 'd033dda8c130'
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column('payment', 'patient_id',
               existing_type=sa.Integer(),
               nullable=True)


def downgrade():
    op.alter_column('payment', 'patient_id',
               existing_type=sa.Integer(),
               nullable=False)
