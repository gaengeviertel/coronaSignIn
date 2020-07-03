from datetime import date

import requests
from bs4 import BeautifulSoup
from flask import url_for
from freezegun import freeze_time
from pytest import fail, mark
from selenium.common.exceptions import NoSuchElementException
from sqlalchemy import select

import sign_ins
from db import db


def test_headline_exists(client):
    page = client.get("/")
    assert b"Moin lieber Gast!" in page.data


def test_success_page_has_content(client):
    page = client.get("/thank-you")
    assert b"Danke" in page.data


def test_form_validation_errors_are_shown(client):
    page = client.post("/", data={"first_name": "foo"})
    html = BeautifulSoup(page.data, "html.parser")

    last_name_input = html.find("input", attrs={"name": "last_name"})
    assert "has_error" in last_name_input.attrs.get("class", [])

    errors = html.find_all("ul", attrs={"class": "errors"})
    assert len(errors) == 2  # last name and contact data
    assert errors[0].text.strip() == "Bitte trag deinen Nachnamen ein"


@mark.usefixtures("broken_app")
def test_error_page(client):
    page = client.get("/")
    assert b"Uups... Error 500" in page.data


@freeze_time("2020-03-21")
def test_db(app, db_session):
    # This test is not used yet, but it shows that the db_session works. Let's keep it
    # around until we use the db in another test
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
        ("date", date(2020, 3, 21)),
    ]


@mark.usefixtures("live_server")
def test_no_cookies():
    response = requests.get(url_for("index", _external=True))
    assert "set-cookie" not in response.headers

    response = requests.post(
        url_for("index", _external=True),
        data={"first_name": "zxcv", "last_name": "asdf", "contact_data": "qwer"},
    )
    assert "set-cookie" not in response.headers

    response = requests.get(url_for("thank_you", _external=True))
    assert "set-cookie" not in response.headers


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

    # ensure the result page has loaded
    selenium.find_element_by_xpath('//*[text()="Danke"]')

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
            # We cannot freeze live_server's time because it runs in a separate process
            ("date", date.today()),
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


@mark.usefixtures("live_server")
@mark.slow
def test_localstorage_is_cleared_if_saving_not_selected(selenium):
    selenium.get(url_for("index", _external=True))
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
    selenium.get(url_for("index", _external=True))

    assert (
        selenium.execute_script(
            "return JSON.parse(window.localStorage.getItem('saved-form'))"
        )
        is not None
    )

    selenium.find_element_by_name("first_name").send_keys("Octave")
    selenium.find_element_by_name("last_name").send_keys("Garnier")
    selenium.find_element_by_name("contact_data").send_keys("555-12345")

    save_for_next_time = selenium.find_element_by_id("save_for_next_time")
    assert (
        save_for_next_time.is_selected()
    ), "assumed save_for_next_time would be checked since we have data in localStorage"
    save_for_next_time.click()

    selenium.find_element_by_xpath('//input[@type="submit"]').click()

    # ensure the result page has loaded
    selenium.find_element_by_xpath('//*[text()="Danke"]')

    assert (
        selenium.execute_script(
            "return JSON.parse(window.localStorage.getItem('saved-form'))"
        )
        is None
    )


@mark.usefixtures("live_server")
@mark.slow
def test_localstorage_is_not_populated_on_form_submit_by_default(selenium):
    selenium.get(url_for("index", _external=True))
    selenium.execute_script("window.localStorage.clear()")

    selenium.get(url_for("index", _external=True))
    selenium.find_element_by_name("first_name").send_keys("Octave")
    selenium.find_element_by_name("last_name").send_keys("Garnier")
    selenium.find_element_by_name("contact_data").send_keys("555-12345")

    selenium.find_element_by_xpath('//input[@type="submit"]').click()

    # ensure the result page has loaded
    selenium.find_element_by_xpath('//*[text()="Danke"]')

    assert (
        selenium.execute_script(
            "return JSON.parse(window.localStorage.getItem('saved-form'))"
        )
        is None
    )


@mark.usefixtures("live_server")
@mark.slow
def test_localstorage_is_populated_on_form_submit_if_selected(selenium):
    selenium.get(url_for("index", _external=True))
    selenium.execute_script("window.localStorage.clear()")

    selenium.find_element_by_name("first_name").send_keys("Octave")
    selenium.find_element_by_name("last_name").send_keys("Garnier")
    selenium.find_element_by_name("contact_data").send_keys("555-12345")
    selenium.find_element_by_id("save_for_next_time").click()

    selenium.find_element_by_xpath('//input[@type="submit"]').click()

    # ensure the result page has loaded
    selenium.find_element_by_xpath('//*[text()="Danke"]')

    assert selenium.execute_script(
        "return JSON.parse(window.localStorage.getItem('saved-form'))"
    ) == {"first_name": "Octave", "last_name": "Garnier", "contact_data": "555-12345"}


@mark.usefixtures("live_server")
@mark.slow
def test_save_for_next_time_is_preselected_iff_data_was_stored(selenium):
    selenium.get(url_for("index", _external=True))
    selenium.execute_script("window.localStorage.clear()")

    selenium.get(url_for("index", _external=True))
    assert not selenium.find_element_by_id("save_for_next_time").is_selected()

    selenium.execute_script(
        """
        window.localStorage.setItem('saved-form', JSON.stringify({
            first_name: "Jules",
            last_name: "Joseph",
            contact_data: "Go to the sea and shout"
        }));
    """
    )
    selenium.get(url_for("index", _external=True))

    assert selenium.find_element_by_id("save_for_next_time").is_selected()
