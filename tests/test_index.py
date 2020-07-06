import json
from datetime import datetime, timedelta

import requests
from bs4 import BeautifulSoup
from flask import url_for
from pytest import fail, mark
from selenium.common.exceptions import NoSuchElementException
from sqlalchemy import select

import sign_ins
from db import db
from factories import makeSignInData


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
    assert errors[0].text.strip() == "Bitte trag deinen Nachnamen ein"


def test_error_page(broken_app, client):
    broken_app.config["PROPAGATE_EXCEPTIONS"] = False
    page = client.get("/")
    assert b"Uups..." in page.data


def test_db(app, db_session):
    # This test is not used yet, but it shows that the db_session works. Let's keep it
    # around until we use the db in another test
    db.session.execute(
        sign_ins.table.insert().values(
            first_name="f",
            last_name="l",
            street_and_house_number="example lane 42",
            plz_and_city="12345 anyville",
            phone_number="555-12345",
            signed_in_at=datetime(2020, 3, 21, 13, 12, 7),
        )
    )
    db.session.commit()

    results = db.session.execute(select([sign_ins.table])).fetchall()

    assert len(results) == 1
    assert results[0].items() == [
        ("first_name", "f"),
        ("last_name", "l"),
        ("street_and_house_number", "example lane 42"),
        ("plz_and_city", "12345 anyville"),
        ("phone_number", "555-12345"),
        ("signed_in_at", datetime(2020, 3, 21, 13, 12, 7)),
    ]


@mark.usefixtures("live_server")
def test_no_cookies():
    response = requests.get(url_for("index", _external=True))
    assert "set-cookie" not in response.headers

    response = requests.post(url_for("index", _external=True), data=makeSignInData())
    assert "Dein Eintrag wurde in unserer Datenbank gespeichert" in response.text
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

    fill_field(selenium, "first_name", "Octave")
    fill_field(selenium, "last_name", "Garnier")
    fill_field(selenium, "street_and_house_number", "hideout avenue 681")
    fill_field(selenium, "plz_and_city", "98765 somewhere")
    fill_field(selenium, "phone_number", "(555) 1234")

    selenium.find_element_by_xpath('//input[@type="submit"]').click()

    # ensure the result page has loaded
    selenium.find_element_by_xpath('//*[text()="Danke"]')

    response = db.session.execute(select([sign_ins.table])).fetchall()

    assert len(response) == 1

    entry = response[0]
    assert entry.first_name == "Octave"
    assert entry.last_name == "Garnier"
    assert entry.street_and_house_number == "hideout avenue 681"
    assert entry.plz_and_city == "98765 somewhere"
    assert entry.phone_number == "(555) 1234"

    time_since_entry = datetime.now() - entry.signed_in_at
    assert time_since_entry.total_seconds() > 0, "signed_in is in the future"
    assert time_since_entry < timedelta(seconds=10), "signed_in seems too long ago"


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
            street_and_house_number: "foo street 42",
            plz_and_city: "777 beep boop computer town",
            phone_number: "00 00 00 00"
        }));
    """
    )

    # Reload the page
    selenium.get(url_for("index", _external=True))

    def get_value(name):
        return selenium.find_element_by_name(name).get_attribute("value")

    # Assertions
    assert get_value("first_name") == "Jules"
    assert get_value("last_name") == "Joseph"
    assert get_value("street_and_house_number") == "foo street 42"
    assert get_value("plz_and_city") == "777 beep boop computer town"
    assert get_value("phone_number") == "00 00 00 00"


@mark.usefixtures("live_server")
@mark.slow
def test_localstorage_is_cleared_if_saving_not_selected(selenium):
    selenium.get(url_for("index", _external=True))
    selenium.execute_script("window.localStorage.clear()")
    selenium.execute_script(
        f"""
        window.localStorage.setItem(
            'saved-form',
            '{json.dumps(makeSignInData())}'
        );
    """
    )
    selenium.get(url_for("index", _external=True))

    assert (
        selenium.execute_script(
            "return JSON.parse(window.localStorage.getItem('saved-form'))"
        )
        is not None
    )

    fill_form_with_fake_data(selenium)

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

    fill_form_with_fake_data(selenium)

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

    fill_field(selenium, "first_name", "Octave")
    fill_field(selenium, "last_name", "Garnier")
    fill_field(selenium, "street_and_house_number", "yup 2")
    fill_field(selenium, "plz_and_city", "7 yea")
    fill_field(selenium, "phone_number", "555-12345")
    selenium.find_element_by_id("save_for_next_time").click()

    selenium.find_element_by_xpath('//input[@type="submit"]').click()

    # ensure the result page has loaded
    selenium.find_element_by_xpath('//*[text()="Danke"]')

    assert selenium.execute_script(
        "return JSON.parse(window.localStorage.getItem('saved-form'))"
    ) == {
        "first_name": "Octave",
        "last_name": "Garnier",
        "street_and_house_number": "yup 2",
        "plz_and_city": "7 yea",
        "phone_number": "555-12345",
    }


@mark.usefixtures("live_server")
@mark.slow
def test_save_for_next_time_is_preselected_iff_data_was_stored(selenium):
    selenium.get(url_for("index", _external=True))
    selenium.execute_script("window.localStorage.clear()")

    selenium.get(url_for("index", _external=True))
    assert not selenium.find_element_by_id("save_for_next_time").is_selected()

    selenium.execute_script(
        f"""
        window.localStorage.setItem(
            'saved-form',
            '{json.dumps(makeSignInData())}'
        );
    """
    )
    selenium.get(url_for("index", _external=True))

    assert selenium.find_element_by_id("save_for_next_time").is_selected()


def fill_field(selenium, name, value):
    selenium.find_element_by_name(name).send_keys(value)


def fill_form_with_fake_data(selenium):
    for name, value in makeSignInData().items():
        fill_field(selenium, name, value)
