from django.db.models import Prefetch
from django.shortcuts import render

from blog.models import Category, Post


def index(request):
    categories = Category.objects.order_by('name', 'pk').prefetch_related(
        Prefetch('posts', queryset=Post.objects.all()[:4], to_attr='latest_posts')
    )
    return render(request, 'main/index.html', {'categories': categories})


def search(request):
    return render(request, 'main/search.html', {"menu": [], "active": "home"})
