# Export Templates

NetBox allows users to define custom templates that can be used when exporting objects. To create an export template, navigate to Customization > Export Templates.

Each export template is associated with a certain type of object. For instance, if you create an export template for VLANs, your custom template will appear under the "Export" button on the VLANs list. Each export template must have a name, and may optionally designate a specific export [MIME type](https://developer.mozilla.org/en-US/docs/Web/HTTP/Basics_of_HTTP/MIME_types) and/or file extension.

Export templates must be written in [Jinja2](https://jinja.palletsprojects.com/).

!!! note
    The name `table` is reserved for internal use.

!!! warning
    Export templates are rendered using user-submitted code, which may pose security risks under certain conditions. Only grant permission to create or modify export templates to trusted users.

The list of objects returned from the database when rendering an export template is stored in the `queryset` variable, which you'll typically want to iterate through using a `for` loop. Object properties can be access by name. For example:

```jinja2
{% for rack in queryset %}
Rack: {{ rack.name }}
Site: {{ rack.site.name }}
Height: {{ rack.u_height }}U
{% endfor %}
```

To access custom fields of an object within a template, use the `cf` attribute. For example, `{{ obj.cf.color }}` will return the value (if any) for a custom field named `color` on `obj`.

If you need to use the config context data in an export template, you'll should use the function `get_config_context` to get all the config context data. For example:
```
{% for server in queryset %}
{% set data = server.get_config_context() %}
{{ data.syslog }}
{% endfor %}
```

The `as_attachment` attribute of an export template controls its behavior when rendered. If true, the rendered content will be returned to the user as a downloadable file. If false, it will be displayed within the browser. (This may be handy e.g. for generating HTML content.)

A MIME type and file extension can optionally be defined for each export template. The default MIME type is `text/plain`.
