from django.db import models
from django.urls import reverse


class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.CharField(max_length=100, unique=True)
    image = models.CharField(max_length=200)
    description = models.TextField()

    def get_absolute_url(self):
        return reverse('category_detail', args=[str(self.slug)])

    def __str__(self):
        return self.name


class Post(models.Model):
    title = models.CharField(max_length=200)
    slug = models.CharField(max_length=200, unique=True)
    content = models.TextField()
    image = models.CharField(max_length=200)
    youtube = models.CharField(max_length=100)
    tiktok = models.CharField(max_length=100)
    category = models.ForeignKey(
        Category, related_name='posts', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def anons(self):
        text = self.content.replace("&nbsp;", " ")
        text = text.replace("\n", " ")
        text = text.replace("\r", " ")
        text = text.replace("  ", " ")
        text = text.replace("&amp;", "&")
        text = text.replace("&#39;", "'")
        text = text.replace('&quot;', '"')
        text = text.replace("&raquo;", '"')
        text = text.replace("&laquo;", '"')
        text = text.replace("&rsquo;", "'")
        return text.lstrip()[0:300]

    def get_absolute_url(self):
        return reverse('post_detail', args=[str(self.category.slug), str(self.slug)])

    def __str__(self):
        return self.title
