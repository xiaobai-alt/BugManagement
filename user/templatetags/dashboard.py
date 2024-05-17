from django.template import Library
from django.urls import reverse
from user import models

register = Library()


@register.simple_tag
def user_space(size):
    if not size:
        size = 0
    if int(size) >= 1024 * 1024 * 1024:
        return "%.2f GB" % (int(size) / (1024 * 1024 * 1024),)
    elif int(size) >= 1024 * 1024:
        return "%.2f MB" % (int(size) / (1024 * 1024),)
    elif int(size) >= 1024:
        return "%.2f KB" % (int(size) / 1024,)
    else:
        return "%d B" % int(size)