from django.urls import path
from django.contrib.sitemaps.views import sitemap
from . import views
from blog.sitemaps import PostSitemap

sitemaps = {
    'posts': PostSitemap,
}

urlpatterns = [
    path('', views.index, name='index'),
    path('search', views.search),
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps},
         name='django.contrib.sitemaps.views.sitemap'),
]
