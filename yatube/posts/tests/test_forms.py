import shutil
import tempfile
from http import HTTPStatus

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..forms import PostForm
from ..models import Comment, Group, Post, User

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='UserTest')
        cls.group_1 = Group.objects.create(
            title='Тестовая группа_1',
            slug='group_test_1'
        )
        cls.group_2 = Group.objects.create(
            title='Тестовая группа_2',
            slug='group_test_2'
        )
        cls.group_3 = Group.objects.create(
            title='Тестовая группа_3',
            slug='group_test_3'
        )
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый текст',
            group=cls.group_1,
        )
        cls.form = PostForm()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_user = Client()
        self.authorized_user = Client()
        self.authorized_user.force_login(self.user)
        self.post = Post.objects.create(
            text='Тестовый пост',
            author=self.user,
            group=self.group_1
        )

    def test_create_post_form(self):
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=self.small_gif,
            content_type='image/gif'
        )
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Тестовый пост',
            'group': self.group_1.pk,
            'image': uploaded,
        }
        response = self.authorized_user.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response,
            reverse('posts:profile', kwargs={'username': self.user})
        )
        self.assertEqual(
            Post.objects.count(),
            posts_count + 1,
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        post = Post.objects.first()
        check_post_fields = (
            (post.author, self.post.author),
            (post.text, self.post.text),
            (post.group, self.post.group),
            (post.image, f'posts/{uploaded}'),
        )
        for new_post, expected in check_post_fields:
            with self.subTest(new_post=expected):
                self.assertEqual(new_post, expected)

    def test_edit_post_form(self):
        posts_count = Post.objects.count()
        uploaded = SimpleUploadedFile(
            name='small_1.gif',
            content=self.small_gif,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Новый пост_ред.',
            'group': self.group_2.pk,
            'image': uploaded
        }
        response = self.authorized_user.post(
            reverse('posts:post_edit', args=[self.post.pk]),
            data=form_data, follow=True)
        self.assertRedirects(response, reverse(
            'posts:post_detail', args=(self.post.pk,)),
        )
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertTrue(
            Post.objects.filter(
                text=form_data['text'],
                group=form_data['group'],
                author=self.user,
                image='posts/small_1.gif'
            ).exists())

    def test_unauthorized_user_create_post(self):
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Новый пост',
            'group': self.group_3.pk,
        }
        response = self.guest_user.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        redirect = reverse('login') + '?next=' + reverse('posts:post_create')
        self.assertRedirects(response, redirect)
        self.assertEqual(Post.objects.count(), posts_count)

    def test_unauthorized_user_edit(self):
        redir = reverse('users:login')
        redir_2 = reverse('posts:post_edit', kwargs={'post_id': self.post.pk})
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Тестовый пост',
            'group': self.group_3.id,
        }
        response = self.guest_user.post(
            redir_2,
            data=form_data,
            follow=True,
        )
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertRedirects(
            response,
            f"{redir}?next={redir_2}")

        self.assertTrue(
            Post.objects.filter(
                text='Тестовый пост',
            ).exists()
        )

    def test_add_comment_authorized_user(self):
        comment_count = Comment.objects.count()
        form_data = {
            'author': self.user,
            'text': 'комментарий',
            'post': self.post,
        }
        response = self.authorized_user.post(
            reverse('posts:add_comment', args=(self.post.pk,)),
            data=form_data, follow=True)
        self.assertEqual(Comment.objects.count(), comment_count + 1)
        self.assertRedirects(response, reverse(
            'posts:post_detail',
            args=(self.post.pk,)
        ))
        self.assertTrue(
            Comment.objects.filter(
                text=form_data['text']
            ).exists()
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        comment = Comment.objects.first()
        comment_text = comment.text
        self.assertEqual(comment_text, form_data['text'])

    def test_add_comment_unauthorized_user(self):
        redir = reverse('users:login')
        redir2 = reverse('posts:add_comment', kwargs={'post_id': self.post.pk})
        comment_count = Comment.objects.count()
        response = self.client.post(
            redir2,
        )
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertRedirects(
            response,
            f"{redir}?next={redir2}",
        )
        self.assertEqual(Comment.objects.count(), comment_count)
