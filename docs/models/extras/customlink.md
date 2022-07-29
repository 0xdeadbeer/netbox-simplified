# Custom Links

Custom links allow users to display arbitrary hyperlinks to external content within NetBox object views. These are helpful for cross-referencing related records in systems outside NetBox. For example, you might create a custom link on the device view which links to the current device in a Network Monitoring System (NMS).

Custom links are created by navigating to Customization > Custom Links. Each link is associated with a particular NetBox object type (site, device, prefix, etc.) and will be displayed on relevant views. Each link has display text and a URL, and data from the NetBox item being viewed can be included in the link using [Jinja2 template code](https://jinja2docs.readthedocs.io/en/stable/) through the variable `obj`, and custom fields through `obj.cf`.

For example, you might define a link like this:

* Text: `View NMS`
* URL: `https://nms.example.com/nodes/?name={{ obj.name }}`

When viewing a device named Router4, this link would render as:

```no-highlight
<a href="https://nms.example.com/nodes/?name=Router4">View NMS</a>
```

Custom links appear as buttons in the top right corner of the page. Numeric weighting can be used to influence the ordering of links, and each link can be enabled or disabled individually.

!!! warning
    Custom links rely on user-created code to generate arbitrary HTML output, which may be dangerous. Only grant permission to create or modify custom links to trusted users.

## Context Data

The following context data is available within the template when rendering a custom link's text or URL.

| Variable  | Description                                                                                                       |
|-----------|-------------------------------------------------------------------------------------------------------------------|
| `object`  | The NetBox object being displayed                                                                                 |
| `obj`     | Same as `object`; maintained for backward compatability until NetBox v3.5                                         |
| `debug`   | A boolean indicating whether debugging is enabled                                                                 |
| `request` | The current WSGI request                                                                                          |
| `user`    | The current user (if authenticated)                                                                               |
| `perms`   | The [permissions](https://docs.djangoproject.com/en/stable/topics/auth/default/#permissions) assigned to the user |

While most of the context variables listed above will have consistent attributes, the object will be an instance of the specific object being viewed when the link is rendered. Different models have different fields and properties, so you may need to some research to determine the attributes available for use within your template for a specific object type.

Checking the REST API representation of an object is generally a convenient way to determine what attributes are available. You can also reference the NetBox source code directly for a comprehensive list.

## Conditional Rendering

Only links which render with non-empty text are included on the page. You can employ conditional Jinja2 logic to control the conditions under which a link gets rendered.

For example, if you only want to display a link for active devices, you could set the link text to

```jinja2
{% if obj.status == 'active' %}View NMS{% endif %}
```

The link will not appear when viewing a device with any status other than "active."

As another example, if you wanted to show only devices belonging to a certain manufacturer, you could do something like this:

```jinja2
{% if obj.device_type.manufacturer.name == 'Cisco' %}View NMS{% endif %}
```

The link will only appear when viewing a device with a manufacturer name of "Cisco."

## Link Groups

Group names can be specified to organize links into groups. Links with the same group name will render as a dropdown menu beneath a single button bearing the name of the group.

## Table Columns

Custom links can also be included in object tables by selecting the desired links from the table configuration form. When displayed, each link will render as a hyperlink for its corresponding object. When exported (e.g. as CSV data), each link render only its URL.
