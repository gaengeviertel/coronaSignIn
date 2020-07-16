![CI](https://github.com/voidus/coronaSignIn/workflows/CI/badge.svg)
# Simple Sign-In system to comply with Hamburg, Germany corona regulations

As of July 2020, Hamburg (Germany) requires bars, pubs and the like to record
the names and contact data for all visitors to help with COVID-19 contact
tracing. This application allows guests to fill in their data on their phones.

**IMPORTANT**: This document contains suggestions on how to deal with this
regulation, but we are no legal professional. Just as the rest of this software,
this document is provided *as-is*, with **no guarantees at all**, including for
correctness of information or absence of critical bugs.

Nonetheless, we hope this is helpful, but you need to decide if there is an
unacceptable risk for you.

## Architecture

The application will write the data into an PostgreSQL database. At the moment
we only officially support deployment on podman, but we assume that docker and
platforms such as kubernetes should work fine. If you are interested in running
this application and need any support, don't hesitate to [create an issue](https://github.com/voidus/coronaSignIn/issues)

## Deployment

**Important**: Please make sure to follow the Production Checklist if you deploy
this application!

Build the docker image using `podman build -t corona-sign-in .`

The application needs a postgresql database. We currently do not provide
a production-grade pod definition, but looking into `kube-dev.yml` should tell
you how the application can be run.

You need to **migrate the database** before you can use the service:

```
podman exec corona-sign-in-app \
    flask db upgrade
```

If you struggle with setting things up and require more instructions, please
[let us know](https://github.com/voidus/coronaSignIn/issues).

### Production Checklist

Please make sure to take care of the following topics before going live. They
are listed first and then discussed in detail.

- **Backups**: You need to make sure that you can provide the data in case the
    Gesundheitsamt requests it.
- **Data pruning**: The regulations require you to provide data for the previous
    two weeks in the case of a known case of COVID-19, so you shouldn't store
    forever.

#### Backups
Given that you also need to delete data from backups after four weeks, we
suggest the following approach:

- Set up a cronjob to backup the data for the previous day every morning at e.g.
    3 am.
- Use the date of the data you backed up in the filename
- In a similar cronjob, remove all files that are older than 28 days.

The shell command to save a backup is

```
YESTERDAY=$(date -d yesterday '+%Y-%m-%d')
podman exec corona-sign-in-db \
    psql -h localhost -U corona-sign-in corona-sign-in \
    --csv
    --command "SELECT * FROM sign_ins WHERE signed_in_at::date = $YESTERDAY"
    > "/path/to/backup/folder/corona-sign-in-${YESTERDAY}.csv"
```

You can delete old files with the following commands. Make sure there are no
other files in that folder!:

```
find /path/to/backup/folder -daystart -mtime +28 -delete
```

#### Data pruning

This deletes all entries that are older than four weeks (28 days). This should
be run in a cronjob. Please test this thoroughly! If you accidentally delete
data earlier than you mean to, you won't be able to produce it in case of
a COVID-19 infection!

```
podman exec corona-sign-in-db \
    psql -h localhost -U corona-sign-in corona-sign-in \
    --command 'DELETE FROM sign_ins WHERE NOW()::date - signed_in_at::date > 28;'
```

For how to delete backups, see the Backups section

### How to export data

This gets all saved sign-ins and stores them in a file named like
`corona-sign-in-2020-06-04-to-2020-07-02.csv`. Test this after setting
everything up, you might need to adjust the pod name or postgresql credentials!

You will only ever need to export data in case of COVID-19 infection and you
should delete your local copy of the csv file after handing it over to the
authorities.

```
podman exec corona-sign-in-db \
    psql -h localhost -U corona-sign-in corona-sign-in \
    --csv --command 'SELECT * FROM sign_ins;' \
    > "corona-sign-in-$(date -I -d '28 days ago')-to-$(date -I).csv"
```

## Customise Content & Look

### Content
#### Data Protection Policy
To comply with GDPR regulations an entity that operates a website or application, which collects and processes personal data, needs to provide a data protection policy. To match the look & feel of the application you can add the contents of your data protection policy inside the `{% block content %}` section of this template file: 
```
/src/templates/data-protection.html.jinja2
```

**IMPORTANT**: As already mentioned at the beginning, this document contains suggestions on how to deal with legal
regulations, but we are no legal professional and this document contains **no legal advise**. Just as the rest of this software,
the data protection template provides **no guarantees at all**, including for
correctness of information.

#### Impressum
To link to your website's impressum update the `#` in the following line of the footer template with your URL link:
```
<a href="#" target="_blank">Impressum</a>
/src/templates/_footer.html.jinja2
```

#### Form, Success & Error Page
To customise the headlines and description texts for the form, the success page and the error page you will need to edit the text in the respective template files:

Form (Main Page): 
```
/src/templates/index.html.jinja2
```

Success Page: 
```
/src/templates/success-page.html.jinja2
```

Error Page: 
```
/src/templates/error-page.html.jinja2
```

### Images
You will be able to customize the application with your images by only replacing and adding image files. There's no need to change template or stylesheet code unless you want to do so. 

You can add your Logo to the header section of the form and success page by replacing the following file:
```
/src/static/images/logo.jpg
```

If you want to add an image to the success page, which will be shown to the user after they successfully submitted the form, you can do so by adding the following file:
```
/src/static/images/success.jpg
```

If you want to customise the image on the error page, you can do so by replacing the following file:
```
/src/static/images/error.jpg
```

To add a [favicon](https://en.wikipedia.org/wiki/Favicon) to the web pages you can add the following file:
```
/src/static/images/favicon.ico
```

### Color
In order to customise the primary color used for headlines, buttons and links replace all occurences of the value `darkseagreen` with your preferred color value (keyword (e.g. `lime`), hex code (e.g. `#00FF00`) or rgb decimal code (e.g `rgb(0,255,0)`)) in the following file:
```
/src/static/styles/main.css
```

## Dev Setup

The application requires Python version 3.8.
With `direnv` installed, you only need to install pipenv and then you're set.

Otherwise, you need to install `pipenv` first. Then, install the dependencies
using `pipenv install`.
You can run the project in development mode using
```
env \
    FLASK_ENV=development \
    CORONA_SIGN_IN_SECRET_KEY="insecure secret key" \
    CORONA_SIGN_IN_DATABASE_URI="sqlite:///${PWD}/db.sqlite" \
    pipenv run flask run
```

If you have direnv installed (highly recommended), this will work automatically,
and you can start the dev server using `flask run`

### Tests

Run the tests using `pipenv run pytest`. You can also auto-rerun tests while
you're changing code with `pipenv run invoke tdd`. It will only re-run tests
affected by your changes, so it should be a pretty good feedback loop.

The selenium tests are marked with `slow`. If you don't have selenium installed,
you can skip them using `pytest -m 'not slow'`.

The container-tests are not run by default, since they are even slower and need
[podman installed](https://podman.io/getting-started/installation). You can run
them using `inv containertests`.

The containertests are a bit hard to debug. Here are some things that can help:

- Use `pytest tests_container -s` to show stdout and stderr during the test run.
    This shows you podman output, so you can see why containers aren't starting
    etc.
- Use one of the following ways to stop the tests:
    - `pytest tests_container --pdb` will break on failures
    - Inserting `breakpoint()` will break at that location
    - Removing the `finally`-part from `tests_container.tests.running_pod` will
        keep the containers around after the test run
- When stopped, these are some ways to get information:
    - `podman logs corona-sign-in-automatic-test-app` will show you the app logs
    - `podman exec -ti corona-sign-in-automatic-test-app bash` will give you
        a shell in the app container
    - `podman exec -ti corona-sign-in-automatic-test-db psql -h localhost -U corona-sign-in corona-sign-in`
        will get you a database shell

### Style

Use (black)[https://github.com/ambv/black] to format your code. It will be
installed as part of the dev dependencies.

### Pre-Commit

To automatically run black and check for a few other common issues on commit,
run `pre-commit install`. It is installed as part of the dev requirements and
will set everything up. You only ever need to run it once.

## Configuration

Configuration is done via environment variables. Have a look at `src/config.py`,
kube-dev.yml or the examples in this readme to see which configuration options
are possible.

### Running the application manually

1. Build the image
    `podman build -t corona-sign-in .`
2. Create the pod
    `podman pod create --name corona-sign-in --publish 8080:8080`
3. Run the database
    `podman container run -d --name corona-sign-in-db --pod corona-sign-in -e POSTGRES_PASSWORD=pass -e POSTGRES_USER=corona-sign-in -e POSTGRES_DB=corona-sign-in postgres`
4. Migrate the database
    `podman container run --pod corona-sign-in -e CORONA_SIGN_IN_DATABASE_URI="postgresql://corona-sign-in:pass@localhost/corona-sign-in" -e CORONA_SIGN_IN_SECRET_KEY="irrelevant" corona-sign-in flask db upgrade`
5. Run the application
    `podman container run -d --pod corona-sign-in -e CORONA_SIGN_IN_DATABASE_URI="postgresql://corona-sign-in:pass@localhost/corona-sign-in" -e CORONA_SIGN_IN_SECRET_KEY="irrelevant" corona-sign-in`

### Running the application using the kube file

1. Build the image
    `podman build -t corona-sign-in .`
2. Load the kube file
    `podman play kube kube-dev.yml`
3. Migrate the database
    `podman exec corona-sign-in-app flask db upgrade`

#### Get a database shell

`podman container run -ti --rm --pod corona-sign-in postgres -h localhost -U corona-sign-in corona-sign-in`
