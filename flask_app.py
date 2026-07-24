from app import create_app
from app.models import db


app = create_app("ProductionConfig")


# Render starts this module with: gunicorn flask_app:app
with app.app_context():
    db.create_all()

# Note: we change the name of this file from app.py to flask_app.py so that when gunicorn tries to run app:app (looking for the app object in the app file) it doesn't get confused by the fact that we have an app object in an app file in an app folder.  And since we're relying on gunicorn to run our app, we no longer need to say app.run()