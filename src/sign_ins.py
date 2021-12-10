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
            (id, location.name) for id, location in locations.items()
        ]

    @property
    def data(self):
        data = super().data
        try:
            data["location"] = next(
                label for (value, label) in self.location.choices if value == self.location.data
            )
        except StopIteration:
            raise ValueError(f'Location id "{self.location.data}" not resolved')
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
