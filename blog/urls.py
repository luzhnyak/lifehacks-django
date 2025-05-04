from django.urls import path
from . import views

urlpatterns = [    
    path('', views.posts, name='category_detail'),
    path('<str:slug>', views.post, name='post_detail'),
]
