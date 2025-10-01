from marshmallow import fields, validate, Schema
from marshmallow import ValidationError, fields
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from app.database import db
from app.utils.enums.enums import Estado, Sesion

class AuthRegisterSchemaBody(Schema):
    nombre = fields.Str(required=True)
    email = fields.Email(required=True)
    password = fields.Str(required=True, validate=validate.Length(min=8))

class AuthLoginSchemaBody(Schema):
    email = fields.Email(required=True)
    password = fields.Str(required=True)

class UsuarioSchema(Schema):
    id = fields.UUID(dump_only=True)
    nombre = fields.Str(required=True)
    username = fields.Str(required=True)
    email = fields.Email(required=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)
    is_deleted = fields.Bool(dump_only=True)

class ProjectSchema(Schema):
    id = fields.UUID(dump_only=True)
    name = fields.Str(required=True, validate=validate.Length(min=1))
    description = fields.Str(required=False, allow_none=True)
    user_id = fields.UUID(required=True)
    diagram_data = fields.Dict(required=False, allow_none=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)

class ClassSchema(Schema):
    id = fields.UUID(dump_only=True)
    project_id = fields.UUID(required=True)
    name = fields.Str(required=True, validate=validate.Length(min=1))
    stereotype = fields.Str(required=False, allow_none=True)
    attributes = fields.List(fields.Dict(), required=False, allow_none=True)
    methods = fields.List(fields.Dict(), required=False, allow_none=True)
    position = fields.Dict(required=False, allow_none=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)

class RelationshipSchema(Schema):
    id = fields.UUID(dump_only=True)
    project_id = fields.UUID(required=True)
    source_class_id = fields.UUID(required=True)
    target_class_id = fields.UUID(required=True)
    relationship_type = fields.Str(required=True)
    source_multiplicity = fields.Str(required=False, allow_none=True)
    target_multiplicity = fields.Str(required=False, allow_none=True)
    label = fields.Str(required=False, allow_none=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)
