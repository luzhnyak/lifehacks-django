from django.test import TestCase

from blog.models import Category, Post


class HomepageTests(TestCase):
    def test_homepage_limits_each_category_without_query_growth(self):
        for category_number in range(5):
            category = Category.objects.create(name=f'Category {category_number}')
            for post_number in range(6):
                post = Post.objects.create(title=f'Post {category_number}-{post_number}', content='Text')
                post.categories.add(category)
        Category.objects.create(name='Empty')
        with self.assertNumQueries(2):
            response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Empty')
        self.assertContains(response, 'Post 0-5')
        self.assertNotContains(response, 'Post 0-0')
