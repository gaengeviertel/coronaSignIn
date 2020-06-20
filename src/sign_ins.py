from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField
from wtforms.validators import DataRequired

from db import db

table = db.Table(
    "sign_ins",
    db.Column("first_name", db.String(length=255)),
    db.Column("last_name", db.String(length=255)),
    db.Column("contact_data", db.Text),
    db.Column("date", db.Date),
)


class Form(FlaskForm):
    first_name = StringField(
        "Vorname", validators=[DataRequired(message="Bitte trag deinen Vornamen ein")],
    )
    last_name = StringField(
        "Nachname",
        validators=[DataRequired(message="Bitte trag deinen Nachnamen ein")],
    )
    contact_data = TextAreaField(
        "Kontaktdaten (entweder volle Adresse, Telefonnummer oder E-Mail)",
        validators=[DataRequired(message="Bitte trag eine Kontaktmöglichkeit ein")],
    )
