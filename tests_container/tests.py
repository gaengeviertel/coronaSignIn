import http.client
import socket
import subprocess
import time
from collections import namedtuple
from datetime import date

from pytest import fixture, mark
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

# These variables have to be in sync with the test_container/pod.yml
app_image_name = "corona-sign-in-automatic-test"
pod_name = "corona-sign-in-automatic-test"


@fixture(scope="session")
def container_names():
    # Podman pre-2 seems to generate different container names
    ContainerNames = namedtuple("ContainerNames", "app db")
    version = (
        subprocess.run(["podman", "--version"], check=True, stdout=subprocess.PIPE)
        .stdout.decode("utf-8")
        .strip()
    )
    print(f"podman --version gave: {version}")

    if version == "podman version 1.9.3":
        print("Using unprefixed container names")
        return ContainerNames(app="app", db="db")
    else:
        print("Using prefixed container names")
        return ContainerNames(app=f"{pod_name}-app", db=f"{pod_name}-db")


@fixture(scope="session")
def running_pod(container_names):
    """
    This is shared state between tests.

    Also, currently there is no way to wipe the database between tests.
    This is not idea, but recreating the pod takes a long time.

    Debugging failing tests based on this is not easy because the logs are deleted when
    we remove the pod.

    You can use `pytest --pdb`, insert a `breakpoint()` or remove the "podman pod rm"
    command to keep the pod up and then use `podman logs
    corona-sign-in-automatic-test-app` (container name is podname-containername) to get
    the logs or `podman exec -ti corona-sign-in-automatic-test-app bash` to get a shell
    in the container.

    Running pytest with -s (so that it directly prints stdout) allows you to see the
    podman output, which is helpful if that part fails.
    """

    try:
        subprocess.run(["podman", "build", "-t", app_image_name, "."], check=True)
        subprocess.run(
            ["podman", "pod", "rm", "--force", "--ignore", pod_name], check=True
        )
        subprocess.run(
            ["podman", "play", "kube", "tests_container/pod.yml"], check=True
        )
        subprocess.run("podman container ls".split())

        wait_for_db_or_raise(container_names.db)

        subprocess.run(
            ["podman", "exec", container_names.app, "flask", "db", "upgrade"],
            check=True,
        )

        wait_for_app_or_raise()

        yield
    finally:
        subprocess.run(["podman", "pod", "rm", "--force", pod_name], check=True)


def wait_for_db_or_raise(container_name):
    attempts = 40
    delay_seconds = 0.5

    for _ in range(attempts):
        time.sleep(delay_seconds)
        result = subprocess.run(
            [
                *f"podman exec {container_name}".split(),
                *"psql -h localhost -U corona-sign-in".split(),
                *["--command", "SELECT 1;"],
            ],
            stderr=subprocess.STDOUT,
            stdout=subprocess.PIPE,
        )
        if result.returncode == 0:
            return

    print("Output fromwait_for_db:")
    print(result.stdout)

    raise Exception(
        f"Waited {attempts * delay_seconds}s for the db "
        "container to respond, giving up."
    )


def wait_for_app_or_raise():
    attempts = 150
    delay_seconds = 0.2

    for _ in range(attempts):
        time.sleep(delay_seconds)
        try:
            try:
                conn = http.client.HTTPConnection("localhost", 9178)
                conn.request("HEAD", "/")
                return
            except ConnectionError:
                # It's fine, this is why we're doing this check.
                pass
        finally:
            conn.close()

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
    selenium.get("http://localhost:9178/")

    selenium.find_element_by_name("first_name").send_keys("Octave")
    selenium.find_element_by_name("last_name").send_keys("Garnier")
    selenium.find_element_by_name("contact_data").send_keys("555-12345")

    selenium.find_element_by_xpath('//input[@type="submit"]').click()

    # ensure the result page has loaded
    selenium.find_element_by_xpath('//*[text()="Danke"]')

    completedProcess = subprocess.run(
        [
            *f"podman exec {container_names.db}".split(),
            *"psql -h localhost -U corona-sign-in corona-sign-in".split(),
            *"--quiet --no-align --pset=tuples_only".split(),
            *["--command", "SELECT * FROM sign_ins;"],
        ],
        stdout=subprocess.PIPE,
    )

    assert (
        completedProcess.stdout.decode("utf-8").strip()
        == f"Octave|Garnier|555-12345|{date.today().isoformat()}"
    )
