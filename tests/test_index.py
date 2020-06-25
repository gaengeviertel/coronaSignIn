from datetime import date

from flask import url_for
from pytest import fail, mark
from selenium.common.exceptions import NoSuchElementException
from sqlalchemy import select

import sign_ins
from db import db


def test_headline_exists(client):
    page = client.get("/")
    assert b"Moin lieber Gast!" in page.data


def test_db(app, db_session):
    db.session.execute(
        sign_ins.table.insert().values(
            first_name="f", last_name="l", contact_data="c", date=date.today()
        )
    )
    db.session.commit()

    results = db.session.execute(select([sign_ins.table])).fetchall()

    assert len(results) == 1
    assert results[0].items() == [
        ("first_name", "f"),
        ("last_name", "l"),
        ("contact_data", "c"),
        ("date", date(2020, 6, 25)),
    ]


@mark.usefixtures("live_server")
@mark.slow
def test_live_index(selenium):
    selenium.get(url_for("index", _external=True))
    try:
        selenium.find_element_by_xpath('//*[text()="Moin lieber Gast!"]')
    except NoSuchElementException:
        fail("Could not find headline on index page")


@mark.usefixtures("live_server")
@mark.slow
def test_form_data_is_saved_to_database(selenium, db_session):
    selenium.get(url_for("index", _external=True))

    selenium.find_element_by_name("first_name").send_keys("Octave")
    selenium.find_element_by_name("last_name").send_keys("Garnier")
    selenium.find_element_by_name("contact_data").send_keys("555-12345")

    selenium.find_element_by_xpath('//input[@type="submit"]').click()

    selenium.find_element_by_xpath('//*[text()="thank you!"]')

    assert list(
        map(
            lambda row: row.items(),
            db.session.execute(select([sign_ins.table])).fetchall(),
        )
    ) == [
        [
            ("first_name", "Octave"),
            ("last_name", "Garnier"),
            ("contact_data", "555-12345"),
            ("date", date(2020, 6, 25)),
        ]
    ]


@mark.usefixtures("live_server")
@mark.slow
def test_form_is_filled_from_localstorage(selenium):
    # Set up localStorage
    selenium.get(url_for("index", _external=True))
    selenium.execute_script("window.localStorage.clear()")

    selenium.get(url_for("index", _external=True))
    element = selenium.find_element_by_name("first_name")
    assert (
        element.get_attribute("value") == ""
    ), "The browser is weird, why is this filled?"

    selenium.execute_script("window.localStorage.clear()")
    selenium.execute_script(
        """
        window.localStorage.setItem('saved-form', JSON.stringify({
            first_name: "Jules",
            last_name: "Joseph",
            contact_data: "Go to the sea and shout"
        }));
    """
    )

    # Reload the page
    selenium.get(url_for("index", _external=True))

    # Assertions
    assert selenium.find_element_by_name("first_name").get_attribute("value") == "Jules"
    assert selenium.find_element_by_name("last_name").get_attribute("value") == "Joseph"
    assert (
        selenium.find_element_by_name("contact_data").get_attribute("value")
        == "Go to the sea and shout"
    )
