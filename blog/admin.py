from django.contrib import admin
from .models import Category, Post


class BlogAdmin(admin.ModelAdmin):
    # Відображення полів у списку постів
    list_display = ('title', 'youtube')
    list_filter = ('categories',)  # Фільтрація по категорії


admin.site.register(Category)
admin.site.register(Post, BlogAdmin)
