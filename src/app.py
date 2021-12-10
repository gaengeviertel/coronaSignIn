import os
from datetime import datetime

from flask import Flask, redirect, render_template, request, Response, url_for

from typing import Optional, Union

import sign_ins
from config import ProductionConfig
from db import db
from migrate import migrate
from slugify import slugify
from hashlib import md5
import cwa_qr
from cwa_qr import CwaLocation
from io import BytesIO
import qrcode.image.svg

class Location:
    name: str
    address: Optional[str]
    type: CwaLocation
    default_check_in_length: int
    cwa_seed: Optional[str]

    cwa_seed_prefix: str='corona-sign-in'

    # Map names to CWA types
    types = {
        'generic': CwaLocation.permanent_other,
        'retail': CwaLocation.permanent_retail,
        'food': CwaLocation.permanent_food_service,
        'craft': CwaLocation.permanent_craft,
        'workplace': CwaLocation.permanent_workplace,
        'educational': CwaLocation.permanent_educational_institution,
        'public building': CwaLocation.permanent_public_building,
    }

    def __init__(self, name: str, address: Optional[str]=None,
                 type: Union[str,CwaLocation]=CwaLocation.permanent_other,
                 default_check_in_length: int=60, cwa_seed: Optional[str]=None,
                 secret: Optional[str]=None):
        if len(name) < 3:
            raise ValueError('{name}: Invalid location name')
        self.name = name

        if address is not None and len(address) < 5:
            raise ValueError(f'{name}: Invalid location address: {address}')
        self.address = address

        if isinstance(type, CwaLocation):
            self.type = type
        else:
            if type not in self.types:
                raise ValueError(f'{name}: Invalid location type: {type}')
            self.type = self.types[type]

        self.default_check_in_length = default_check_in_length
        if cwa_seed is None and secret is not None:
            digest = md5(f'{secret}-{name}'.encode()).hexdigest()
            cwa_seed = f'{self.cwa_seed_prefix}-{digest}'
        self.cwa_seed = cwa_seed

    @classmethod
    def create_with_id(cls, *args, **kwargs):
        l = cls(*args, **kwargs)
        return (l.id, l)

    @property
    def id(self):
        return slugify(self.name)

    def __str__(self):
        return f'{self.name}, {self.address}'

    def cwa_event(self):
        event = cwa_qr.CwaEventDescription()
        event.location_description = self.name
        event.location_address = self.address
        event.location_type = self.type
        event.default_check_in_length_in_minutes = self.default_check_in_length
        event.seed = self.cwa_seed
        return event

    def cwa_url(self):
        try:
            ev = self.cwa_event()
            return cwa_qr.generate_url(ev)
        except TypeError:
            return None

    def cwa_qr_code(self):
        try:
            ev = self.cwa_event()
            qr = cwa_qr.generate_qr_code(ev)
        except TypeError:
            return None
        svg = qr.make_image(image_factory=qrcode.image.svg.SvgPathFillImage)
        buf = BytesIO()
        svg.save(buf)
        return buf.getvalue()


def create_app(config=None):
    app = Flask(__name__)

    app.config.from_object(config if config else ProductionConfig())
    if os.environ.get("CORONA_SIGN_IN_CONFIG"):
        app.config.from_envvar("CORONA_SIGN_IN_CONFIG")

    db.init_app(app)
    migrate.init_app(app, db)

    # Create the location list from either a simple list of names, or
    # a dict of options for each location
    locations_cfg = app.config["LOCATIONS"]
    secret = app.config.get('SECRET_KEY')
    if isinstance(locations_cfg, (tuple, list)):
        locations = dict((Location.create_with_id(name, secret=secret)
                          for name in locations_cfg))
    else:
        locations = dict((Location.create_with_id(name, secret=secret, **opts)
                          for name, opts in locations_cfg.items()))

    @app.route("/", methods=("GET", "POST"))
    def index():
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
            return redirect(url_for('.thank_you', location_id=form.location.data))
        return render_template("index.html.jinja2", form=form)

    @app.route("/data-protection")
    def data_protection():
        return render_template("data-protection.html.jinja2")

    @app.route("/thank-you/<location_id>")
    def thank_you(location_id):
        location = locations.get(location_id)
        if not location:
            return render_template("error-page.html.jinja2", error="Invalid location"), 400

        return render_template("success-page.html.jinja2", cwa_url=location.cwa_url())

    @app.route("/cwa/<location_id>/qr-code.svg")
    def cwa_qr_code(location_id):
        location = locations.get(location_id)
        if not location:
            return render_template("error-page.html.jinja2", error="Location not found"), 404

        return Response(location.cwa_qr_code(), mimetype="image/svg+xml")

    @app.route("/cwa/<location_id>")
    def cwa(location_id):
        location = locations.get(location_id)
        if not location:
            return render_template("error-page.html.jinja2", error="Location not found"), 404

        return render_template("cwa-page.html.jinja2", location=location.name,
                               qr_code=url_for('.cwa_qr_code', location_id=location.id))

    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template("error-page.html.jinja2"), 500

    app.register_error_handler(500, internal_server_error)
    return app
