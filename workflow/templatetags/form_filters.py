from django import template

register = template.Library()


@register.filter(name='add_class')
def add_class(field, css_class):
    """Add CSS class(es) to a form field's widget, merging with existing classes."""
    existing = field.field.widget.attrs.get('class', '')
    merged = f"{existing} {css_class}".strip()
    return field.as_widget(attrs={'class': merged})
