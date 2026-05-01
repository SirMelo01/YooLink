# YooLink

Wie ich alles aufgesetzt habe und gehostet habe:
https://www.youtube.com/watch?v=DLxcyndCvO4


-   Docker wird benutzt und deshalb muss vor allen Befehlen stehen: ()
## Local:

### Webseite starten:
        $ docker-compose -f local.yml build
        $ docker-compose -f local.yml up

### Load Translations:
        - {% load i18n %}
        - {% trans "FAQ_TITLE" %}
        $ docker-compose -f local.yml run --rm django python manage.py makemessages -l de -l en
        $ docker-compose -f local.yml run --rm django python manage.py compilemessages

### Django Migrations:
        $ docker-compose -f local.yml run --rm django python manage.py makemigrations
        $ docker-compose -f local.yml run --rm django python manage.py migrate 

### App erstellen:
        $ docker-compose -f local.yml run --rm django python manage.py startapp namederapp

### Superuser erstellen:
        $ docker-compose -f local.yml run --rm django python manage.py createsuperuser

### File Compress:
        $ docker-compose -f local.yml run --rm django python manage.py collectstatic
        $ docker-compose -f local.yml run --rm django python manage.py compress --force

## Production:
        $ in der Console erst mal in Ordner YooLink gehen: cd YooLink/

### Webseite starten:
        $ docker-compose -f production.yml build
        $ docker-compose -f production.yml up

### Django Migrations:
        $ docker-compose -f production.yml run --rm django python manage.py makemigrations
        $ docker-compose -f production.yml run --rm django python manage.py migrate

### Superuser erstellen:
        $ docker-compose -f production.yml run --rm django python manage.py createsuperuser
        $ bestehender Superuser:

### File Compress:
        $ docker-compose -f production.yml run --rm django python manage.py collectstatic
        $ docker-compose -f production.yml run --rm django python manage.py compress --force


### Load Translations Production:
        $ docker-compose -f production.yml run --rm django python manage.py makemessages -l de -l en
        $ docker-compose -f production.yml run --rm django python manage.py compilemessages

### .django Manuell kopieren:
-   da wichtige schlüssel in der datei liegen, müssen diese per hand kopiert werden

        $ cd .envs/
        $ cd .production/
        $ nano .django 

### Konsole verlassen:
        $ exit




## Tailwind:
        $ npm run build
        $ npm run watch

## Tests / Sicherheitsnetz:

### Lokal alle Tests ausfÃ¼hren:
        $ docker-compose -f local.yml run --rm django pytest

### Lokal nur CMS-/Shop-Sicherheitsnetz ausfÃ¼hren:
        $ docker-compose -f local.yml run --rm django pytest tests/test_cms_2fa.py tests/test_cms_core_modules.py tests/test_shop_safety_net.py tests/test_public_pages_safety_net.py

### Lokal mit frischer Testdatenbank:
        $ docker-compose -f local.yml run --rm django pytest --create-db

### Production-Check vor Deployment:
-   Nicht gegen die echte Produktionsdatenbank testen. Vorher eine separate Test-Env oder Staging-Env nutzen.
-   Das Production-Image enthÃ¤lt keine lokalen Test-Dependencies wie pytest. Deshalb vor dem Deployment das komplette Test-Sicherheitsnetz lokal/CI ausfÃ¼hren und das Production-Image separat mit Django Checks prÃ¼fen:

        $ docker-compose -f local.yml run --rm django pytest
        $ docker-compose -f production.yml run --rm django python manage.py check --deploy --settings=config.settings.production

### Prompt fÃ¼r Codex vor Updates:
        Analysiere die anstehenden Dependency-Updates. FÃ¼hre zuerst das komplette Test-Sicherheitsnetz lokal aus, behebe Regressionen in kleinen Schritten und fasse danach zusammen, welche CMS-, Shop-, Auth-, Medien- und Public-Page-Flows grÃ¼n sind.


## Deployment

https://www.youtube.com/watch?v=DLxcyndCvO4 hier ab minute 28




ssh root@195.201.112.17

