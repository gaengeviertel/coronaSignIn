"""empty message

Revision ID: 742e70cfd5ee
Revises: 397b61eff2c6
Create Date: 2020-07-06 10:45:27.814417

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.sql import table

# revision identifiers, used by Alembic.
revision = "742e70cfd5ee"
down_revision = "397b61eff2c6"
branch_labels = None
depends_on = None


def upgrade():
    # 1. Add the new columns
    op.add_column(
        "sign_ins", sa.Column("phone_number", sa.String(length=255), nullable=True)
    )
    op.add_column("sign_ins", sa.Column("plz_and_city", sa.Text(), nullable=True))
    op.add_column("sign_ins", sa.Column("signed_in_at", sa.DateTime(), nullable=True))
    op.add_column(
        "sign_ins", sa.Column("street_and_house_number", sa.Text(), nullable=True)
    )

    # 2. Update the data
    sign_ins = table(
        "sign_ins",
        sa.Column("street_and_house_number", sa.Text),
        sa.Column("contact_data", sa.Text),
        sa.Column("signed_in_at", sa.DateTime),
        sa.Column("date", sa.Date),
    )

    op.execute(
        sign_ins.update().values(
            {
                sign_ins.c.street_and_house_number: sign_ins.c.contact_data,
                sign_ins.c.signed_in_at: sign_ins.c.date,
            }
        )
    )

    # 3. Remove the old columns
    with op.batch_alter_table("sign_ins") as batch_op:
        batch_op.drop_column("contact_data")
        batch_op.drop_column("date")


def downgrade():
    op.add_column("sign_ins", sa.Column("date", sa.DATE(), nullable=True))
    op.add_column("sign_ins", sa.Column("contact_data", sa.TEXT(), nullable=True))

    sign_ins = table(
        "sign_ins",
        sa.Column("street_and_house_number", sa.Text),
        sa.Column("plz_and_city", sa.Text),
        sa.Column("phone_number", sa.String(length=255)),
        sa.Column("contact_data", sa.Text),
        sa.Column("signed_in_at", sa.DateTime),
        sa.Column("date", sa.Date),
    )

    op.execute(
        sign_ins.update().values(
            {
                sign_ins.c.date: sign_ins.c.signed_in_at,
                # Hauptstraße 1 12345 City 555-12345, it's fine for a downgrade
                sign_ins.c.contact_data: (
                    sign_ins.c.street_and_house_number.concat("")
                    .concat(sign_ins.c.plz_and_city)
                    .concat(" ")
                    .concat(sign_ins.c.phone_number)
                ),
            }
        )
    )

    with op.batch_alter_table("sign_ins") as batch_op:
        batch_op.drop_column("street_and_house_number")
        batch_op.drop_column("signed_in_at")
        batch_op.drop_column("plz_and_city")
        batch_op.drop_column("phone_number")
