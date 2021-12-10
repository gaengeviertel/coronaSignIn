import sys
from datetime import datetime

from flask import Flask, redirect, render_template, request

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
        locations = app.config["LOCATIONS"]
        if locations:
            form = sign_ins.FormWithLocation(locations)
            preselected_location = request.args.get("location")
            if preselected_location:
                try:
                    form.set_location(preselected_location)
                except ValueError:
                    return f'Location "{preselected_location}" does not exist', 400
        else:
            form = sign_ins.Form()
        if form.validate_on_submit():
            db.session.execute(
                sign_ins.table.insert().values(**form.data, signed_in_at=datetime.now())
            )
            db.session.commit()
            return redirect("/thank-you")
        return render_template("index.html.jinja2", form=form)

    @app.route("/data-protection")
    def data_protection():
        return render_template("data-protection.html.jinja2")

    @app.route("/thank-you")
    def thank_you():
        return render_template("success-page.html.jinja2")

    @app.errorhandler(500)
    @app.errorhandler(404)
    def internal_server_error(e):
        return render_template("error-page.html.jinja2", error=e.name, description=e.description), e.code

    return app
