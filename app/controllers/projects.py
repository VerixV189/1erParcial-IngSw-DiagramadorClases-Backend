from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.database import db
from app.models import Project, Users, Relationship, Class # Asegúrate de que tu modelo se llame 'Projects'
from app.errors.errors import GenericError
from app.schemas.project_schema_body import ProjectCreateSchemaBody
from app.schemas.project_schema import ProjectSchema 
from sqlalchemy.orm import joinedload
from marshmallow import ValidationError
from http import HTTPStatus

projects_bp = Blueprint('projects_bp', __name__)

# Esquema para validación de entrada
project_create_schema = ProjectCreateSchemaBody()
# Esquema para serialización de salida
project_schema = ProjectSchema()

@projects_bp.route('/list', methods=['GET'])
@jwt_required()
def get_user_projects():
    """Endpoint para obtener los proyectos del usuario autenticado."""
    try:
        # Obtener la identidad del token (en este caso, el user_id)
        current_user_id = get_jwt_identity()

        # Usar el user_id para buscar al usuario y sus proyectos
        user = Users.query.filter_by(id=current_user_id).first()

        if not user:
            return jsonify({"message": "Usuario no encontrado"}), 404

        # Obtener los proyectos del usuario usando la relación del modelo
        # Esto filtra automáticamente los proyectos por el user_id
        projects = user.projects

        # Serializar los proyectos a un formato JSON
        projects_list = [
            {
                "id": str(project.id),
                "name": project.name,
                "created_at": project.created_at.isoformat(),
                "updated_at": project.updated_at.isoformat()
            }
            for project in projects
        ]

        return jsonify(projects_list), 200

    except Exception as err:
        raise GenericError(f"Error inesperado al obtener proyectos: {str(err)}")

@projects_bp.route('', methods=['POST'])
@jwt_required()
def create_project():
    """Endpoint para crear un nuevo proyecto para el usuario autenticado."""
    try:
        current_user_id = get_jwt_identity()
        
        # 1. Validar los datos de entrada
        schema = ProjectCreateSchemaBody()
        data = schema.load(request.json)
        
        # 2. Crear la instancia del proyecto
        new_project = Project(
            name=data['name'],
            description=data.get('description'), # La descripción es opcional
            user_id=current_user_id
        )
        
        # 3. Guardar en la base de datos
        db.session.add(new_project)
        db.session.commit()
        
        # 4. Devolver la información del proyecto creado
        return jsonify({
            "id": str(new_project.id),
            "name": new_project.name,
            "description": new_project.description,
            "user_id": str(new_project.user_id)
        }), HTTPStatus.CREATED # Retornar 201 Created

    except ValidationError as err:
        return jsonify({"errors": err.messages}), HTTPStatus.BAD_REQUEST
    except Exception as err:
        db.session.rollback()
        raise GenericError(
            HTTPStatus.INTERNAL_SERVER_ERROR,
            HTTPStatus.INTERNAL_SERVER_ERROR.phrase,
            f"Error al crear el proyecto: {str(err)}"
        )
    
@projects_bp.route('/<uuid:project_id>', methods=['GET'])
@jwt_required()
def get_project_data(project_id):
    """
    Endpoint para obtener los detalles de un proyecto específico, incluyendo clases y relaciones.
    """
    try:
        current_user_id = get_jwt_identity()
        
        # 1. Buscar el proyecto activo por ID con CARGA ANSIOSA (EAGER LOADING)
        # Esto asegura que project.classes y project.relationships estén llenos.
        project = Project.get_active().options(
            joinedload(Project.classes),
            joinedload(Project.relationships)
        ).filter_by(id=project_id).one_or_none()
        
        if not project:
            raise GenericError(
                HTTPStatus.NOT_FOUND,
                HTTPStatus.NOT_FOUND.phrase,
                "Proyecto no encontrado o eliminado."
            )

        # 2. Verificar la propiedad
        if str(project.user_id) != current_user_id:
            raise GenericError(
                HTTPStatus.FORBIDDEN,
                HTTPStatus.FORBIDDEN.phrase,
                "Acceso denegado. El proyecto no te pertenece."
            )
            
        # 3. Serializar y devolver
        # ProjectSchema ahora serializará las relaciones que están cargadas en 'project'
        project_data = ProjectSchema().dump(project)
        
        # Limpiar la sesión después de usarla
        db.session.remove() 

        return jsonify(project_data), HTTPStatus.OK

    except GenericError as e:
        db.session.rollback()
        db.session.remove() 
        return jsonify({"message": e.message}), e.status
    except Exception as err:
        db.session.rollback()
        db.session.remove() 
        print(f"Error inesperado en get_project_data: {err}")
        return jsonify({
            "message": "Error interno del servidor al cargar el proyecto."
        }), HTTPStatus.INTERNAL_SERVER_ERROR

@projects_bp.route('/<uuid:project_id>/save', methods=['POST'])
@jwt_required()
def save_project_data(project_id):
    """
    Guarda los datos del diagrama (classes y relationships) en las tablas relacionales.
    
    Esta función implementa la lógica de 'upsert' mediante un borrado y reinserción
    completa para simplificar la sincronización del diagrama (una estrategia común para 
    datos que se gestionan de forma monolítica en el frontend, como un diagrama).
    """
    updated_at_str = None
    
    try:
        current_user_id = get_jwt_identity()
        data = request.json
        
        # 1. Buscar el proyecto y verificar la propiedad
        project = Project.get_active().filter_by(id=project_id).one_or_none()

        if not project:
            raise GenericError(HTTPStatus.NOT_FOUND, HTTPStatus.NOT_FOUND.phrase, "Proyecto no encontrado o eliminado.")
            
        if str(project.user_id) != current_user_id:
            raise GenericError(HTTPStatus.FORBIDDEN, HTTPStatus.FORBIDDEN.phrase, "Acceso denegado. No tienes permiso para editar este proyecto.")

        # 2. Validación de datos de entrada
        if not (data and 'classes' in data and 'relationships' in data):
             raise GenericError(HTTPStatus.BAD_REQUEST, HTTPStatus.BAD_REQUEST.phrase, "El cuerpo de la solicitud debe contener las listas 'classes' y 'relationships'.")

        # --- LÓGICA DE SINCRONIZACIÓN RELACIONAL ---

        # 2a. Actualizar el campo JSON (opcional, pero buena práctica si se usa como caché/backup)
        project.diagram_data = data 
        db.session.add(project)
        
        # 2b. Eliminación de datos antiguos (Las relaciones se borran en cascada con las clases si se usa ORM)
        # SQLAlchemy gestionará los borrados en cascada definidos en el modelo (cascade="all, delete-orphan").
        # Borrando las colecciones de Python asociadas al objeto, SQLAlchemy sabe que debe eliminarlas de la DB.

        # Borrar relaciones existentes (ya que dependen de las clases)
        Relationship.query.filter_by(project_id=project.id).delete()
        # Borrar clases existentes
        Class.query.filter_by(project_id=project.id).delete()
        
        # 2c. Reinserción de las nuevas clases
        class_id_map = {} # Mapeo para manejar IDs temporales del frontend
        
        for class_data in data['classes']:
            # El ID del frontend se usará temporalmente como clave para mapear las relaciones
            temp_id = class_data.get('id')
            
            # Creamos un nuevo objeto Class (SQLAlchemy generará un nuevo ID UUID)
            new_class = Class(
                project_id=project.id,
                name=class_data.get('name', 'ClaseSinNombre'),
                stereotype=class_data.get('stereotype'),
                attributes=class_data.get('attributes', []),
                methods=class_data.get('methods', []),
                # Aseguramos que position es un dict, aunque JSON lo mapee por defecto
                position=class_data.get('position', {"x": 0, "y": 0}) 
            )
            db.session.add(new_class)
            # Guardamos el mapeo: ID Temporal del Frontend -> Objeto ORM (el ID de la DB se generará en el commit)
            class_id_map[str(temp_id)] = new_class

        # 2d. Reinserción de las nuevas relaciones
        
        # Es necesario forzar el flush para que los nuevos objetos Class tengan sus IDs de BD generados
        # antes de intentar usarlos para las claves foráneas de las relaciones.
        db.session.flush() 

        for rel_data in data['relationships']:
            # Usamos el mapeo para encontrar el objeto Class real (con su ID de BD)
            source_class_orm = class_id_map.get(str(rel_data.get('sourceClassId')))
            target_class_orm = class_id_map.get(str(rel_data.get('targetClassId')))

            if source_class_orm and target_class_orm:
                new_relationship = Relationship(
                    project_id=project.id,
                    source_class_id=source_class_orm.id, # Usamos el ID generado por la BD
                    target_class_id=target_class_orm.id, # Usamos el ID generado por la BD
                    relationship_type=rel_data.get('relationshipType'),
                    source_multiplicity=rel_data.get('sourceMultiplicity'),
                    target_multiplicity=rel_data.get('targetMultiplicity'),
                    label=rel_data.get('label')
                )
                db.session.add(new_relationship)
            else:
                 print(f"Advertencia: Relación ignorada debido a IDs de clase no encontrados: {rel_data}")


        # 3. Hacer COMMIT explícito de toda la transacción
        db.session.commit()
        
        # 4. Refresco y limpieza (Mantenemos el fix anterior para el 'updated_at')
        db.session.refresh(project)
        updated_at_str = project.updated_at.isoformat()
        db.session.remove()

        # 5. Respuesta exitosa
        return jsonify({
            "message": "Proyecto guardado y sincronizado exitosamente.", 
            "updatedAt": updated_at_str
        }), HTTPStatus.OK

    except GenericError as e:
        db.session.rollback()
        db.session.remove() 
        return jsonify({"message": e.message}), e.status
    except Exception as err:
        db.session.rollback()
        db.session.remove() 
        print(f"Error inesperado en save_project_data: {err}")
        return jsonify({
            "message": "Error interno del servidor al intentar guardar el proyecto."
        }), HTTPStatus.INTERNAL_SERVER_ERROR
    
# --- RUTA 5: ELIMINAR PROYECTO (DELETE /api/projects/{projectId}) ---
@projects_bp.route('/projects/<uuid:project_id>', methods=['DELETE'])
@jwt_required()
def delete_project(project_id):
    """
    Marca un proyecto como eliminado lógicamente.
    """
    try:
        current_user_id = get_jwt_identity()
        
        # 1. Buscar el proyecto activo por ID
        project = Project.get_active().filter_by(id=project_id).one_or_none()

        if not project:
            return jsonify({"message": "Proyecto no encontrado o ya eliminado."}), HTTPStatus.NOT_FOUND

        # 2. Verificar la propiedad
        if str(project.user_id) != current_user_id:
            return jsonify({"message": "Acceso denegado."}), HTTPStatus.FORBIDDEN
            
        # 3. Eliminar lógicamente
        project.soft_delete()
        db.session.commit()
        
        return jsonify({"message": f"Proyecto '{project.name}' eliminado lógicamente."}), HTTPStatus.NO_CONTENT

    except Exception as err:
        db.session.rollback()
        print(f"Error inesperado al eliminar proyecto: {err}")
        return jsonify({
            "message": "Error interno del servidor al intentar eliminar el proyecto."
        }), HTTPStatus.INTERNAL_SERVER_ERROR