"""switch email to username

Revision ID: 8c2f31a1724b
Revises: 4b32f2f6ffac
Create Date: 2026-04-30 22:57:13.588582

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8c2f31a1724b'
down_revision = '4b32f2f6ffac'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('user', sa.Column('username', sa.String(length=80), nullable=True))
    op.execute('UPDATE user SET username = email')
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.drop_constraint(batch_op.f('uq_user_email'), type_='unique')
        batch_op.create_unique_constraint('uq_user_username', ['username'])
        batch_op.alter_column('username', existing_type=sa.String(length=80), nullable=False)
        batch_op.drop_column('email')


def downgrade():
    op.add_column('user', sa.Column('email', sa.String(length=255), nullable=True))
    op.execute('UPDATE user SET email = username')
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.drop_constraint('uq_user_username', type_='unique')
        batch_op.create_unique_constraint(batch_op.f('uq_user_email'), ['email'])
        batch_op.alter_column('email', existing_type=sa.String(length=255), nullable=False)
        batch_op.drop_column('username')
