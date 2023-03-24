# YooLink

Wie ich alles aufgesetzt habe und gehostet habe:
https://www.youtube.com/watch?v=DLxcyndCvO4


Docker wird benutzt und deshalb muss vor allen Befehlen stehen: ()
## Local:

### Webseite starten:
        $ python manage.py createsuperuser
docker-compose -f local.yml build
docker-compose -f local.yml up

### Django Migrations:
docker-compose -f local.yml run --rm django python manage.py makemigrations
docker-compose -f local.yml run --rm django python manage.py migrate 

### App erstellen:
docker-compose -f local.yml run --rm django python manage.py startapp cms

### Superuser erstellen:
docker-compose -f local.yml run --rm django python manage.py createsuperuser

### File Compress:
docker-compose -f local.yml run --rm django python manage.py collectstatic
docker-compose -f local.yml run --rm django python manage.py compress --force





## Production:
in der Console erst mal in Ordner YooLink gehen: cd YooLink/

### Webseite starten:
docker-compose -f production.yml build
docker-compose -f production.yml up

### Django Migrations:
docker-compose -f production.yml run --rm django python manage.py migrate
docker-compose -f production.yml run --rm django python manage.py makemigrations

### Superuser erstellen:
docker-compose -f production.yml run --rm django python manage.py createsuperuser
bestehender Superuser: Sepp PW: 1234Sepp1234

### .django Manuell kopieren:
da wichtige schlüssel in der datei liegen, müssen diese per hand kopiert werden:
cd .envs/
cd .production/
nano .django 

### Konsole verlassen:
exit




## Tailwind:
npm run build
npm run watch

License: MIT

## Settings

Moved to [settings](http://cookiecutter-django.readthedocs.io/en/latest/settings.html).

## Basic Commands

### Setting Up Your Users

-   To create a **normal user account**, just go to Sign Up and fill out the form. Once you submit it, you'll see a "Verify Your E-mail Address" page. Go to your console to see a simulated email verification message. Copy the link into your browser. Now the user's email should be verified and ready to go.

-   To create a **superuser account**, use this command:

        $ python manage.py createsuperuser

For convenience, you can keep your normal user logged in on Chrome and your superuser logged in on Firefox (or similar), so that you can see how the site behaves for both kinds of users.

### Type checks

Running type checks with mypy:

    $ mypy yoolink

### Test coverage

To run the tests, check your test coverage, and generate an HTML coverage report:

    $ coverage run -m pytest
    $ coverage html
    $ open htmlcov/index.html

#### Running tests with pytest

    $ pytest

### Live reloading and Sass CSS compilation

Moved to [Live reloading and SASS compilation](https://cookiecutter-django.readthedocs.io/en/latest/developing-locally.html#sass-compilation-live-reloading).

### Celery

This app comes with Celery.

To run a celery worker:

``` bash
cd yoolink
celery -A config.celery_app worker -l info
```

Please note: For Celery's import magic to work, it is important *where* the celery commands are run. If you are in the same folder with *manage.py*, you should be right.

To run [periodic tasks](https://docs.celeryq.dev/en/stable/userguide/periodic-tasks.html), you'll need to start the celery beat scheduler service. You can start it as a standalone process:

``` bash
cd yoolink
celery -A config.celery_app beat
```

or you can embed the beat service inside a worker with the `-B` option (not recommended for production use):

``` bash
cd yoolink
celery -A config.celery_app worker -B -l info
```

## Deployment

https://www.youtube.com/watch?v=DLxcyndCvO4 hier ab minute 28

### Docker

See detailed [cookiecutter-django Docker documentation](http://cookiecutter-django.readthedocs.io/en/latest/deployment-with-docker.html).
