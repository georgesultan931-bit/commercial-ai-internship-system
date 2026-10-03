STEP 1 - SECURITY CLEANUP

Replace these backend files:
- config/settings.py
- accounts/views.py
- .env.example
- render.yaml
- .gitignore

IMPORTANT BEFORE STARTING:
1. Keep your real backend/.env private. Do NOT replace it with .env.example.
2. Because a Brevo key was present in the old .env.example/archive, rotate that key in Brevo and update only backend/.env and your production environment variables.
3. Ensure backend/.env contains DJANGO_SECRET_KEY. Generate one with:
   python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
4. Do not upload backend/.env, db.sqlite3, venv/, node_modules/, or media/ in future source ZIPs.

VERIFY:
python manage.py check
python manage.py check --deploy
python manage.py runserver

NOTE:
check --deploy may warn while DJANGO_DEBUG=True locally. That is expected; the production host must use DJANGO_DEBUG=False.

CLEANUP AFTER VERIFYING THE APP:
- Delete the accidental template:
  templates/accounts/Rename-Item templates/accounts/password_reset_form.html password_reset.html.html
- Do not delete your working local venv until you have confirmed requirements.txt can rebuild it.
- Do not delete db.sqlite3 if it contains local data you still need.
