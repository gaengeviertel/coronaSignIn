import http.client
import socket
import subprocess
import time
from collections import namedtuple
from datetime import date, datetime, timedelta

from pytest import fixture, mark
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

# These variables have to be in sync with the test_container/pod.yml
app_image_name = "corona-sign-in-automatic-test"
pod_name = "corona-sign-in-automatic-test"


@fixture(scope="session")
def container_names():
    ContainerNames = namedtuple("ContainerNames", "app db")
    return ContainerNames(app="corona-sign-in-app", db="corona-sign-in-db")


@fixture(scope="session")
def running_pod(container_names):
    """
    This is shared state between tests.

    Also, currently there is no way to wipe the database between tests.
    This is not ideal, but recreating the pod takes a long time.
    """
    run_pod = "docker-compose up -d".split()
    upgrade_db = f"docker-compose exec {container_names.app} flask db upgrade".split()
    stop_pod = "docker-compose down".split()

    try:
        subprocess.run(run_pod, check=True)

        wait_for_db_or_raise(container_names.db)

        subprocess.run(upgrade_db, check=True)

        wait_for_app_or_raise(container_names.app)

        yield
    finally:
        subprocess.run(stop_pod, check=True)


def wait_for_db_or_raise(container_name):
    attempts = 240
    delay_seconds = 2

    db_test_command = [
        *f"docker-compose exec {container_name} psql -h localhost -U corona-sign-in".split(),
        "--command",
        "SELECT 1;",
    ]

    for _ in range(attempts):
        time.sleep(delay_seconds)
        result = subprocess.run(
            db_test_command, stderr=subprocess.STDOUT, stdout=subprocess.PIPE
        )
        if result.returncode == 0:
            return

    print("Output from wait_for_db:")
    print(result.stdout)

    raise Exception(
        f"Waited {attempts * delay_seconds}s for the db "
        "container to respond, giving up."
    )


def wait_for_app_or_raise(container_name):
    attempts = 360
    delay_seconds = 0.5

    for _ in range(attempts):
        time.sleep(delay_seconds)
        try:
            try:
                conn = http.client.HTTPConnection("localhost", 8080)
                conn.request("HEAD", "/")
                return
            except ConnectionError:
                # It's fine, this is why we're doing this check.
                pass
        finally:
            conn.close()

    print("Output from app container")
    subprocess.run(["podman", "logs", container_name])

    raise Exception(
        f"Waited {attempts} x {delay_seconds}s for the app "
        "container to respond, giving up."
    )


@fixture(scope="session")
def selenium():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    driver = webdriver.Chrome(options=chrome_options)
    yield driver
    driver.quit()


@mark.usefixtures("running_pod")
def test_submitted_form_is_in_database(selenium, container_names):
    run_in_db_container = f"docker-compose exec {container_names.db}".split()
    run_db_query = (
        "psql -h localhost -U corona-sign-in corona-sign-in "
        "--quiet --no-align --pset=tuples_only --command ".split()
    )
    delete_existing_entries_sql = "DELETE FROM sign_ins;"
    commandline = [*run_in_db_container, *run_db_query, delete_existing_entries_sql]
    subprocess.run(commandline, stdout=subprocess.PIPE)

    selenium.get("http://localhost:8080/")

    def fill_field(name, value):
        selenium.find_element_by_name(name).send_keys(value)

    fill_field("first_name", "Octave")
    fill_field("last_name", "Garnier")
    fill_field("street_and_house_number", "foo 9")
    fill_field("plz_and_city", "1234 city")
    fill_field("phone_number", "33 4455")

    selenium.find_element_by_xpath('//input[@type="submit"]').click()

    # ensure the result page has loaded
    selenium.find_element_by_xpath('//*[text()="Danke"]')

    #### Verify ####

    # Get the data from the db

    run_in_db_container = f"docker-compose exec {container_names.db}".split()
    run_db_query = (
        "psql -h localhost -U corona-sign-in corona-sign-in "
        "--quiet --no-align --pset=tuples_only --command ".split()
    )
    get_sign_ins_from_db_sql = (
        "SELECT "
        "   first_name, last_name, street_and_house_number, "
        "   plz_and_city, phone_number, signed_in_at "
        "FROM sign_ins;"
    )
    commandline = [*run_in_db_container, *run_db_query, get_sign_ins_from_db_sql]

    completedProcess = subprocess.run(commandline, stdout=subprocess.PIPE)
    output = completedProcess.stdout.decode("utf-8").strip()

    # We only compare the start of the date to avoid having to deal with seconds
    assert output.startswith(
        f"Octave|Garnier|foo 9|1234 city|33 4455|{date.today().isoformat()}"
    )
