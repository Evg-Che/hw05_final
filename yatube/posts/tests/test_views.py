from http import HTTPStatus

from django import forms
from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Follow, Group, Post, User


class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='UserTest')
        cls.group = Group.objects.create(
            title="Тестовая группа",
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
        cache.clear()

    def test_pages_uses_correct_template(self):
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

    def test_posts_show_correct_context(self):
        namespace_list = {
            reverse('posts:index'): 'page_obj',
            reverse('posts:group_list', args=[self.group.slug]): 'page_obj',
            reverse('posts:profile', args=[self.user.username]): 'page_obj',
            reverse('posts:post_detail', args=[self.post.pk]): 'post',
        }
        for reverse_name, context in namespace_list.items():
            first_object = self.guest_user.get(reverse_name)
            if context == 'post':
                first_object = first_object.context[context]
            else:
                first_object = first_object.context[context][0]
            post_text = first_object.text
            post_author = first_object.author
            post_group = first_object.group
            posts_dict = {
                post_text: self.post.text,
                post_author: self.user,
                post_group: self.group,
            }
            for post_param, test_post_param in posts_dict.items():
                with self.subTest(
                        post_param=post_param,
                        test_post_param=test_post_param):
                    self.assertEqual(post_param, test_post_param)

    def test_create_post_show_correct_context(self):
        namespace_list = [
            reverse('posts:post_create'),
            reverse('posts:post_edit', args=[self.post.pk])
        ]
        for reverse_name in namespace_list:
            response = self.authorized_user.get(reverse_name)
            form_fields = {
                'text': forms.fields.CharField,
                'group': forms.fields.ChoiceField,
            }
            for value, expected in form_fields.items():
                with self.subTest(value=value):
                    form_field = response.context['form'].fields[value]
                    self.assertIsInstance(form_field, expected)

    def test_post_another_group(self):
        response = self.authorized_user.get(
            reverse('posts:group_list', args={self.group.slug}))
        first_object = response.context["page_obj"][0]
        post_text = first_object.text
        self.assertTrue(post_text, 'Текст тестового поста')

    def test_cache_index(self):
        post = Post.objects.create(
            text='Тестовый пост',
            author=self.user,
        )
        response = self.authorized_user.get(reverse('posts:index'))
        Post.objects.filter(pk=post.pk).delete()
        response_2 = self.authorized_user.get(reverse('posts:index'))
        self.assertEqual(response.content, response_2.content)

    def test_404_page(self):
        response = self.guest_user.get('/OmG333/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_add_comment_authorized_user(self):
        comment = {'text': 'Тестовый коммент'}
        self.authorized_user.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.pk}),
            data=comment, follow=True
        )
        response = self.authorized_user.get(f'/posts/{self.post.id}/')
        self.assertContains(response, comment['text'])

    def test_add_comment_unauthorized_user(self):
        comment = {'text': 'Тестовый коммент_2'}
        self.guest_user.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.pk}),
            data=comment, follow=True
        )
        response = self.guest_user.get(f'/posts/{self.post.pk}/')
        self.assertNotContains(response, comment['text'])

    def test_follow(self):
        author_user = User.objects.create(username='Testik_User')
        self.authorized_user.get(reverse(
            'posts:profile_follow',
            args=(author_user.username,)))
        follow_exist = Follow.objects.filter(user=self.user,
                                             author=author_user
                                             ).exists()
        self.assertTrue(follow_exist)

    def test_unfollow(self):
        author_user = User.objects.create(username='Testik_User')
        Follow.objects.create(user=self.user,
                              author=author_user)
        self.authorized_user.get(reverse(
            'posts:profile_unfollow',
            args=(author_user.username,)))
        follow_exist = Follow.objects.filter(user=self.user,
                                             author=author_user
                                             ).exists()
        self.assertFalse(follow_exist)

    def test_posts_in_follow_index(self):
        author_user = User.objects.create(username='Testik_User')
        post = Post.objects.create(
            text='Тестовый текст поста',
            author=author_user
        )
        Follow.objects.create(
            user=self.user,
            author=author_user
        )
        response = self.authorized_user.get(reverse('posts:follow_index'))
        self.assertIn(post, response.context['page_obj'])

    def test_posts_not_in_follow(self):
        author_user = User.objects.create(username='Testik_User')
        post = Post.objects.create(
            text='Тестовый текст поста',
            author=author_user
        )
        response = self.authorized_user.get(
            reverse('posts:follow_index'))
        self.assertNotIn(post, response.context['page_obj'])
