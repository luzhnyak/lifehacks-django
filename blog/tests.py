from io import BytesIO
from tempfile import TemporaryDirectory

from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TestCase, TransactionTestCase, override_settings
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


class ImageTestMixin:
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


class ImageTests(ImageTestMixin, TestCase):

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


class PostGalleryAdminTests(ImageTestMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.client.force_login(get_user_model().objects.create_superuser(
            username='editor', email='editor@example.com', password='test-password',
        ))
        self.category = Category.objects.create(name='Gallery')
        self.post = Post.objects.create(title='Gallery', content='Text')
        self.url = f'/admin/blog/post/{self.post.pk}/change/'

    def data(self, rows, *, initial=0):
        data = {
            'title': self.post.title, 'slug': self.post.slug, 'content': 'Text',
            'categories': [self.category.pk],
            'images-TOTAL_FORMS': str(len(rows)),
            'images-INITIAL_FORMS': str(initial),
            'images-MIN_NUM_FORMS': '0', 'images-MAX_NUM_FORMS': '1000',
            '_save': 'Save',
        }
        for index, row in enumerate(rows):
            data.update({f'images-{index}-{key}': value for key, value in row.items()})
        return data

    def test_upload_multiple_images_and_select_main_in_one_save(self):
        response = self.client.post(self.url, self.data([
            {'image': self.upload((1600, 800))},
            {'image': self.upload((1200, 900)), 'is_main': 'on'},
        ]))
        self.assertEqual(response.status_code, 302)
        self.post.refresh_from_db()
        self.assertTrue(self.post.image, 'The selected gallery image must become Post.image')
        images = list(self.post.images.order_by('pk'))
        self.assertEqual(len(images), 2)
        self.assertNotEqual(images[0].image.name, images[1].image.name)
        self.assertEqual(self.post.image.name, images[1].image.name)
        self.assertContains(self.client.get(self.post.get_absolute_url()), images[1].image.url)
        with images[0].image.open('rb') as file, Image.open(file) as image:
            self.assertEqual(image.size, (800, 400))
        response = self.client.get(self.url)
        self.assertContains(response, images[0].image.url)
        self.assertContains(response, 'blog/admin/post-images.js')
        forms = response.context['inline_admin_formsets'][0].formset.forms
        self.assertFalse(forms[0]['is_main'].value())
        self.assertTrue(forms[1]['is_main'].value())

    def test_rejects_two_main_images_without_saving_uploads(self):
        response = self.client.post(self.url, self.data([
            {'image': self.upload((100, 100)), 'is_main': 'on'},
            {'image': self.upload((100, 100)), 'is_main': 'on'},
        ]))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['inline_admin_formsets'][0].formset.non_form_errors())
        self.assertFalse(self.post.images.exists())

    def test_switch_main_then_delete_it(self):
        self.client.post(self.url, self.data([
            {'image': self.upload((100, 100)), 'is_main': 'on'},
            {'image': self.upload((100, 100))},
        ]))
        first, second = self.post.images.order_by('pk')
        response = self.client.post(self.url, self.data([
            {'id': first.pk}, {'id': second.pk, 'is_main': 'on'},
        ], initial=2))
        self.assertEqual(response.status_code, 302)
        self.post.refresh_from_db()
        self.assertEqual(self.post.image.name, second.image.name)
        response = self.client.post(self.url, self.data([
            {'id': first.pk}, {'id': second.pk, 'is_main': 'on', 'DELETE': 'on'},
        ], initial=2))
        self.assertEqual(response.status_code, 302)
        self.post.refresh_from_db()
        self.assertFalse(self.post.image)
        self.assertEqual(self.post.images.count(), 1)

    def test_create_post_with_gallery(self):
        data = self.data([
            {'image': self.upload((100, 100)), 'is_main': 'on'},
            {'image': self.upload((100, 100))},
        ])
        data['slug'] = ''
        response = self.client.post('/admin/blog/post/add/', data)
        self.assertEqual(response.status_code, 302)
        post = Post.objects.exclude(pk=self.post.pk).get()
        self.assertEqual(post.images.count(), 2)
        self.assertEqual(post.image.name, post.images.first().image.name)

    def test_main_image_requires_a_file(self):
        response = self.client.post(self.url, self.data([{'is_main': 'on'}]))
        self.assertEqual(response.status_code, 200)
        forms = response.context['inline_admin_formsets'][0].formset.forms
        self.assertIn('image', forms[0].errors)
        self.assertFalse(self.post.images.exists())

    def test_view_only_gallery_preserves_main_when_editing_post(self):
        self.client.post(self.url, self.data([
            {'image': self.upload((100, 100)), 'is_main': 'on'},
        ]))
        self.post.refresh_from_db()
        original_image = self.post.image.name
        attachment = self.post.images.get()
        editor = get_user_model().objects.create_user(username='post-editor', is_staff=True)
        editor.user_permissions.add(*Permission.objects.filter(
            content_type__app_label='blog', codename__in=['change_post', 'view_postimage'],
        ))
        self.client.force_login(editor)
        data = self.data([{'id': attachment.pk}], initial=1)
        data['title'] = 'Updated title'
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 302)
        self.post.refresh_from_db()
        self.assertEqual(self.post.title, 'Updated title')
        self.assertEqual(self.post.image.name, original_image)


class PostGalleryMigrationTests(TransactionTestCase):
    def test_existing_main_image_is_attached_without_changing_its_path(self):
        executor = MigrationExecutor(connection)
        previous = [('blog', '0006_alter_post_options_alter_post_image')]
        current = [('blog', '0007_postimage')]
        executor.migrate(previous)
        try:
            old_apps = executor.loader.project_state(previous).apps
            old_post = old_apps.get_model('blog', 'Post').objects.create(
                title='Existing', slug='existing', content='Text', image='posts/existing.jpg',
            )
            old_apps.get_model('blog', 'Post').objects.create(
                title='Empty', slug='empty', content='Text',
            )
            executor = MigrationExecutor(connection)
            executor.migrate(current)
            apps = executor.loader.project_state(current).apps
            attachment = apps.get_model('blog', 'PostImage').objects.get(post_id=old_post.pk)
            self.assertEqual(attachment.image.name, 'posts/existing.jpg')
            self.assertEqual(apps.get_model('blog', 'PostImage').objects.count(), 1)
            post = apps.get_model('blog', 'Post').objects.get(pk=old_post.pk)
            self.assertEqual(post.image.name, 'posts/existing.jpg')
        finally:
            MigrationExecutor(connection).migrate(current)


