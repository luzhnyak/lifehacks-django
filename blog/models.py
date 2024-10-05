from django.db import models
from django.urls import reverse
from django.utils.text import slugify
from django.db.models.signals import post_save
from django.dispatch import receiver

import itertools
import os
from unidecode import unidecode
from PIL import Image


def category_image_upload_to(instance, filename):
    extension = filename.split('.')[-1]
    filename = f"{instance.slug}.{extension}"
    return os.path.join('categories/', filename)


class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.CharField(max_length=100, unique=True, blank=True)
    image = models.ImageField(
        upload_to=category_image_upload_to, blank=True, null=True)
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


def category_image_upload_to(instance, filename):
    extension = filename.split('.')[-1]
    filename = f"{instance.slug}.{extension}"
    return os.path.join('categories/', filename)


class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.CharField(max_length=100, unique=True, blank=True)
    image = models.ImageField(
        upload_to=category_image_upload_to, blank=True, null=True)
    description = models.TextField(blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.slug or self.slug == "":
            self.slug = slugify(unidecode(self.name))
            original_slug = self.slug
            for i in itertools.count(1):
                if not Category.objects.filter(slug=self.slug).exists():
                    break
                self.slug = f'{original_slug}-{i}'
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('category_detail', args=[str(self.slug)])

    def __str__(self):
        return self.name


@receiver(post_save, sender=Category)
def resize_and_crop_image(sender, instance, **kwargs):
    if instance.image:
        img_path = instance.image.path
        if os.path.exists(img_path):  # Перевіряємо, чи існує файл
            img = Image.open(img_path)

            # Задаємо потрібні розміри (ширина, висота)
            target_size = (640, 480)

            # Змінюємо розмір зображення, зберігаючи пропорції
            img_ratio = img.width / img.height
            target_ratio = target_size[0] / target_size[1]

            if img_ratio > target_ratio:
                # Якщо зображення ширше, ніж потрібно, змінюємо висоту, залишаючи ширину пропорційною
                new_height = target_size[1]
                new_width = int(new_height * img_ratio)
            else:
                # Якщо зображення вище, ніж потрібно, змінюємо ширину, залишаючи висоту пропорційною
                new_width = target_size[0]
                new_height = int(new_width / img_ratio)

            # Використовуємо Image.Resampling.LANCZOS для високоякісного зміщення
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

            # Обрізаємо зайві частини для відповідності точному розміру
            left = (new_width - target_size[0]) / 2
            top = (new_height - target_size[1]) / 2
            right = (new_width + target_size[0]) / 2
            bottom = (new_height + target_size[1]) / 2

            img = img.crop((left, top, right, bottom))

            # Зберігаємо зображення
            img.save(img_path)


def post_image_upload_to(instance, filename):
    extension = filename.split('.')[-1]
    filename = f"{instance.slug}.{extension}"
    return os.path.join('posts/', filename)


class Post(models.Model):
    title = models.CharField(max_length=200)
    slug = models.CharField(max_length=200, unique=True, blank=True)
    content = models.TextField()
    image = models.ImageField(
        upload_to=post_image_upload_to, blank=True, null=True)
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
        return reverse('post_detail', args=[str(self.slug)])

    def __str__(self):
        return self.title


@receiver(post_save, sender=Post)
def resize_image_post(sender, instance, **kwargs):
    if instance.image:
        img_path = instance.image.path
        if os.path.exists(img_path):  # Перевіряємо, чи існує файл
            img = Image.open(img_path)

            # Максимальні розміри
            max_size = (800, 600)
            img.thumbnail(max_size)

            # Зберігаємо зображення
            img.save(img_path)
