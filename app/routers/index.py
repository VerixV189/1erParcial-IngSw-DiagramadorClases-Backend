from flask import Blueprint
from app.controllers.auth import auth_bp
from app.controllers.projects import projects_bp
from app.controllers.classes import classes_bp
from app.controllers.relationships import relationships_bp

api_bp = Blueprint('api', __name__)

api_bp.register_blueprint(auth_bp, url_prefix='/auth')
api_bp.register_blueprint(projects_bp, url_prefix='/projects')
api_bp.register_blueprint(classes_bp, url_prefix='/classes')
api_bp.register_blueprint(relationships_bp, url_prefix='/relationships')