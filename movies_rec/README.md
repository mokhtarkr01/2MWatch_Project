# 🎬 CineMatch — Movie Recommendation App

A full-featured Django movie recommendation app powered by **Collaborative Filtering** (User-Based CF + Item-Based CF fallback).

---

## ✨ Features

| Feature | Details |
|---|---|
| 🤝 User-Based CF | Pearson Correlation to find taste-alike users |
| 🎞️ Item-Based CF | Cosine Similarity fallback for sparse data |
| ⭐ Star Rating | AJAX live 1–5 star ratings per movie |
| 📌 Watchlist | Save movies to watch later |
| 🔍 Browse & Filter | Search by title/director, filter by genre, sort |
| 👤 User Profiles | Rating history + distribution chart |
| 🌱 Seed Data | 50 real movies + simulated user ratings |

---

## 🚀 Quick Start

```bash
# 1. Clone / unzip the project
cd movie_recommender

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run migrations
python manage.py migrate

# 5. Create superuser
python manage.py createsuperuser
# Username: admin  Password: admin123

# 6. Seed database (50 movies + 8 users + ~200 ratings)
python manage.py seed_data

# 7. Run server
python manage.py runserver
```

Open http://127.0.0.1:8000 — **done!**

---

## 👤 Sample Accounts

After running `seed_data`:

| Username | Password |
|---|---|
| alice | password123 |
| bob | password123 |
| carol | password123 |
| dave | password123 |
| eve | password123 |
| frank | password123 |
| grace | password123 |
| henry | password123 |

---

## 🧠 How the Recommendation Engine Works

### Architecture: `movies/recommender.py`

```
User rates movies
       ↓
Engine builds User-Movie Rating Matrix
       ↓
  ┌─────────────────────────────────┐
  │   User-Based CF (Primary)       │
  │                                 │
  │  1. Pearson Correlation between │
  │     target user & all others    │
  │                                 │
  │  2. Find Top-N similar users    │
  │                                 │
  │  3. Weighted avg of their       │
  │     ratings on unseen movies    │
  └──────────────┬──────────────────┘
                 │  No similar users found?
                 ↓
  ┌─────────────────────────────────┐
  │   Item-Based CF (Fallback)      │
  │                                 │
  │  1. Cosine Similarity between   │
  │     movies (via shared ratings) │
  │                                 │
  │  2. Score candidates based on   │
  │     user's existing ratings     │
  └──────────────┬──────────────────┘
                 │  No ratings at all?
                 ↓
         Cold Start: Top-Rated Movies
```

### Pearson Correlation Formula

For users A and B with shared rated movies S:

```
        Σ(rA·rB) - (ΣrA · ΣrB / |S|)
r = ─────────────────────────────────────────────
    √[(ΣrA² - (ΣrA)²/|S|) · (ΣrB² - (ΣrB)²/|S|)]
```

- Score range: -1 (opposite taste) to +1 (identical taste)
- Only users with r > 0 (positive correlation) are used
- Requires at least 2 shared movies

### Cosine Similarity (Item-Based)

```
         A · B
sim = ─────────────
       ‖A‖ · ‖B‖
```

Where A and B are rating vectors of two movies across shared users.

---

## 📁 Project Structure

```
movie_recommender/
├── manage.py
├── settings.py              # Django config
├── urls.py                  # Root URL config
├── requirements.txt
│
├── movies/
│   ├── models.py            # Movie, Rating, Watchlist, Genre
│   ├── views.py             # All page + AJAX views
│   ├── urls.py              # App URL patterns
│   ├── admin.py             # Admin registration
│   ├── recommender.py       # ★ CF Engine (Pearson + Cosine)
│   ├── templatetags/
│   │   └── movie_tags.py    # Custom |get_item filter
│   └── management/
│       └── commands/
│           └── seed_data.py # 50 movies + simulated ratings
│
└── templates/
    └── movies/
        ├── base.html        # Nav, global styles, JS
        ├── home.html        # Recommendations + onboarding
        ├── movie_list.html  # Browse with search/filter
        ├── movie_detail.html# Detail + similar movies
        ├── watchlist.html   # Saved movies
        ├── profile.html     # Rating history + distribution
        ├── login.html
        └── register.html
```

---

## 🔌 Key URLs

| URL | View | Description |
|---|---|---|
| `/` | `home` | Personalized recommendations |
| `/movies/` | `movie_list` | Browse all movies |
| `/movies/<id>/` | `movie_detail` | Detail + similar movies |
| `/movies/<id>/rate/` | `rate_movie` | AJAX POST: rate movie |
| `/movies/<id>/watchlist/` | `toggle_watchlist` | AJAX POST: toggle |
| `/watchlist/` | `watchlist` | User's watchlist |
| `/profile/` | `profile` | Rating history |
| `/register/` | `register` | Create account |
| `/login/` | Login | Sign in |
| `/admin/` | Admin | Django admin panel |

---

## 🎨 Tech Stack

- **Backend:** Django 4.2, SQLite
- **Recommendation:** Pure Python CF (no ML libraries needed)
- **Frontend:** Vanilla HTML/CSS/JS — dark cinema theme
- **Fonts:** Playfair Display + DM Sans (Google Fonts)
- **AJAX:** Fetch API for live ratings & watchlist
