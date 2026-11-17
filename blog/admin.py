from django.contrib import admin
from django.utils.html import format_html

from .forms import PostImageForm, PostImageFormSet
from .models import Category, Post, PostImage


class PostImageInline(admin.TabularInline):
    model = PostImage
    form = PostImageForm
    formset = PostImageFormSet
    fields = ('preview', 'image', 'is_main')
    readonly_fields = ('preview',)
    extra = 1

    @admin.display(description='Прев’ю')
    def preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="max-width:160px;max-height:100px" alt="">', obj.image.url)
        return '—'

    class Media:
        js = ('blog/admin/post-images.js',)


class BlogAdmin(admin.ModelAdmin):
    exclude = ('image',)
    readonly_fields = ('main_image_preview',)
    inlines = (PostImageInline,)

    @admin.display(description='Image')
    def main_image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="max-width:240px;max-height:180px" alt="">', obj.image.url)
        return 'Виберіть головне зображення в галереї нижче.'
    # Відображення полів у списку постів
    list_display = ('title', 'youtube')
    list_filter = ('categories',)  # Фільтрація по категорії


admin.site.register(Category)
admin.site.register(Post, BlogAdmin)
