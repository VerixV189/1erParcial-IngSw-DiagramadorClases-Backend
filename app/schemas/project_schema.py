from marshmallow import Schema, fields
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from app.database import db
from app.models import Project, Class, Relationship


# --- ESQUEMAS PARA COMPONENTES UML ---

# Esquema para atributos
class UMLAttributeSchema(Schema):
    name = fields.Str()
    type = fields.Str()
    visibility = fields.Str()
    # Serializa 'is_static' (base de datos) a 'isStatic' (frontend)
    isStatic = fields.Bool(data_key="isStatic") 

# Esquema para métodos
class UMLMethodSchema(Schema):
    name = fields.Str()
    # Serializa 'return_type' (base de datos) a 'returnType' (frontend)
    returnType = fields.Str(data_key="returnType")
    # Los parámetros deben coincidir con la estructura UMLParameter si la tuvieras definida, aquí usamos Dict
    parameters = fields.List(fields.Dict()) 
    visibility = fields.Str()
    isStatic = fields.Bool(data_key="isStatic")
    isAbstract = fields.Bool(data_key="isAbstract")

# Esquema para las Clases
class UMLClassSchema(Schema):
    """Serializa el modelo Class a la interfaz UMLClass del frontend."""
    id = fields.UUID(dump_only=True)
    # Serializa 'project_id' a 'projectId'
    projectId = fields.UUID(dump_only=True, data_key="projectId")
    name = fields.Str()
    stereotype = fields.Str(allow_none=True)
    attributes = fields.List(fields.Nested(UMLAttributeSchema)) 
    methods = fields.List(fields.Nested(UMLMethodSchema))
    # 'position' es un JSON en el modelo y un Dict en Marshmallow
    position = fields.Dict() 


# Esquema para las Relaciones
class UMLRelationshipSchema(Schema):
    """Serializa el modelo Relationship a la interfaz UMLRelationship del frontend."""
    id = fields.UUID(dump_only=True)
    # Serializa 'source_class_id' a 'sourceClassId'
    sourceClassId = fields.UUID(data_key="sourceClassId")
    # Serializa 'target_class_id' a 'targetClassId'
    targetClassId = fields.UUID(data_key="targetClassId")
    # Serializa 'relationship_type' a 'relationshipType'
    relationshipType = fields.Str(data_key="relationshipType")
    # Serializa 'source_multiplicity' a 'sourceMultiplicity'
    sourceMultiplicity = fields.Str(data_key="sourceMultiplicity", allow_none=True)
    # Serializa 'target_multiplicity' a 'targetMultiplicity'
    targetMultiplicity = fields.Str(data_key="targetMultiplicity", allow_none=True)
    label = fields.Str(allow_none=True)

class ClassSchema(SQLAlchemyAutoSchema):
    """Serializa/Deserializa el modelo Class."""
    class Meta:
        model = Class
        sqla_session = db.session
        # Campos que queremos incluir. 'id' es UUID, los demás son estándares.
        include_fk = True
        load_instance = True
        
    # El ID es el identificador principal para el frontend
    id = fields.UUID(attribute="id", dump_only=True)

    createdAt = fields.DateTime(attribute="created_at", dump_only=True)
    updatedAt = fields.DateTime(attribute="updated_at", dump_only=True)


class RelationshipSchema(SQLAlchemyAutoSchema):
    """Serializa/Deserializa el modelo Relationship."""
    class Meta:
        model = Relationship
        sqla_session = db.session
        # Incluir las FKs para saber qué nodos conecta
        include_fk = True
        load_instance = True

    # El ID es el identificador principal para el frontend
    id = fields.UUID(attribute="id", dump_only=True)
    
    # Aseguramos que los IDs de origen y destino se serialicen como string/UUID
    # CRÍTICO: Conversión de snake_case a camelCase para coincidir con UMLRelationship
    sourceClassId = fields.UUID(attribute="source_class_id")
    targetClassId = fields.UUID(attribute="target_class_id")
    
    # 'relationship_type', 'label', 'source_multiplicity', 'target_multiplicity'
    # son lo suficientemente parecidos para que SQLAlchemyAutoSchema los maneje bien
    # si se llaman así en el modelo. Si necesitas camelCase:
    # relationshipType = fields.Str(attribute="relationship_type")
    
    createdAt = fields.DateTime(attribute="created_at", dump_only=True)
    updatedAt = fields.DateTime(attribute="updated_at", dump_only=True)


# --- ESQUEMA PRINCIPAL DE PROYECTO ---

class ProjectSchema(SQLAlchemyAutoSchema):
    """Serializa/Deserializa el modelo Project, incluyendo sus colecciones anidadas."""
    class Meta:
        model = Project
        sqla_session = db.session
        load_instance = True
        
    # Conversión de snake_case a camelCase para el proyecto
    updatedAt = fields.DateTime(attribute="updated_at", dump_only=True)
    createdAt = fields.DateTime(attribute="created_at", dump_only=True)
    
    # Anidación usando los esquemas corregidos
    classes = fields.List(
        fields.Nested(ClassSchema), 
        required=False, 
        dump_default=[]
    )
    
    relationships = fields.List(
        fields.Nested(RelationshipSchema), 
        required=False,
        dump_default=[]
    )
    
    # ... otros campos ...
    id = fields.UUID(attribute="id", dump_only=True)
    user_id = fields.UUID(attribute="user_id", dump_only=True)

# Clase de error para usar en los endpoints
class GenericError(Exception):
    def __init__(self, status, phrase, message):
        self.status = status
        self.phrase = phrase
        self.message = message