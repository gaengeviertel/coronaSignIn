from flask import url_for
from pytest import fail, mark
from selenium.common.exceptions import NoSuchElementException


def test_headline_exists(client):
    page = client.get("/")
    assert b"Moin lieber Gast!" in page.data


@mark.usefixtures("live_server")
@mark.slow
def test_live_index(selenium):
    selenium.get(url_for("index", _external=True))
    try:
        selenium.find_element_by_xpath('//*[text()="Moin lieber Gast!"]')
    except NoSuchElementException:
        fail("Could not find headline on index page")
