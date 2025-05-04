from django.shortcuts import render
from django.shortcuts import get_object_or_404
from .models import Post
from .models import Category, Post
from django.core.paginator import Paginator


def index(request):
    categories = Category.objects.all()
    return render(request, 'blog/index.html', {"categories": categories, "active": "posts"})


def posts(request):
    category_slug = request.GET.get('category')
    page_number = request.GET.get('page')

    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        posts = category.posts.all()
    else:
        posts = Post.objects.all()
        category = None

    categories = Category.objects.all()

    paginator = Paginator(posts, 12)
    page_obj = paginator.get_page(page_number)

    return render(request, 'blog/posts.html', {"categories": categories, "category": category, "page_obj": page_obj, "active": "posts"})


def post(request, slug):
    categories = Category.objects.all()
    post = Post.objects.filter(slug=slug).first()
    return render(request, 'blog/post.html', {"categories": categories, "post": post, "active": "posts"})
