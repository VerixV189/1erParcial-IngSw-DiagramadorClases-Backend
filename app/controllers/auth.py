from datetime import timedelta
from http import HTTPStatus

from flask import Blueprint, request, jsonify
from flask_bcrypt import Bcrypt
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required
from marshmallow import ValidationError

from app.errors.errors import GenericError
from app.models import BitacoraUsers, Users
from app.database import db
# El esquema que me pasaste ahora está en este archivo
from app.schemas.auth_schema_body import AuthLoginSchemaBody, AuthRegisterSchemaBody
from app.schemas.schemas import UsuarioSchema
from app.utils.enums.enums import Sesion

# Se inicializa una vez en tu archivo principal de la app
bcrypt = Bcrypt()
auth_bp = Blueprint('auth', __name__)

def obtener_ip():
    """Obtiene la dirección IP del cliente de forma segura."""
    return request.headers.get("X-Forwarded-For", request.remote_addr)

@auth_bp.route('/registrar', methods=['POST'])
def register():
    try:
        body = request.get_json()
        schema = AuthRegisterSchemaBody()
        
        # Marshmallow.load valida los datos y lanza ValidationError si hay un problema
        data = schema.load(body)
        
        usuario_existente = Users.query.filter_by(email=data["email"]).first()
        if usuario_existente: 
            raise GenericError(
                HTTPStatus.BAD_REQUEST,
                HTTPStatus.BAD_REQUEST.phrase,
                "Error... El usuario ya está registrado en el sistema."
            )
            
        nuevo_usuario = Users(
            name=data["nombre"],
            # El campo username se crea a partir del nombre, tal como estaba en tu código
            username=data["nombre"].strip().split()[0].capitalize(),
            email=data["email"],
            password=bcrypt.generate_password_hash(data["password"]).decode('utf-8'),
        )
        
        db.session.add(nuevo_usuario)

        bitacora_usuario = BitacoraUsers(
            ip=obtener_ip(),
            tipo_accion=Sesion.REGISTRO_DE_USUARIO._value_[0],
        )
        nuevo_usuario.bitacora_entries.append(bitacora_usuario)
        db.session.add(bitacora_usuario)
        
        db.session.commit()
        
        response = UsuarioSchema().dump(nuevo_usuario)
        return jsonify({"usuario": response}), HTTPStatus.CREATED
        
    except ValidationError as err:
        return jsonify({"errors": err.messages}), HTTPStatus.BAD_REQUEST
    except GenericError as e:
        db.session.rollback()
        raise e
    except Exception as e:
        db.session.rollback()
        raise GenericError(
            HTTPStatus.INTERNAL_SERVER_ERROR,
            HTTPStatus.INTERNAL_SERVER_ERROR.phrase,
            f"Error inesperado: {str(e)}"
        )

@auth_bp.route("/login", methods=["POST"])
def login():
    try:
        body = request.get_json()
        schema = AuthLoginSchemaBody()
        data = schema.load(body)
        
        usuario_db = Users.query.filter_by(email=data["email"]).first()

        if not usuario_db or not bcrypt.check_password_hash(usuario_db.password, data["password"]):
            raise GenericError(
                HTTPStatus.UNAUTHORIZED,
                HTTPStatus.UNAUTHORIZED.phrase,
                "Error... credenciales no válidas."
            )
        
        if usuario_db.is_deleted:
            raise GenericError(
                HTTPStatus.UNAUTHORIZED,
                HTTPStatus.UNAUTHORIZED.phrase,
                "Error... Usuario no autorizado."
            )
        
        token = create_access_token(identity=str(usuario_db.id), expires_delta=timedelta(hours=1)) 
        
        bitacora_usuario = BitacoraUsers(
            ip=obtener_ip(),
            # Referencia al ID del usuario en lugar del username
            user_id=usuario_db.id,
            tipo_accion=Sesion.LOGIN._value_[0],
        )
        db.session.add(bitacora_usuario)
        db.session.commit()
        
        return jsonify({
            "message": f"Bienvenido Usuario {usuario_db.username}",
            "access_token": token,
            "usuario": UsuarioSchema().dump(usuario_db)
        })
        
    except ValidationError as err:
        return jsonify({"errors": err.messages}), HTTPStatus.BAD_REQUEST
    except GenericError as e:
        db.session.rollback()
        raise e
    except Exception as e:
        db.session.rollback()
        raise GenericError(
            HTTPStatus.INTERNAL_SERVER_ERROR,
            HTTPStatus.INTERNAL_SERVER_ERROR.phrase,
            f"Error inesperado: {str(e)}"
        )

@auth_bp.route('/me', methods=["GET"])
@jwt_required()
def get_authenticated_user():
    try:
        id_usuario_autenticado = get_jwt_identity()
        usuario = Users.query.get(id_usuario_autenticado)
        
        if not usuario:
            return jsonify({"msg": "Usuario autenticado no encontrado en la base de datos."}), HTTPStatus.NOT_FOUND
        
        return UsuarioSchema().dump(usuario), HTTPStatus.OK
        # return jsonify({
        #     "usuario": UsuarioSchema().dump(usuario)
        # })
        
    except Exception as e:
        # Manejo de cualquier error inesperado de DB o serialización.
        db.session.rollback()
        print(f"FATAL Error en /api/auth/me: {e}") 
        
        # Devolver un 500 limpio.
        return jsonify({
            "msg": "Internal Server Error during user lookup",
            "error": "Failed to retrieve user data."
        }), HTTPStatus.INTERNAL_SERVER_ERROR

@auth_bp.route('/logout', methods=["POST"])
@jwt_required()
def logout():
    try:
        id_usuario_autenticado = get_jwt_identity()
        usuario = Users.query.get(id_usuario_autenticado)
        
        if not usuario:
            raise GenericError(
                HTTPStatus.UNAUTHORIZED,
                HTTPStatus.UNAUTHORIZED.phrase,
                "Error... usuario no autenticado."
            )
            
        bitacora_usuario = BitacoraUsers(
            ip=obtener_ip(),
            # Referencia al ID del usuario en lugar del username
            tipo_accion=Sesion.LOGOUT._value_[0],
        )
        usuario.bitacora_entries.append(bitacora_usuario)
        db.session.add(bitacora_usuario)
        db.session.commit()
        
        return jsonify({
            "message": "Sesión cerrada exitosamente."
        })
        
    except GenericError as e:
        db.session.rollback()
        raise e
    except Exception as e:
        db.session.rollback()
        raise GenericError(
            HTTPStatus.INTERNAL_SERVER_ERROR,
            HTTPStatus.INTERNAL_SERVER_ERROR.phrase,
            f"Error inesperado: {str(e)}"
        )