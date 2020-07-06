from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField
from wtforms.validators import DataRequired

from db import db

table = db.Table(
    "sign_ins",
    db.Column("first_name", db.String(length=255)),
    db.Column("last_name", db.String(length=255)),
    db.Column("street_and_house_number", db.Text),
    db.Column("plz_and_city", db.Text),
    db.Column("phone_number", db.String(length=255)),
    db.Column("signed_in_at", db.DateTime),
)


class Form(FlaskForm):
    first_name = StringField(
        "Vorname", validators=[DataRequired(message="Bitte trag deinen Vornamen ein")],
    )
    last_name = StringField(
        "Nachname",
        validators=[DataRequired(message="Bitte trag deinen Nachnamen ein")],
    )
    street_and_house_number = StringField(
        "Straße und Hausnummer",
        validators=[DataRequired(message="Bitte trag deine Straße und Hausnummer ein")],
    )
    plz_and_city = StringField(
        "PLZ und Ort",
        validators=[
            DataRequired(message="Bitte trag deine Postleitzahl und deinen Ort ein")
        ],
    )
    phone_number = StringField(
        "Telefonnummer",
        validators=[DataRequired(message="Bitte trag deine Telefonnummer ein")],
    )
