from io import BytesIO
from tempfile import TemporaryDirectory

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from PIL import Image

from .models import Category, Post


class BlogTests(TestCase):
    def test_missing_post_returns_404(self):
        self.assertEqual(self.client.get('/posts/missing').status_code, 404)

    def test_category_absolute_url_filters_posts(self):
        category = Category.objects.create(name='Kitchen')
        post = Post.objects.create(title='Recipe', content='Text')
        post.categories.add(category)
        Post.objects.create(title='Other', content='Text')
        response = self.client.get(category.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(response.context['page_obj']), [post])

    def test_list_is_newest_first_and_has_a_heading(self):
        first = Post.objects.create(title='First', content='Text')
        last = Post.objects.create(title='Last', content='Text')
        response = self.client.get('/posts/')
        self.assertEqual(list(response.context['page_obj']), [last, first])
        self.assertContains(response, '<h1>Лайфхаки</h1>', html=True)

    def test_pagination_preserves_category(self):
        category = Category.objects.create(name='Kitchen')
        for number in range(25):
            post = Post.objects.create(title=f'Post {number}', content='Text')
            post.categories.add(category)
        response = self.client.get('/posts/', {'category': 'kitchen', 'page': 2})
        for page in (1, 3):
            self.assertContains(response, f'href="?category=kitchen&amp;page={page}"')
        self.assertEqual(len(response.context['page_obj']), 12)

    def test_slug_generation_handles_empty_and_long_names(self):
        for model, field, length in ((Category, 'name', 100), (Post, 'title', 200)):
            with self.subTest(model=model.__name__):
                first = model.objects.create(**{field: 'a' * length})
                second = model.objects.create(**{field: 'a' * length})
                self.assertLessEqual(len(second.slug), length)
                self.assertNotEqual(first.slug, second.slug)
                values = {field: '!!!'}
                if model is Post:
                    values['content'] = 'Text'
                empty = model.objects.create(**values)
                self.assertTrue(empty.slug)
                empty.full_clean(exclude=['categories'] if model is Post else None)

    def test_slug_is_stable_after_title_change(self):
        post = Post.objects.create(title='Порада', content='Text')
        post.title = 'Changed'
        post.save()
        self.assertEqual(Post.objects.get(pk=post.pk).slug, 'porada')

    def test_summary_strips_html_and_decodes_entities(self):
        post = Post(content='<p>One&nbsp; &amp; two</p>\n<p>Three</p>')
        self.assertEqual(post.anons, 'One & two Three')

    def test_article_removes_active_html_but_keeps_formatting(self):
        post = Post.objects.create(
            title='HTML',
            content='<p><strong>Useful</strong></p><script>alert(1)</script>'
                    '<img src="photo.jpg" onerror="alert(2)">'
                    '<a href="javascript:alert(3)">link</a>',
        )
        response = self.client.get(post.get_absolute_url())
        self.assertContains(response, '<strong>Useful</strong>', html=True)
        self.assertNotContains(response, '<script>alert(1)</script>')
        self.assertNotContains(response, 'onerror=')
        self.assertNotContains(response, 'javascript:')


class ImageTests(TestCase):
    def setUp(self):
        directory = TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        settings = override_settings(MEDIA_ROOT=directory.name)
        settings.enable()
        self.addCleanup(settings.disable)

    def upload(self, size):
        data = BytesIO()
        Image.new('RGB', size, 'red').save(data, format='JPEG')
        return SimpleUploadedFile('photo.jpg', data.getvalue(), content_type='image/jpeg')

    def test_category_upload_is_cropped(self):
        category = Category.objects.create(name='Kitchen', image=self.upload((1000, 500)))
        with category.image.open('rb') as file, Image.open(file) as image:
            self.assertEqual(image.size, (640, 480))

    def test_post_upload_is_resized(self):
        post = Post.objects.create(title='Photo', content='Text', image=self.upload((1600, 800)))
        with post.image.open('rb') as file, Image.open(file) as image:
            self.assertEqual(image.size, (800, 400))

    def test_long_title_can_have_an_image(self):
        post = Post.objects.create(title='a' * 200, content='Text', image=self.upload((100, 100)))
        post.refresh_from_db()
        self.assertLessEqual(len(post.image.name), 100)
        with post.image.open('rb') as file, Image.open(file) as image:
            self.assertEqual(image.size, (100, 100))

    def test_edit_does_not_reencode_existing_image(self):
        post = Post.objects.create(title='Photo', content='Text', image=self.upload((1600, 800)))
        with post.image.open('rb') as file:
            before = file.read()
        post.title = 'Updated'
        post.save(update_fields=['title'])
        with post.image.open('rb') as file:
            self.assertEqual(file.read(), before)

    @override_settings(STORAGES={'default': {'BACKEND': 'django.core.files.storage.InMemoryStorage'}})
    def test_upload_does_not_require_a_local_path(self):
        category = Category.objects.create(name='Remote', image=self.upload((1000, 500)))
        with category.image.open('rb') as file, Image.open(file) as image:
            self.assertEqual(image.size, (640, 480))


