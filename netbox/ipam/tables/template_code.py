
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

DEVICE_FROM_DISPLAY = """
{% for from in record.device_from.all %}
    {% if from %}
        {% badge from|linkify bg_color="blue" %}
    {% else %}
        None 
    {% endif %}
{% endfor %}
"""

DEVICE_TO_DISPLAY = """
{% for to in record.device_to.all %}
    {% if to %}
        {% badge to|linkify bg_color="blue" %}
    {% else %}
        None 
    {% endif %}
{% endfor %}
"""