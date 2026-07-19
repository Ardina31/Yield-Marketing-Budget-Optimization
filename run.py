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


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=app.config.get("DEBUG", False))
