from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Group, Post, User


class URLTests(TestCase):
    def setUp(self):
        self.guest_client = Client()

        self.user_one = User.objects.create_user(username='one')
        self.user_one_client = Client()
        self.user_one_client.force_login(self.user_one)

        self.user_two = User.objects.create_user(username='two')
        self.user_two_client = Client()
        self.user_two_client.force_login(self.user_two)

        self.test_group = Group.objects.create(
            title='Test Group',
            slug='group',
            description='Description',
        )

        self.test_post = Post.objects.create(
            text='Test post',
            author=self.user_one,
            group=self.test_group,
        )

    def test_urls_allowed_for_guests(self):
        """Страницы доступные неавторизованному пользователю."""
        urls = [
            reverse('index'),
            reverse('about:tech'),
            reverse('about:author'),
            reverse('group', args=['group']),
            reverse('profile', args=[self.user_one]),
            reverse('post', args=[self.user_one, self.test_post.id]),
        ]

        for url in urls:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                msg = f'У гостя не открывается страница {url}'
                self.assertEqual(response.status_code, 200, msg)

    def test_urls_forbidden_for_guests(self):
        """Страницы не доступные неавторизованному пользователю."""
        urls = [
            reverse('new_post'),
            reverse('post_edit', args=[self.user_one, self.test_post.id]),
        ]

        for url in urls:
            with self.subTest(url=url):
                response = self.guest_client.get(url, follow=True)
                expected = f'/auth/login/?next={url}'
                msg = f'У гостя не должна открываться страница {url}'
                self.assertRedirects(response, expected, msg_prefix=msg)

    def test_urls_allowed_for_users(self):
        """Страницы доступные авторизованному пользователю."""
        urls = [
            reverse('new_post'),
            reverse('post_edit', args=[self.user_one, self.test_post.id]),
        ]

        for url in urls:
            with self.subTest(url=url):
                response = self.user_one_client.get(url)
                msg = f'Пользователь не может открыть страницу {url}'
                self.assertEqual(response.status_code, 200, msg)

    def test_url_forbidden_for_another_users(self):
        """Редирект не автора поста."""
        url = reverse('post_edit', args=[self.user_one, self.test_post.id])
        response = self.user_two_client.get(url, follow=True)
        expected = reverse('post', args=[self.user_one, self.test_post.id])
        msg = f'Только у автора должна открываться страница {url}'
        self.assertRedirects(response, expected, msg_prefix=msg)

    def test_404_not_found(self):
        """Сервер возвращает код 404"""
        response = self.guest_client.get('/404/')
        msg = 'Сервер не возвращает код 404 на запрос несуществующей страницы'
        self.assertEqual(response.status_code, 404, msg)
