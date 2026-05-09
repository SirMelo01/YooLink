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

## Externe YooLink API

Developer API Keys werden im CMS unter `Einstellungen -> Developer Settings` erstellt. Der vollstaendige Schluessel wird nur direkt nach dem Erstellen angezeigt und danach nur gehasht gespeichert.

### Blog API

Basis-Endpoint:

        /api/cms/blog/

Authentifizierung:

        Authorization: Bearer <api-key>

Read-only Keys duerfen `GET` verwenden. Write Keys duerfen zusaetzlich `POST`, `PATCH`, `PUT` und `DELETE` verwenden.

`GET /api/cms/blog/` liefert eine kompakte Liste ohne `markdown`, `body`, `code` und Sprachvarianten. Vollstaendige Blogdaten inklusive Markdown, HTML-Body und Sprachvarianten gibt es ueber `GET /api/cms/blog/<id>/`.

Minimaler JSON-Body zum Erstellen eines Blogs:

        {
          "title": "Event Rueckblick",
          "description": "Kurzer SEO-Teaser fuer Blogkarten und Meta Description.",
          "markdown": "## Rueckblick\n\nMarkdown-Inhalt des automatisch generierten Blogartikels.",
          "active": true,
          "language": "de"
        }

Alternativ kann weiterhin `body` als HTML oder `code` als Blog-Builder-JSON gesendet werden. Die API erzeugt daraus automatisch Markdown, damit KI-Workflows eine klare Textquelle haben.

Content-Bilder fuer Markdown-Blogs koennen per Multipart direkt hochgeladen werden:

        POST /api/cms/blog/media/
        Authorization: Bearer <write-api-key>
        Content-Type: multipart/form-data

        file: event.png
        title: Event Bild
        alt_text: Volles Haus beim Event

Die Antwort enthaelt `url`, `markdown` und `html`. Fuer KI-Workflows reicht es meist, das `markdown`-Snippet direkt in den Blog-Markdown einzusetzen. Ein Titelbild kann beim Erstellen oder Aktualisieren eines Blogs weiterhin als Multipart-Feld `title_image` an `/api/cms/blog/` bzw. `/api/cms/blog/<id>/` gesendet werden.

Wenn du den Blog als JSON erstellst, kann `title_image` keine URL sein. Lade das Bild vorher ueber `/api/cms/blog/media/` hoch und sende danach die erhaltene `id` als `title_image_media_id`:

        {
          "title": "Event Rueckblick",
          "description": "Kurzer SEO-Teaser fuer Blogkarten und Meta Description.",
          "markdown": "## Rueckblick\n\nMarkdown-Inhalt.",
          "title_image_media_id": 44,
          "active": true,
          "language": "de"
        }

## Deployment

https://www.youtube.com/watch?v=DLxcyndCvO4 hier ab minute 28

ssh root@195.201.112.17


## Fehlerbehebung Space full
df -h
docker system df

docker buildx prune -af
docker builder prune -af
docker image prune -af
docker container prune -f

docker compose -f production.yml build --no-cache django
docker compose -f production.yml up

