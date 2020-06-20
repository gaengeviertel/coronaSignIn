import datetime
import sys

from flask import Flask, redirect, render_template

import sign_ins
from config import ProductionConfig
from db import db
from migrate import migrate


def create_app(config=None):
    app = Flask(__name__)

    app.config.from_object(config if config else ProductionConfig())

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