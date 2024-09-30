from django.db import models
from django.urls import reverse
from django.utils.text import slugify
import itertools
from Unidecode import unidecode


class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.CharField(max_length=100, unique=True, blank=True)
    image = models.CharField(max_length=200, blank=True, null=True)
    description = models.TextField(blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.slug or self.slug == "":
            self.slug = slugify(unidecode(self.name))
            original_slug = self.slug
            for i in itertools.count(1):
                if not Post.objects.filter(slug=self.slug).exists():
                    break
                self.slug = f'{original_slug}-{i}'
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('category_detail', args=[str(self.slug)])

    def __str__(self):
        return self.name


class Post(models.Model):
    title = models.CharField(max_length=200)
    slug = models.CharField(max_length=200, unique=True, blank=True)
    content = models.TextField()
    image = models.CharField(max_length=200, blank=True, null=True)
    youtube = models.CharField(max_length=100, blank=True, null=True)
    tiktok = models.CharField(max_length=100, blank=True, null=True)
    categories = models.ManyToManyField(Category, related_name='posts')
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.slug or self.slug == "":
            self.slug = slugify(unidecode(self.title))
            original_slug = self.slug
            for i in itertools.count(1):
                if not Post.objects.filter(slug=self.slug).exists():
                    break
                self.slug = f'{original_slug}-{i}'
        super().save(*args, **kwargs)

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
