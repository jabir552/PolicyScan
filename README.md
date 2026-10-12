# A2P 10DLC Privacy Policy & Terms of Service Compliance Checker

An automated compliance inspection web application built with **Python 3**, **Django**, **BeautifulSoup4**, **Requests**, and **Bootstrap 5**.

This tool checks whether a customer's **Privacy Policy (PP)** and **Terms of Service (TOS)** comply with strict **A2P 10DLC carrier requirements and Twilio registration guidelines** (including requirements mandatory for all entities and Sole Proprietors starting June 30, 2026).

---

## 🌟 Key Features

1. **Dual URL Input**: Enter a Privacy Policy URL and/or a Terms of Service URL.
2. **Web Content Retrieval & Parsing**:
   - Secure fetching via `requests` with standard User-Agent headers, timeouts, and error handling.
   - HTML cleanup, sentence boundary segmentation, hyperlink extraction, and bold font styling detection using `BeautifulSoup`.
3. **Automated Compliance Verification**:
   - Evaluates requirements with configurable, transparent rules.
   - Detects **PASS**, **MISSING**, or **NEEDS MANUAL REVIEW** statuses.
   - Extracts verbatim **evidence snippets** from webpage text.
4. **Twilio & Carrier Rule Checklist**:
   - **Privacy Policy**:
     - Data collection and usage disclosure.
     - Mobile phone / text-messaging information non-sharing guarantee (exempt from marketing/affiliates).
     - Standard safe-harbor originator opt-in non-sharing statement.
   - **Terms of Service**:
     - Brand or messaging program name.
     - Program description (nature of SMS messages).
     - Standard message & data rates disclosure (`Message and data rates may apply`).
     - Message frequency disclosure (`Message frequency varies` or recurring messages).
     - Customer support contact information (email, telephone, or support desk).
     - **STOP** opt-out instructions.
     - **HELP** assistance instructions.
     - **Bold formatting verification** for both `STOP` and `HELP` in HTML tags (`<b>`, `<strong>`, or bold CSS).
     - Direct hyperlink to Privacy Policy.
     - Carrier disclaimer (`Carriers are not liable for delayed or undelivered messages`).
5. **Audit History & Reporting**:
   - All scans stored persistently in **SQLite** via Django ORM.
   - Visual dashboard with progress scorecards and color-coded badges.
   - **One-click CSV Export** to generate compliance audit documentation.
6. **Built-in Demo Samples**:
   - Pre-loaded compliant and non-compliant policy test pages accessible directly within the app.

---

## 🚀 Quick Start Guide

### 1. Prerequisites
Ensure you have Python 3.10+ installed:
```bash
python --version
```

### 2. Install Dependencies
```bash
pip install django beautifulsoup4 requests
```

### 3. Initialize SQLite Database
Apply migrations to create the database tables:
```bash
python manage.py migrate
```

### 4. Run Development Server
```bash
python manage.py runserver
```
Visit `http://127.0.0.1:8000/` in your browser.

---

## 🧪 Testing

Run the automated test suite covering all compliance rules, views, and CSV generation:
```bash
python manage.py test
```

---

## 📂 Project Architecture

```
d:/TL_Checker/
├── config/
│   ├── settings.py          # Django settings & INSTALLED_APPS registration
│   ├── urls.py              # Root URL routing
│   └── wsgi.py
├── checker/
│   ├── models.py            # ScanReport & ComplianceResult models (SQLite)
│   ├── fetcher.py           # Requests + BeautifulSoup parser & bold detector
│   ├── compliance_engine.py # Configurable rule engine for PP & TOS
│   ├── views.py             # Dashboard, scan runner, reports & CSV export views
│   ├── urls.py              # App routing
│   ├── tests.py             # Unit & integration tests
│   ├── templates/
│   │   └── checker/
│   │       ├── base.html          # Responsive Bootstrap 5 layout
│   │       ├── index.html         # Scan form & recent audits
│   │       ├── report_detail.html # Full report, scorecards & snippets
│   │       ├── history.html       # Historical scan table
│   │       └── sample_pages.html  # Interactive test policy pages
└── manage.py
```
