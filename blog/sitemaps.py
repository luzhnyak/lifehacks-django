from django.contrib.sitemaps import Sitemap
from .models import Post


# class CategorySitemap(Sitemap):
#     changefreq = 'daily'
#     priority = 0.9

#     def items(self):
#         return Category.objects.all()


class PostSitemap(Sitemap):
    changefreq = 'daily'
    priority = 0.9

    def items(self):
        return Post.objects.all()

    def lastmod(self, obj):
        return obj.created_at
