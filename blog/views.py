from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, render

from .models import Category, Post


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

    return render(request, 'blog/posts.html', {
        'categories': categories,
        'category': category,
        'page_obj': page_obj,
        'active': 'posts',
    })


def post(request, slug):
    categories = Category.objects.all()
    article = get_object_or_404(Post.objects.prefetch_related('categories'), slug=slug)
    return render(request, 'blog/post.html', {
        'categories': categories, 'post': article, 'active': 'posts',
    })
