from app import create_app
from app.models import db


app = create_app("ProductionConfig")


# Render starts this module with: gunicorn flask_app:app
with app.app_context():
    db.create_all()
