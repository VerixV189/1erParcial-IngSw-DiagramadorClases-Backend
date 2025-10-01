import os
from flask import Flask, jsonify # Añadida 'jsonify' para los manejadores de error
from app.database import init_db
from app.config.config import Config
from app.controllers.auth import bcrypt
from dotenv import load_dotenv
from app.routers.index import api_bp
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from http import HTTPStatus # Necesario para usar códigos de estado en los manejadores

load_dotenv()
jwt = JWTManager()

def create_app():
    app = Flask(__name__)
    
    # Carga la configuración directamente desde la clase Config
    app.config.from_object(Config)
    
    # Inicializa las extensiones
    init_db(app)
    bcrypt.init_app(app)
    jwt.init_app(app)
    
    # --- MANEJADORES DE ERRORES DE JWT ---
    # Esto asegura que los errores 401 de JWT (token faltante, inválido o expirado)
    # devuelvan JSON en lugar de HTML, evitando el SyntaxError del frontend.

    @jwt.unauthorized_loader
    def unauthorized_callback(callback):
        return jsonify({
            "message": "Token de acceso faltante en la solicitud.",
            "error": "unauthorized"
        }), HTTPStatus.UNAUTHORIZED # 401

    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return jsonify({
            "message": f"Token inválido: {error}",
            "error": "invalid_token"
        }), HTTPStatus.UNAUTHORIZED # 401

    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return jsonify({
            "message": "El token ha expirado.",
            "error": "token_expired"
        }), HTTPStatus.UNAUTHORIZED # 401
    
    # --- FIN MANEJADORES DE ERRORES DE JWT ---
    
    # --- MANEJADOR DE ERRORES GENÉRICO (500) ---
    # Captura cualquier error 500 no manejado por otras funciones.
    @app.errorhandler(HTTPStatus.INTERNAL_SERVER_ERROR) # 500
    def handle_internal_server_error(e):
        print(f"Error 500 no manejado: {e}")
        return jsonify({
            "message": "Error interno del servidor no manejado. Por favor, revisa los logs del backend.",
            "error_detail": str(e)
        }), HTTPStatus.INTERNAL_SERVER_ERROR
    # --- FIN MANEJADOR DE ERRORES GENÉRICO ---

    CORS(app, resources={
        r"/api/*": {
            "origins": ["http://localhost:3000", "https://primerparcialingsw.netlify.app/","https://primerparcialingsw.netlify.app/", ""],
            # "origins": ["*"],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"],
            "supports_credentials": True 
        }
    })

    app.register_blueprint(api_bp, url_prefix="/api")

    from . import models
    return app