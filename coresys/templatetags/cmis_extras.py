from django import template
from django.urls import reverse

register = template.Library()


@register.simple_tag
def qs_replace(request, **kwargs):
    """Build a querystring from the current request's GET params with overrides."""
    params = request.GET.copy()
    for k, v in kwargs.items():
        params[k] = v
    return params.urlencode()


@register.inclusion_tag("partials/tags/kpi.html")
def kpi(label, value, accent="brand"):
    return {"label": label, "value": value, "accent": accent}


@register.inclusion_tag("partials/tags/pagination.html", takes_context=True)
def pagination(context, page_obj, url_name):
    return {
        "page_obj": page_obj,
        "url_name": url_name,
        "request": context["request"],
    }


@register.inclusion_tag("partials/tags/field.html")
def field(label, name, type="text", value="", required=False, placeholder=""):
    return {"label": label, "name": name, "type": type, "value": value or "",
            "required": required, "placeholder": placeholder}


@register.inclusion_tag("partials/tags/select.html")
def select(label, name, options, selected="", required=False, blank_label=None):
    return {"label": label, "name": name, "options": options, "selected": selected,
            "required": required, "blank_label": blank_label}


@register.inclusion_tag("partials/tags/textarea.html")
def textarea(label, name, value="", rows=3, required=False):
    return {"label": label, "name": name, "value": value or "", "rows": rows, "required": required}


@register.inclusion_tag("partials/tags/password_field.html")
def password_field(label, name, required=False, autocomplete="current-password", minlength=None):
    return {"label": label, "name": name, "required": required,
            "autocomplete": autocomplete, "minlength": minlength}


@register.inclusion_tag("partials/tags/badge.html")
def badge(text, color="brand"):
    return {"text": text, "color": color}


@register.filter
def parse_pairs(spec):
    """Turn 'val:Label,val2:Label2' into [('val','Label'), ('val2','Label2')] for inline select options."""
    pairs = []
    for chunk in spec.split(","):
        if ":" in chunk:
            v, l = chunk.split(":", 1)
            pairs.append((v, l))
    return pairs


@register.filter
def role_in(role, roles_csv):
    if not role:
        return False
    return role in [r.strip() for r in roles_csv.split(",")]


@register.filter
def get_item(d, key):
    try:
        return d.get(key)
    except AttributeError:
        try:
            return d[key]
        except Exception:
            return None
