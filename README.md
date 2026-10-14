# SkillSwap

SkillSwap is a Django platform where people publish skills they can teach and request lessons from other users.

## Features

- registration, login, logout, profiles, Cloudinary avatars;
- four access levels: guest, user, admin, and super admin;
- skill offers with Cloudinary images, categories, levels, formats, and duration;
- draft, pending, published, and rejected moderation states;
- lesson requests with controlled status transitions;
- one rating and review per completed lesson;
- favorites, mentors, popular offers, search, and combined filters;
- ownership checks, banned-user restrictions, and optimized related-object queries.

## Local setup

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py seed_categories
python manage.py createsuperuser
python manage.py runserver
```

Open <http://127.0.0.1:8000/>.

Add your Cloudinary credentials to `.env`. Never commit that file.

For an optional local demo, choose a password and enter it only in your terminal:

```bash
python manage.py create_demo_data --password "your-local-demo-password"
```

## Roles

- A super admin is created with `createsuperuser` and can assign or remove admin access on the Users page.
- An admin can moderate and edit offers, ban users, and delete reviews.
- A user can manage only their own offers, requests, favorites, and reviews.
- A guest can browse published offers and public profiles.

## Checks

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test
```

