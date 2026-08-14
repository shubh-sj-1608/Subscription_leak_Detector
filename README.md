# Subscription Leak Detector

An AI/ML-powered web application that reads a user's bank statement and automatically detects recurring subscriptions — even when merchant names are messy or inconsistent — flags which ones are likely being wasted, and tracks silent price increases over time.

## The Problem

Bank statements list the same subscription under different, inconsistent names (e.g. `NETFLIX.COM 8829 CA` vs `NETFLIX*STREAM`), making manual tracking unreliable. Existing budgeting apps show total spending but never identify which charges are recurring, which have quietly increased in price, or which are safe to cancel.

## What This Project Does

1. **Upload** a bank statement (CSV)
2. **Clean & resolve merchant names** — NLP text cleaning + fuzzy matching groups messy variants of the same merchant into one canonical entity
3. **Detect recurring charges** — statistical analysis of transaction gaps and amount stability identifies genuine subscriptions
4. **Score risk** — an explainable, confidence-scored "cancel candidate" flag with a human-readable reason (e.g. *"price increased 27% over time; confirmed recurring pattern"*)
5. **Track price history** — a price-creep chart shows silent price increases per subscription
6. **Simulate savings** — an interactive calculator shows projected annual savings from hypothetically cancelling subscriptions
7. **Learn from feedback** — users confirm or reject flagged subscriptions, and this feedback adjusts future risk scoring (active learning loop)

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | HTML5, CSS3, JavaScript, Chart.js |
| Backend | Python, Django, Django REST Framework |
| Database | MySQL |
| ML / NLP Pipeline | Pandas, RapidFuzz, Scikit-learn, NumPy |
| Data Prototyping | Jupyter Notebook |
| Synthetic Data | Faker |
| Dev Environment | VS Code, Git & GitHub |

## Project Structure

```
ghost-subscription-tracker/
├── config/              # Django project settings, URLs
├── transactions/        # Transaction model, CSV upload API
├── merchants/            # Merchant model (canonical entities)
├── subscriptions/          # Subscription model, price history, feedback API
├── insights/                # Dashboard views, authentication
├── ml_pipeline/               # Standalone ML/NLP logic (clean, cluster, recurrence, risk_score)
├── templates/                  # HTML pages (dashboard, login, signup)
├── static/                      # CSS and JavaScript
├── notebooks/                    # Jupyter prototyping notebooks
├── requirements.txt
└── manage.py
```

## How It Works (Architecture)

```
User uploads CSV
      ↓
Django REST API (transactions/views.py)
      ↓
ML Pipeline (ml_pipeline/)
  1. clean.py       → normalize merchant text
  2. cluster.py      → fuzzy-match similar merchants into groups
  3. recurrence.py    → detect recurring payment patterns
  4. risk_score.py     → generate explainable risk scores
      ↓
Saved to MySQL (Merchant, Transaction, Subscription, PriceHistory)
      ↓
Dashboard (templates/dashboard.html + static/js/app.js)
  - Subscription cards with risk badges
  - Price-history chart (Chart.js)
  - Savings simulator
  - Feedback buttons → feed back into future risk scoring
```

## Setup & Installation

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd ghost-subscription-tracker
   ```

2. **Create and activate a virtual environment (Python 3.12 recommended)**
   ```bash
   py -3.12 -m venv venv
   venv\Scripts\activate      # Windows
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up MySQL**
   - Create a database: `CREATE DATABASE ghost_subscription_tracker CHARACTER SET utf8mb4;`
   - Update `config/settings.py` → `DATABASES` with your MySQL username/password

5. **Run migrations**
   ```bash
   python manage.py migrate
   ```

6. **Create a superuser (for admin access)**
   ```bash
   python manage.py createsuperuser
   ```

7. **Run the server**
   ```bash
   python manage.py runserver
   ```

8. Visit `http://127.0.0.1:8000/` — sign up, log in, and upload a bank statement CSV to try it out.

## Generating Test Data

Since real bank statements aren't available for testing, a synthetic data generator (built with Faker, prototyped in `notebooks/`) creates realistic bank statement CSVs with known recurring merchants baked in — used to validate the ML pipeline's precision and recall against a verifiable ground truth.

## Evaluation Results

Tested against a synthetic dataset with 6 known recurring merchants:
- **Precision:** 100% (no false positives among 71 total clusters)
- **Recall:** ~83% (5 of 6 known subscriptions correctly detected; the one miss was an annual subscription with only 2 data points — a known limitation of gap-based detection for low-frequency merchants)

## Known Limitations

- Relies on a manually uploaded CSV — no live bank API integration yet
- Cannot verify actual usage of a subscription, only infers likelihood from payment patterns
- Annual/low-frequency subscriptions are harder to confidently detect with limited transaction history
- Merchant abbreviation handling (e.g. "AMZN" → "Amazon") currently relies on a small manually curated dictionary rather than a learned model

## Future Scope

- Direct bank API integration for automatic, real-time tracking
- Deep learning–based merchant name embeddings for smarter matching
- Mobile app with push notifications for price increases
- Multi-user/family account duplicate-subscription detection
- Crowdsourced, anonymized price benchmarking across users

## Team

- Shubh Shekhar Jha
- Anchal Paswan
- Karma

**Department of Information Technology**
Maharaja Surajmal Institute of Technology, Janakpuri, New Delhi
