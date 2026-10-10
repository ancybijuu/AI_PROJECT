# FAQ Chatbot

A Django + REST Framework backend that answers customer-support questions
by matching them against a knowledge base of FAQs using classic NLP:
tokenization + stemming (NLTK) and TF-IDF + cosine similarity (scikit-learn).
Includes a simple chat UI. Built as Task 2 of an internship-style
submission.

## Tech stack

| Layer      | Technology |
|------------|-----------|
| Frontend   | HTML5, CSS3, vanilla JavaScript (fetch API) — chat bubble UI |
| Backend    | Python, Django |
| API        | Django REST Framework |
| NLP        | NLTK (`wordpunct_tokenize`, `PorterStemmer`) for preprocessing |
| Matching   | scikit-learn `TfidfVectorizer` + `cosine_similarity` |
| Database   | SQLite (via Django ORM) — stores FAQs and chat history |
| Other      | django-cors-headers, python-dotenv, DRF throttling, unit tests |

## How matching works

1. **Preprocess** every FAQ question and every incoming user message the
   same way: lowercase → tokenize (NLTK `wordpunct_tokenize`) → drop
   punctuation/stopwords → stem (NLTK `PorterStemmer`). E.g.
   `"How can I track my order?"` → `"track order"`.
2. **Vectorize** the whole FAQ set with a TF-IDF vectorizer, fit once and
   cached in memory (`chatbot_api/matcher.py`).
3. **Rank** every FAQ against the incoming message by cosine similarity.
4. If the top score clears `FAQ_CONFIDENCE_THRESHOLD` (default `0.25`,
   configurable via `.env`), return that FAQ's answer. Otherwise, return a
   fallback message plus the top 3 alternates as clickable suggestions —
   so the bot never confidently makes something up, it just says "not
   sure" and offers close matches.

This is intentionally a from-scratch, inspectable pipeline rather than a
single opaque library call — useful for explaining *why* the bot answered
the way it did, which matters for an internship demo.

## Features

- **FAQ knowledge base** — 28 seeded Q&As for a fictional e-commerce store
  ("ShopEase"), covering orders/shipping, payments, returns/refunds,
  account, and promotions (`chatbot_api/data/faqs.json`).
- **NLP preprocessing** with NLTK — tokenization + stemming, no
  `nltk.download(...)` corpus required (uses regex-based tokenization and
  the algorithmic Porter stemmer, both bundled with the library), so
  there's nothing to download or fail behind a firewall.
- **Intent matching** via TF-IDF + cosine similarity, with a confidence
  threshold and graceful "I'm not sure" fallback + suggestions.
- **Chat UI** — bubble-style conversation, a sidebar to browse/click any
  FAQ directly, confidence shown under each answer, suggestion chips on
  low-confidence replies, and a clear-chat action.
- **REST API** decoupled from the frontend (see below).
- **Chat history** persisted and exposed via the API, browsable in Django
  admin alongside the FAQ table (with a "Rebuild search index" admin action).
- **Automated tests** (`chatbot_api/tests.py`, 16 tests) covering
  preprocessing, the matcher directly, and every API endpoint — all run
  fully offline.
- **Management command** (`load_faqs`) to seed/reload the FAQ set from JSON.

## Project structure

```
faq_chatbot_project/
├── manage.py
├── requirements.txt
├── .env.example
├── faq_chatbot_project/        # Django project config
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py / asgi.py
├── chatbot_api/                 # The REST API app
│   ├── data/faqs.json           # Seed FAQ dataset
│   ├── management/commands/
│   │   └── load_faqs.py         # Loads faqs.json into the DB
│   ├── models.py                # FAQ, ChatLog
│   ├── nlp.py                   # Tokenize / stopwords / stem
│   ├── matcher.py               # TF-IDF + cosine similarity matcher
│   ├── serializers.py
│   ├── views.py                 # API endpoints
│   ├── urls.py
│   ├── admin.py
│   └── tests.py
├── templates/
│   └── index.html               # Chat UI (Django template)
└── static/
    ├── css/style.css
    └── js/script.js             # Calls the REST API with fetch()
```

## API endpoints

| Method | Endpoint | Description |
|--------|----------|--------------|
| GET    | `/api/faqs/` | List every FAQ (id, question, answer, category) |
| POST   | `/api/chat/` | Ask a question, get the best-matching answer |
| GET    | `/api/chat/history/?limit=10` | Recent chat turns |
| DELETE | `/api/chat/history/clear/` | Wipe chat history |
| POST   | `/api/reindex/` | Rebuild the TF-IDF index after editing FAQs |

**POST /api/chat/** request body: `{ "message": "How do I track my order?" }`

Confident-match response:

```json
{
  "id": 1,
  "user_message": "How do I track my order?",
  "answer": "Once your order ships, we email you a tracking link...",
  "matched_question": "How can I track my order?",
  "matched_faq_id": 1,
  "confidence": 1.0,
  "is_confident": true,
  "suggestions": [ ... top 3 matches, for transparency ... ],
  "created_at": "2026-09-23T09:31:15Z"
}
```

Low-confidence response (`matched_question` is `null`, `answer` is the
fallback message, `suggestions` holds the closest alternates):

```json
{
  "answer": "I'm not confident I have the right answer for that yet...",
  "matched_question": null,
  "confidence": 0.0,
  "is_confident": false,
  "suggestions": [ {"id": 17, "question": "...", "score": 0.0}, ... ]
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
cp .env.example .env

# 4. Set up the database
python manage.py migrate

# 5. Seed the FAQ knowledge base
python manage.py load_faqs

# 6. (optional) create an admin user
python manage.py createsuperuser

# 7. Run the dev server
python manage.py runserver
```

Open **http://127.0.0.1:8000/** for the chat UI, or
**http://127.0.0.1:8000/api/** for the browsable DRF API root.

Unlike the translation project, **this one needs no internet access at
runtime** — NLTK's tokenizer/stemmer and scikit-learn's TF-IDF/cosine
similarity both run entirely locally.

## Running tests

```bash
python manage.py test chatbot_api
```

## Editing the FAQ set

Edit `chatbot_api/data/faqs.json` and re-run `python manage.py load_faqs`
(it skips duplicates by exact question text and rebuilds the search index
automatically), or add/edit FAQs directly in Django admin and use the
"Rebuild search index" action afterward — the TF-IDF index is only built
from what's in the database at reindex time.

## Design notes

- **Why TF-IDF + cosine similarity instead of an embedding model?** It's
  fast, needs no external model download or API key, and is genuinely
  the standard baseline for small, static FAQ sets — a reasonable
  default to demo, with a clear upgrade path (below) if the FAQ set grows
  or paraphrases get trickier than word-overlap can handle.
- **Why a confidence threshold + fallback instead of always answering?**
  A chatbot that confidently returns the "closest" FAQ even when nothing
  is really relevant erodes trust fast. Returning suggestions instead of
  a wrong answer is both more honest and more useful.
- **Why log every chat turn?** Besides the "recent chat" UI panel, low-
  confidence logs are a practical signal for which FAQs are missing from
  the knowledge base — a real analytics use for the history table.

## Future enhancements

- Swap TF-IDF for sentence embeddings (e.g. `sentence-transformers`) for
  better semantic matching on paraphrases that don't share many words.
- Multi-turn context (remember the last question when the user says
  "and what about returns?").
- Per-user chat history instead of a global log.
- A small evaluation script measuring top-1 match accuracy against a
  held-out set of paraphrased test questions — good evidence of NLP rigor
  for an internship writeup.
- Dockerfile + CI (GitHub Actions running `manage.py test`).

## License

MIT — free to use for learning, coursework, or internship submissions.


## Version 2 features

This upgraded version adds an explainable, context-aware demo layer while
keeping the core offline TF-IDF architecture:

- **Explainable answers** — confidence percentage, confidence label, matched FAQ,
  and overlapping processed terms.
- **Conversation context** — the browser sends the previous matched FAQ question
  so follow-ups such as "what about returns?" can use recent context.
- **Related knowledge** — the API exposes the next-best FAQ matches when they
  are sufficiently related to the current question.
- **Answer feedback** — Helpful / Not helpful feedback is persisted with each
  chat log.
- **Analytics dashboard** — total questions, confidence rate, average confidence,
  popular FAQs, and repeated low-confidence questions ("FAQ gaps").
- **Evaluation dashboard** — an explicit FAQ self-match sanity test with Top-1
  and Top-3 retrieval rates. This is not presented as a held-out benchmark.
- **Improved UI** — confidence meter, explanation panel, feedback buttons,
  related knowledge, and an analytics drawer.
- **New endpoints**:
  - `POST /api/chat/<id>/feedback/`
  - `GET /api/analytics/`
  - `GET /api/evaluation/`

### Upgrade / run

```bash
python manage.py migrate
python manage.py load_faqs
python manage.py test chatbot_api
python manage.py runserver
```

The chatbot remains local/offline at runtime; no external AI API is required.
