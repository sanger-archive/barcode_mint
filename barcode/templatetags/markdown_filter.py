from django import template
import markdown

__author__ = 'rf9'

register = template.Library()


@register.filter
def markdownify(text):
    return markdown.markdown(text, safe_mode="escape")
