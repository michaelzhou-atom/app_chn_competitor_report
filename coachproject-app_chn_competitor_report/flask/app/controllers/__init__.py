from .main import main
from .auth import auth


def register_blueprints(app):
    app.register_blueprint(main)
    app.register_blueprint(auth)
