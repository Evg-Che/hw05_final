from django.test import TestCase

from ..models import TEXT_LIMIT, Group, Post, User


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )

    def test_models_have_correct_object_names(self):
        field_expected_names = {
            self.post.text[:TEXT_LIMIT]: str(self.post),
            self.group.title: str(self.group),
        }
        for field, expected_value in field_expected_names.items():
            with self.subTest(field=field):
                self.assertEqual(
                    field, expected_value)

    def test_models_verbose_name(self):
        field_verboses = {
            'text': 'Текст поста',
            'pub_date': 'Дата публикации',
            'author': 'Автор',
            'group': 'Группа',
        }
        for field, expected_value in field_verboses.items():
            with self.subTest(field=field):
                model_field = self.post._meta.get_field(field)
                self.assertEqual(model_field.verbose_name, expected_value)

    def test_models_help_text(self):
        field_help_text = {
            'text': 'Введите текст поста',
            'group': 'Группа, к которой будет относиться пост',
        }
        for field, expected_value in field_help_text.items():
            with self.subTest(field=field):
                self.assertEqual(
                    self.post._meta.get_field(field).help_text, expected_value)
