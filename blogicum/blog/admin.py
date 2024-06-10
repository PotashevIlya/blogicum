from django.contrib import admin

from .models import Category, Location, Post

admin.site.empty_value_display = 'Поле не задано'

admin.site.register(Post)
admin.site.register(Category)
admin.site.register(Location)
