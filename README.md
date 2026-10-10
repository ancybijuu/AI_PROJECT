# AI Language Translator

A full-stack language translation web app: a responsive HTML/CSS/JS frontend
backed by a **Django + Django REST Framework** API, with an **AI/ML language
detection** step and a translation-engine integration. Built as an
internship-style project to demonstrate frontend, backend, REST API design,
and basic ML integration in one codebase.

## Tech stack

| Layer            | Technology |
|-------------------|-----------|
| Frontend           | HTML5, CSS3, vanilla JavaScript (fetch API, Web Speech API) |
| Backend            | Python, Django |
| API                | Django REST Framework |
| AI/ML              | `langdetect` (n-gram statistical language identification) |
| Translation engine | `deep-translator` (Google Translate backend, swappable) |
| Database           | SQLite (via Django ORM) — stores translation history |
| Other              | django-cors-headers, python-dotenv, DRF throttling, unit tests |

## Features

- **Responsive UI** — text entry panel, language pickers, swap button, live
  character counter, works down to mobile widths.
- **Auto-detect source language** using a machine-learning language
  classifier (`langdetect`), with the detected language and confidence score
  shown in the UI.
- **REST API** (`/api/...`) that is fully decoupled from the frontend — you
  could swap in a React/Vue/mobile client without touching the backend.
- **Translation history** persisted to the database and exposed via the API,
  with a "recent translations" panel and a clear-history action.
- **Copy to clipboard** and **text-to-speech** (Web Speech API) for both the
  source and translated text.
- **Input validation & error handling** — DRF serializers reject empty text
  or unsupported language codes (400); a broken translation backend returns
  a clean 502 instead of a stack trace.
- **Automated tests** (`translator_api/tests.py`) covering the happy path,
  auto-detect path, and failure paths, using mocks so tests don't depend on
  network access.
- **Django admin** wired up for browsing translation history.
- **Rate limiting** (DRF `AnonRateThrottle`) on the API as a basic abuse guard.

## Project structure

```
translator_project/
├── manage.py
├── requirements.txt
├── .env.example
├── translator_project/       # Django project config
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py / asgi.py
├── translator_api/           # The REST API app
│   ├── models.py             # TranslationHistory model
│   ├── serializers.py        # Request validation
│   ├── services.py           # ML detection + translation logic
│   ├── views.py              # API endpoints
│   ├── urls.py
│   ├── admin.py
│   └── tests.py              # Unit tests (mocked network calls)
├── templates/
│   └── index.html            # Frontend page (Django template)
└── static/
    ├── css/style.css
    └── js/script.js          # Calls the REST API with fetch()
```

## API endpoints

| Method | Endpoint              | Description |
|--------|-----------------------|--------------|
| GET    | `/api/languages/`     | List supported language codes/names |
| POST   | `/api/translate/`     | Translate text (see below) |
| GET    | `/api/history/?limit=10` | Recent translation history |
| DELETE | `/api/history/clear/` | Wipe translation history |

**POST /api/translate/** request body:

```json
{
  "text": "Good morning",
  "source_lang": "auto",
  "target_lang": "fr"
}
```

Response:

```json
{
  "id": 12,
  "source_text": "Good morning",
  "translated_text": "Bonjour",
  "source_lang": "auto",
  "detected_lang": "en",
  "detection_confidence": 0.999,
  "target_lang": "fr",
  "created_at": "2026-09-13T09:12:00Z"
}
```

## Setup & run locally

```bash
# 1. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env            # edit SECRET_KEY etc. if needed

# 4. Set up the database
python manage.py migrate

# 5. (optional) create an admin user
python manage.py createsuperuser

# 6. Run the dev server
python manage.py runserver
```

Open **http://127.0.0.1:8000/** for the UI, or **http://127.0.0.1:8000/api/**
for the browsable DRF API root.

> The translation call reaches out to a public translation backend, so the
> machine running the server needs normal internet access. Everything else
> (language detection, history, validation) runs locally.

## Running tests

```bash
python manage.py test translator_api
```

All translation-backend calls are mocked in the test suite, so tests run
offline and deterministically.

## Design notes

- **Why split `services.py` from `views.py`?** So the translation engine can
  be swapped (e.g. for a self-hosted HuggingFace model, see below) without
  touching any DRF/routing code.
- **Why store history server-side instead of in the browser?** It's a more
  realistic demonstration of a persistent backend, and it means the API is
  useful to more than one client.
- **Why `langdetect` instead of just letting the translation API detect the
  language?** To show an explicit, inspectable ML component in the pipeline
  (with a confidence score) rather than treating translation as one opaque
  black box — this is the "AI/ML" layer of the stack, distinct from the
  "API integration" layer.

## Future enhancements

- Swap `deep-translator` for a self-hosted neural MT model (e.g. Hugging
  Face's `Helsinki-NLP/opus-mt-*` MarianMT models, or `facebook/nllb-200`)
  for offline translation and to remove the third-party API dependency.
  `services.py` is structured so only `translate_text()` needs to change.
  For an internship demo, a lightweight fine-tuning or evaluation notebook
  (BLEU score comparison) is a natural extension to show ML depth.
- User accounts, so translation history is per-user instead of global.
- Pagination on `/api/history/`.
- Dockerfile + docker-compose for one-command setup.
- CI (GitHub Actions) running `manage.py test` on every push.
- Deploy to Render/Railway/PythonAnywhere with Postgres in production.

## License

MIT — free to use for learning, coursework, or internship submissions.
