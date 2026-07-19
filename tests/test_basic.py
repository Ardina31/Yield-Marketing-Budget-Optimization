import pytest

from app import create_app
from app.extensions import db
from app.models import User
from app.models.channel import DEFAULT_CHANNELS, Channel


@pytest.fixture
def app():
    app = create_app("testing")
    with app.app_context():
        db.create_all()
        for c in DEFAULT_CHANNELS:
            db.session.add(Channel(**c))
        db.session.commit()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


def test_login_page_loads(client):
    resp = client.get("/auth/login")
    assert resp.status_code == 200
    assert b"Sign in" in resp.data or b"Welcome back" in resp.data


def test_dashboard_requires_login(client):
    resp = client.get("/dashboard", follow_redirects=False)
    assert resp.status_code in (302, 401)


def test_register_and_login_flow(app, client):
    resp = client.post(
        "/auth/register",
        data={
            "name": "Test User",
            "email": "test@example.com",
            "password": "password123",
            "confirm_password": "password123",
            "role": "admin",
            "company_name": "",
        },
        follow_redirects=True,
    )
    assert resp.status_code == 200

    with app.app_context():
        assert User.query.filter_by(email="test@example.com").first() is not None
