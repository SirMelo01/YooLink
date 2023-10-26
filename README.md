# YooLink

Wie ich alles aufgesetzt habe und gehostet habe:
https://www.youtube.com/watch?v=DLxcyndCvO4


-   Docker wird benutzt und deshalb muss vor allen Befehlen stehen: ()
## Local:

### Webseite starten:
        $ docker-compose -f local.yml build
        $ docker-compose -f local.yml up

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
        $ docker-compose -f production.yml run --rm django python manage.py migrate
        $ docker-compose -f production.yml run --rm django python manage.py makemigrations

### Superuser erstellen:
        $ docker-compose -f production.yml run --rm django python manage.py createsuperuser
        $ bestehender Superuser:

### File Compress:
        $ docker-compose -f production.yml run --rm django python manage.py collectstatic
        $ docker-compose -f production.yml run --rm django python manage.py compress --force

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


## Deployment

https://www.youtube.com/watch?v=DLxcyndCvO4 hier ab minute 28




ssh root@195.201.112.17

