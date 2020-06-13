"""Initial

Revision ID: 397b61eff2c6
Revises: 
Create Date: 2020-06-13 15:33:48.670291

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "397b61eff2c6"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "sign_ins",
        sa.Column("first_name", sa.VARCHAR(length=255), nullable=True),
        sa.Column("last_name", sa.VARCHAR(length=255), nullable=True),
        sa.Column("contact_data", sa.TEXT(), nullable=True),
        sa.Column("date", sa.DATE(), nullable=True),
    )


def downgrade():
    op.drop_table("sign_ins")
