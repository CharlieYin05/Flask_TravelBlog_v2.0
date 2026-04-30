"""add email to user

Revision ID: 7e317862da95
Revises: 8c2f31a1724b
Create Date: 2026-04-30 23:01:31.187361

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7e317862da95'
down_revision = '8c2f31a1724b'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('user', sa.Column('email', sa.String(length=255), nullable=True))
    op.execute('UPDATE user SET email = username')
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.create_unique_constraint('uq_user_email', ['email'])
        batch_op.alter_column('email', existing_type=sa.String(length=255), nullable=False)


def downgrade():
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.drop_constraint('uq_user_email', type_='unique')
        batch_op.drop_column('email')
