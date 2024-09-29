from django.shortcuts import render
from .models import Post
from .models import Category, Post
from django.core.paginator import Paginator


def index(request):
    categories = Category.objects.all()
    return render(request, 'blog/index.html', {"categories": categories, "active": "posts"})


def posts(request):
    category_name = request.GET.get('category')
    page_number = request.GET.get('page')

    if category_name:
        posts = Post.objects.filter(categories__name=category_name)
    else:
        posts = Post.objects.all()

    categories = Category.objects.all()
    category = Category.objects.filter(slug=category_name).first()

    paginator = Paginator(posts, 5)
    page_obj = paginator.get_page(page_number)

    return render(request, 'blog/posts.html', {"categories": categories, "category": category, "page_obj": page_obj, "active": "posts"})


def post(request, slug):
    categories = Category.objects.all()
    post = Post.objects.filter(slug=slug).first()
    return render(request, 'blog/post.html', {"categories": categories, "post": post, "active": "posts"})
