import sys

from flask import Flask, redirect, render_template
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField
from wtforms.validators import DataRequired

try:
    import config
except ImportError:
    print(
        "config.py not found. You might need to create one based on config.py.example",
        file=sys.stderr,
    )
    sys.exit(1)

app = Flask(__name__)

app.secret_key = config.secret_key


class SignInForm(FlaskForm):
    first_name = StringField(
        "Vorname", validators=[DataRequired(message="Bitte trag deinen Vornamen ein")]
    )
    last_name = StringField(
        "Nachname", validators=[DataRequired(message="Bitte trag deinen Nachnamen ein")]
    )
    contact_data = TextAreaField(
        "Kontaktdaten (entweder volle Adresse, Telefonnummer oder E-Mail)",
        validators=[DataRequired(message="Bitte trag eine Kontaktmöglichkeit ein")],
    )


@app.route("/", methods=("GET", "POST"))
def index():
    form = SignInForm()
    if form.validate_on_submit():
        return "Yay, ty!"
    return render_template("index.html.jinja2", form=form)
