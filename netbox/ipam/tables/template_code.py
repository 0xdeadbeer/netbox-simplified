
PROTOCOL_TABLE_TEMPLATE = """
    {% if record.protocol %}
        {% badge record.protocol bg_color="red" %}
    {% else %}
        None
    {% endif %}
"""

PORT_TABLE_TEMPLATE = """
    {% if record.port %}
        {% badge record.port bg_color="orange" %}
    {% else %}
        None
    {% endif %}
"""