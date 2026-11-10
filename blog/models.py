import itertools
import nh3
from html import unescape
from io import BytesIO
from pathlib import PurePosixPath
from urllib.parse import urlencode

from django.core.files.base import ContentFile
from django.db import models
from django.urls import reverse
from django.utils.html import strip_tags
from django.utils.text import slugify
from PIL import Image, ImageOps
from unidecode import unidecode


def generate_slug(instance, value, using=None):
    """Preserve existing URLs and reserve space for collision suffixes."""
    max_length = instance._meta.get_field('slug').max_length
    base = slugify(unidecode(value))[:max_length] or instance._meta.model_name
    queryset = type(instance).objects.using(using).exclude(pk=instance.pk)
    candidate = base
    for number in itertools.count(1):
        if not queryset.filter(slug=candidate).exists():
            return candidate
        suffix = f'-{number}'
        candidate = f'{base[:max_length - len(suffix)]}{suffix}'


def prepare_image(field, size, *, crop=False):
    """Process new uploads once, without requiring filesystem storage."""
    if not field or field._committed:
        return
    with Image.open(field.file) as original:
        image_format = original.format
        image = ImageOps.exif_transpose(original)
        if crop:
            image = ImageOps.fit(image, size, method=Image.Resampling.LANCZOS)
        else:
            image.thumbnail(size, Image.Resampling.LANCZOS)
        output = BytesIO()
        image.save(output, format=image_format)
    field.file = ContentFile(output.getvalue(), name=field.name)


def category_image_upload_to(instance, filename):
    return f'categories/{instance.slug}{PurePosixPath(filename).suffix.lower()}'


class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.CharField(max_length=100, unique=True, blank=True)
    image = models.ImageField(upload_to=category_image_upload_to, blank=True, null=True)
    description = models.TextField(blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = generate_slug(self, self.name, kwargs.get('using'))
            if kwargs.get('update_fields') is not None:
                kwargs['update_fields'] = set(kwargs['update_fields']) | {'slug'}
        if kwargs.get('update_fields') is None or 'image' in kwargs['update_fields']:
            prepare_image(self.image, (640, 480), crop=True)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return f"{reverse('category_detail')}?{urlencode({'category': self.slug})}"

    def __str__(self):
        return self.name


def post_image_upload_to(instance, filename):
    return f'posts/{instance.slug}{PurePosixPath(filename).suffix.lower()}'


class Post(models.Model):
    title = models.CharField(max_length=200)
    slug = models.CharField(max_length=200, unique=True, blank=True)
    content = models.TextField()
    image = models.ImageField(upload_to=post_image_upload_to, blank=True, null=True)
    youtube = models.CharField(max_length=100, blank=True, null=True)
    tiktok = models.CharField(max_length=100, blank=True, null=True)
    categories = models.ManyToManyField(Category, related_name='posts')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at', '-pk']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = generate_slug(self, self.title, kwargs.get('using'))
            if kwargs.get('update_fields') is not None:
                kwargs['update_fields'] = set(kwargs['update_fields']) | {'slug'}
        if kwargs.get('update_fields') is None or 'image' in kwargs['update_fields']:
            prepare_image(self.image, (800, 600))
        super().save(*args, **kwargs)

    @property
    def anons(self):
        return ' '.join(unescape(strip_tags(self.content)).split())[:300]

    @property
    def sanitized_content(self):
        return nh3.clean(self.content)

    def get_absolute_url(self):
        return reverse('post_detail', args=[self.slug])

    def __str__(self):
        return self.title
