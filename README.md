# Travel Social Media Website Project (Flask Version)

## Project Overview

This is a group project for building a travel social media website where users can sign up, sign in, submit travel itineraries, browse itineraries, view itinerary details, like/favorite itineraries, and post comments.

The frontend uses HTML, CSS, JavaScript, jQuery, and AJAX/fetch requests. The backend uses Flask, Flask-SQLAlchemy, Flask-WTF, and Flask-Migrate to support routing, form handling, authentication, database interaction, and schema migrations.

---

## 🧱 Project Structure & Git Branch Strategy

---

## Environment Setup for First Run

### 1️⃣ Pull the repository

```bash
git pull
git pull origin dev
```

### 2️⃣ Create a virtual environment

```bash
python -m venv venv
```

### 3️⃣ Activate the virtual environment

Windows:

```bash
venv\Scripts\activate
```

Mac/Linux:

```bash
source venv/bin/activate
```

### 4️⃣ Install dependencies

```bash
pip install -r requirements.txt
```

### 5️⃣ Run the project

```bash
python app.py
```

---

## ✏️ Development Steps

1. Modify code such as Flask routes, templates, JavaScript, CSS, models, or database migrations.
2. Test your changes locally.
3. Ensure there are no errors before committing.
4. Commit and push your changes to the correct branch.

---

## ✅ Running Tests

The project uses Python `unittest` for both unit tests and Selenium system tests.

### Run all tests

From the project root directory:

```bash
python -m unittest discover -s tests -v
```

If Python cannot find the `app` module, run with `PYTHONPATH`:

Mac/Linux:

```bash
PYTHONPATH=. python -m unittest discover -s tests -v
```

Windows PowerShell:

```powershell
$env:PYTHONPATH="."
python -m unittest discover -s tests -v
```

### Run unit tests only

```bash
python -m unittest discover -s tests/unit -v
```

Or run a specific unit test file:

```bash
python -m unittest tests.unit.test_auth -v
python -m unittest tests.unit.test_submit -v
python -m unittest tests.unit.test_browse_view -v
python -m unittest tests.unit.test_home_search -v
```

### Run Selenium system tests only

```bash
python -m unittest discover -s tests/system -v
```

Or run a specific Selenium test file:

```bash
python -m unittest tests.system.test_auth_system -v
python -m unittest tests.system.test_submit_system -v
python -m unittest tests.system.test_browse_view_system -v
python -m unittest tests.system.test_home_search_system -v
```

### Selenium browser setup

The Selenium tests run in a real browser in headless mode. The project can use Chrome, Edge, or Firefox depending on the browser installed on the machine.

Recommended approach:

```bash
SELENIUM_BROWSER=chrome python -m unittest discover -s tests/system -v
```

Other supported options:

```bash
SELENIUM_BROWSER=edge python -m unittest discover -s tests/system -v
SELENIUM_BROWSER=firefox python -m unittest discover -s tests/system -v
```

Windows PowerShell example:

```powershell
$env:SELENIUM_BROWSER="edge"
python -m unittest discover -s tests/system -v
```

If no browser is specified, the tests should try an available supported browser. If Selenium cannot start a browser, install Google Chrome, Microsoft Edge, or Firefox, then run the tests again.

### Current test coverage

The test suite includes:

* Authentication unit and Selenium tests.
* Itinerary submission unit and Selenium tests.
* Browse itinerary page unit and Selenium tests.
* View itinerary page unit and Selenium tests.
* API tests for itinerary data, likes, comments, and access control.

---

## ⚠️ Important Notes (Very Important!!!)

### ❌ DO NOT commit the following:

* `venv/` or `.venv/` virtual environment folders
* `__pycache__/`
* `.db` database files, unless specifically required for a demo
* Local browser driver binaries, unless the team has agreed to include them

Make sure `.gitignore` is properly configured.

---

## 📦 Environment Synchronization

Dependencies are managed via `requirements.txt`.

### When you install new packages:

```bash
pip freeze > requirements.txt
```

Then commit and push the updated `requirements.txt`.

### For other team members:

```bash
pip install -r requirements.txt
```
---

## 🚀 Tech Stack

### Frontend

* HTML
* CSS
* JavaScript
* jQuery
* AJAX / Fetch API
* Google Maps JavaScript API

### Backend

* Python
* Flask 3.1.3
* Jinja2 3.1.6
* Werkzeug 3.1.8
* ItsDangerous 2.2.0
* Blinker 1.9.0
* Click 8.3.3

### Database and ORM

* SQLite for local development/testing
* SQLAlchemy 2.0.49
* Flask-SQLAlchemy 3.1.1
* Flask-Migrate 4.1.0
* Alembic 1.18.4
* Greenlet 3.5.0

### Forms and Validation

* Flask-WTF 1.3.0
* WTForms 3.2.2

### Testing

* Python unittest
* Selenium 4.43.0
* Chrome / Edge / Firefox headless browser testing

### Selenium and Browser Support Dependencies

* attrs 26.1.0
* certifi 2026.4.22
* cffi 2.0.0
* h11 0.16.0
* idna 3.13
* outcome 1.3.0.post0
* pycparser 3.0
* PySocks 1.7.1
* sniffio 1.3.1
* sortedcontainers 2.4.0
* trio 0.33.0
* trio-websocket 0.12.2
* typing_extensions 4.15.0
* urllib3 2.7.0
* websocket-client 1.9.0
* wsproto 1.3.2

### Template and Migration Dependencies

* Mako 1.3.12
* MarkupSafe 3.0.3

### Windows Compatibility

* colorama 0.4.6