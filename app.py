import datetime
import sys

from flask import Flask, redirect, render_template

from coronasignin import sign_ins
from coronasignin.config import Config
from coronasignin.db import db
from coronasignin.migrate import migrate


def create_app():
    app = Flask(__name__)

    app.config.from_object(Config())

    db.init_app(app)
    migrate.init_app(app, db)

    @app.route("/", methods=("GET", "POST"))
    def index():
        form = sign_ins.Form()
        if form.validate_on_submit():
            db.session.execute(
                sign_ins.table.insert().values(
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
