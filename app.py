import datetime
import sys

from flask import Flask, redirect, render_template
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField
from wtforms.validators import DataRequired


def create_app():
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
    app.config["SQLALCHEMY_DATABASE_URI"] = config.sqlalchemy_database_uri
    app.config[
        "SQLALCHEMY_TRACK_MODIFICATIONS"
    ] = False  # This is to do away with a deprecation warning that doesn't affect us
    db = SQLAlchemy(app)

    Migrate(app, db)

    sign_ins = db.Table(
        "sign_ins",
        db.Column("first_name", db.String(length=255)),
        db.Column("last_name", db.String(length=255)),
        db.Column("contact_data", db.Text),
        db.Column("date", db.Date),
    )
    insert_sign_in = sign_ins.insert()

    class SignInForm(FlaskForm):
        first_name = StringField(
            "Vorname",
            validators=[DataRequired(message="Bitte trag deinen Vornamen ein")],
        )
        last_name = StringField(
            "Nachname",
            validators=[DataRequired(message="Bitte trag deinen Nachnamen ein")],
        )
        contact_data = TextAreaField(
            "Kontaktdaten (entweder volle Adresse, Telefonnummer oder E-Mail)",
            validators=[DataRequired(message="Bitte trag eine Kontaktmöglichkeit ein")],
        )

    @app.route("/", methods=("GET", "POST"))
    def index():
        form = SignInForm()
        if form.validate_on_submit():
            db.session.execute(
                insert_sign_in.values(
                    first_name=form.first_name.data,
                    last_name=form.last_name.data,
                    contact_data=form.contact_data.data,
                    date=datetime.date.today(),
                )
            )
            db.session.commit()
            return redirect("/thank-you")
        return render_template("index.html.jinja2", form=form)

    @app.route("/thank-you")
    def thank_you():
        return "thank you!"

    return app
