from django import template

register = template.Library()


@register.inclusion_tag('builtins/tag.html')
def tag(value, viewname=None):
    """
    Display a tag, optionally linked to a filtered list of objects.

    Args:
        value: A Tag instance
        viewname: If provided, the tag will be a hyperlink to the specified view's URL
    """
    return {
        'tag': value,
        'viewname': viewname,
    }


@register.inclusion_tag('builtins/badge.html')
def badge(value, bg_color=None, show_empty=False, font_size=None):
    """
    Display the specified number as a badge.

    Args:
        value: The value to be displayed within the badge
        bg_color: Background color CSS name
        show_empty: If true, display the badge even if value is None or zero
    """
    return {
        'value': value,
        'bg_color': bg_color or 'secondary',
        'show_empty': show_empty,
        'font_size': font_size
    }


@register.inclusion_tag('builtins/checkmark.html')
def checkmark(value, show_false=True, true='Yes', false='No'):
    """
    Display either a green checkmark or red X to indicate a boolean value.

    Args:
        value: True or False
        show_false: Show false values
        true: Text label for true values
        false: Text label for false values
    """
    return {
        'value': bool(value),
        'show_false': show_false,
        'true_label': true,
        'false_label': false,
    }
