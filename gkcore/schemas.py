import colander
from gkcore.validators import validate_json


class JSONField(colander.SchemaNode):
    """SchemaNode for JSON. This SchemaNode will be based on string schema type with
    `validate_json` validator
    """
    schema_type = colander.String
    validator = validate_json
    title = "JSON Field"
    description = "This field accepts a JSON string."
