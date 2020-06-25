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
