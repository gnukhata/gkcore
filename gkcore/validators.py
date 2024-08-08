import colander
import json

def validate_json(node, value):
    try:
        # Attempt to parse the JSON string
        json.loads(value)
    except json.JSONDecodeError:
        raise colander.Invalid(node, "Invalid JSON format.")
