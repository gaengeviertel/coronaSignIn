from flask_wtf import FlaskForm
from base64 import b64encode, b64decode
from wtforms import StringField, SelectField
from wtforms.validators import DataRequired

from db import db

table = db.Table(
    "sign_ins",
    db.Column("location", db.String(length=255)),
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


class FormWithLocation(Form):
    def __init__(self, locations):
        super().__init__()
        self.location.choices = [("", "Bitte Auswählen")] + [
            (b64encode(location.encode("utf-8")).decode("utf-8"), location)
            for location in locations
        ]

    @property
    def data(self):
        data = super().data
        data["location"] = b64decode(data["location"]).decode("utf-8")
        return data

    def set_location(self, location: str):
        try:
            location_value = next(
                value for (value, label) in self.location.choices if label == location
            )
        except StopIteration:
            raise ValueError(f'Location "{location}" not found')
        self.location.data = location_value

    location = SelectField(
        "Ort",
        validators=[DataRequired(message="Bitte wähle aus von wo du eincheckst")],
    )
