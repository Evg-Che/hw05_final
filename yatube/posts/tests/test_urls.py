from http import HTTPStatus

from django.test import Client, TestCase
from django.urls import reverse

from ..models import Group, Post, User


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='UserTest')

        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Описание тестовой группы',
        )
        cls.post = Post.objects.create(
            text='Тестовый пост',
            pub_date='Дата публикации тестового поста',
            author=cls.user,
            group=cls.group,
        )

    def setUp(self):
        self.guest_user = Client()
        self.authorized_user = Client()
        self.authorized_user.force_login(self.user)

    def test_urls(self):
        templates_page_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list', kwargs={'slug': self.group.slug}): (
                'posts/group_list.html'
            ),
            reverse('posts:profile', kwargs={'username': (
                self.user.username)}): 'posts/profile.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse('posts:post_detail', kwargs={'post_id': (
                self.post.pk)}): 'posts/post_detail.html',
            reverse('posts:post_edit', kwargs={'post_id': (
                self.post.pk)}): 'posts/create_post.html',
        }
        for reverse_name, template in templates_page_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_user.get(reverse_name)
                self.assertTemplateUsed(response, template)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_for_guest(self):
        templates_page_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list', kwargs={'slug': self.group.slug}): (
                'posts/group_list.html'
            ),
            reverse('posts:profile', kwargs={'username': (
                self.user.username)}): 'posts/profile.html',
            reverse('posts:post_detail', kwargs={'post_id': (
                self.post.pk)}): 'posts/post_detail.html',
        }
        for url in templates_page_names:
            with self.subTest():
                response = self.guest_user.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_create_and_post_edit_for_authorized(self):
        templates_page_names = {
            reverse('posts:post_create'),
            reverse('posts:post_edit', args=[self.post.pk])
        }
        for url in templates_page_names:
            with self.subTest():
                response = self.guest_user.get(url)
                self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_create_url_redirect_guest(self):
        response = self.guest_user.get(
            reverse('posts:post_create'))
        self.assertRedirects(
            response,
            f"{reverse('users:login')}?next={reverse('posts:post_create')}"
        )

    def test_post_edit_url_redirect_guest(self):
        redir = reverse('users:login')
        redir_2 = reverse('posts:post_edit', kwargs={'post_id': self.post.pk})
        response = self.guest_user.get(redir_2)
        self.assertRedirects(
            response,
            f"{redir}?next={redir_2}")

    def test_wrong_url_returns_404(self):
        response = self.client.get('/non-existent_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
