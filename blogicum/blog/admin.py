from django.contrib import admin

from .models import Category, Comment, Location, Post

admin.site.empty_value_display = 'Поле не задано'

admin.site.register(Post)
admin.site.register(Category)
admin.site.register(Location)
admin.site.register(Comment)
