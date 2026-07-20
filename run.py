"""
Development entrypoint.

    $ python run.py

For production, use a WSGI server instead, e.g.:

    $ gunicorn "run:app"
"""
import os

from app import create_app
from app.extensions import db
from app.models.channel import DEFAULT_CHANNELS, Channel
from seed import seed

app = create_app(os.environ.get("FLASK_ENV", "development"))


def _ensure_schema_and_channels():
    with app.app_context():
        db.create_all()
        if Channel.query.count() == 0:
            for c in DEFAULT_CHANNELS:
                db.session.add(Channel(**c))
            db.session.commit()
            app.logger.info("Seeded default marketing channels.")


_ensure_schema_and_channels()

# Auto-seed the demo admin account (admin@yield.app) on every boot. This is
# idempotent - seed() checks whether the account/data already exist and
# skips silently if so, so it's safe to run on every deploy/restart. This
# means the demo account works out of the box on hosts (like Render's free
# tier) that don't provide shell access to run `python seed.py` manually.
try:
    seed(app)
except Exception as exc:  # never let a seeding hiccup crash the whole app
    app.logger.warning("Demo data auto-seed skipped: %s", exc)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=app.config.get("DEBUG", False))
