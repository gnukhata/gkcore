import colander

class LogSchema(colander.MappingSchema):
    activity = colander.SchemaNode(colander.String(), validator=colander.Length(max=500))
