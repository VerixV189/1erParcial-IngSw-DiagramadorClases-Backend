from marshmallow import Schema, fields, validate

class ProjectCreateSchemaBody(Schema):
    """Esquema para la validación del cuerpo de la solicitud de creación de proyecto."""
    name = fields.Str(
        required=True, 
        validate=validate.Length(min=1, max=100),
        error_messages={"required": "El nombre del proyecto es obligatorio."}
    )
    description = fields.Str(
        required=False, 
        validate=validate.Length(max=500),
        allow_none=True
    )
