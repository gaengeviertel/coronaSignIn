"""empty message

Revision ID: 955e39ea4c83
Revises: 742e70cfd5ee
Create Date: 2020-08-13 18:11:52.539259

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "955e39ea4c83"
down_revision = "742e70cfd5ee"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "sign_ins", sa.Column("location", sa.String(length=255), nullable=True)
    )


def downgrade():
    op.drop_column("sign_ins", "location")
