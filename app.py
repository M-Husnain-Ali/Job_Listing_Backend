from flask import Flask
from flask_cors import CORS
from database import db, init_db
from routes import api_bp
import os

def create_app():
    app = Flask(__name__)
    
    CORS(app)
    
    basedir = os.path.abspath(os.path.dirname(__file__))
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(basedir, "jobs.db")}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db.init_app(app)
    
    app.register_blueprint(api_bp, url_prefix='/api')
    
    return app

if __name__ == '__main__':
    app = create_app()
    
    with app.app_context():
        init_db()
    
    app.run(debug=True, port=5000)