from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.database import db
from app.models import Project, Relationship # Necesitamos Project para verificar la propiedad
from app.schemas.project_schema import UMLRelationshipSchema 
from app.errors.errors import GenericError
from http import HTTPStatus
import uuid

relationships_bp = Blueprint('relationships_bp', __name__)

@relationships_bp.route('/', methods=['GET'])
@jwt_required()
def get_relationships_by_project():
    """
    Endpoint para obtener todas las relaciones de un proyecto específico.
    Requiere el query param 'projectId'. Verifica la propiedad del proyecto.
    """
    try:
        current_user_id = get_jwt_identity()
        project_id_str = request.args.get('projectId')
        
        if not project_id_str:
            return jsonify({"message": "Parámetro 'projectId' requerido"}), HTTPStatus.BAD_REQUEST

        try:
            project_id = uuid.UUID(project_id_str)
        except ValueError:
            return jsonify({"message": "ID de proyecto inválido"}), HTTPStatus.BAD_REQUEST

        # 1. Verificar la existencia y propiedad del proyecto
        project = Project.get_active().filter_by(id=project_id).one_or_none()

        if not project:
            raise GenericError(
                HTTPStatus.NOT_FOUND,
                HTTPStatus.NOT_FOUND.phrase,
                "Proyecto no encontrado."
            )

        if str(project.user_id) != current_user_id:
            raise GenericError(
                HTTPStatus.FORBIDDEN,
                HTTPStatus.FORBIDDEN.phrase,
                "Acceso denegado. El proyecto no te pertenece."
            )
            
        # 2. Obtener todas las relaciones del proyecto
        relationships = Relationship.query.filter_by(project_id=project_id).all()
        
        # 3. Serializar y devolver
        relationships_data = UMLRelationshipSchema(many=True).dump(relationships)
        
        return jsonify(relationships_data), HTTPStatus.OK

    except GenericError as e:
        return jsonify({"message": e.message}), e.status
    except Exception as err:
        print(f"Error en get_relationships_by_project: {err}")
        raise GenericError(
            HTTPStatus.INTERNAL_SERVER_ERROR,
            HTTPStatus.INTERNAL_SERVER_ERROR.phrase,
            f"Error inesperado al obtener relaciones: {str(err)}"
        )