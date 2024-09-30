from django.shortcuts import render
from blog.models import Category, Post

# Create your views here.


def index(request):
    categories = Category.objects.all()
    return render(request, 'main/index.html', {"categories": categories, 'posts': []})


def search(request):
    # menu = Menu.objects.all()
    return render(request, 'main/search.html', {"menu": [], "active": "home"})
