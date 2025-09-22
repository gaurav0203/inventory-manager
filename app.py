from flask import Flask
from extensions import db, login_manager
from routes import routes_bp
from models import User

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///db.sqlite"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = "supersecretkey"

db.init_app(app)
login_manager.init_app(app)

# where to redirect if unauthorized user tries to access @login_required route
login_manager.login_view = "routes.login"

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

app.register_blueprint(routes_bp)

with app.app_context():
    db.create_all()

if __name__ == "__main__":    
    app.run(debug = True)