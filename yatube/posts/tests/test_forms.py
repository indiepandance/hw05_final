import shutil
import tempfile


from django.test import Client, TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile

from posts.models import Group, Post, Comment
from posts.forms import PostForm

User = get_user_model()


class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        settings.MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.user = User.objects.create_user(username='TestTestov')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовая группа',
            group=cls.group,
            image=uploaded,
        )

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.author = Client()
        self.author.force_login(self.post.author)

    def test_post_create(self):
        """При создания поста создаётся новая запись в базе данных."""
        post_count = Post.objects.count()
        form_data = {
            'text': self.post.text,
            'author': self.post.author,
            'group': self.group.id,
            'image': self.post.image,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertEqual(Post.objects.count(), post_count + 1)
        self.assertEqual(self.post.text, PostCreateFormTests.post.text)
        self.assertEqual(self.post.author, PostCreateFormTests.post.author)
        self.assertEqual(self.post.group, PostCreateFormTests.group)
        self.assertEqual(self.post.image, PostCreateFormTests.post.image)
        self.assertRedirects(response, reverse(
            'posts:profile',
            kwargs={'username': self.user.username}
        ))

    def test_post_edit(self):
        """При редактировании поста изменяется пост в базе данных."""
        post_count = Post.objects.count()
        form_data = {
            'text': 'Тестовый',
        }
        response = self.author.post(
            reverse('posts:post_edit', kwargs={
                'post_id': self.post.id}),
            data=form_data,
            follow=True
        )
        self.assertEqual(Post.objects.count(), post_count)
        self.assertRedirects(response, reverse(
            'posts:post_detail',
            kwargs={'post_id': self.post.id}
        ))


class TestCommentCreate(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описания',
        )
        cls.post = Post.objects.create(
            text='Текст',
            author=User.objects.create_user(username='author'),

        )
        cls.comment = Comment.objects.create(
            post=cls.post,
            author=User.objects.create_user(username='commentator'),
            text='текст',
        )

        cls.form = PostForm()

    def setUp(self):
        self.guest = Client()
        self.user = User.objects.create_user(username='test')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_comment(self):
        """Тестирование формы комментариев"""
        comments_counter = Comment.objects.count()
        form_data = {
            'text': 'Тестовый текст',
        }

        response_guest = self.guest.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response_guest, '/auth/login/?next=%2Fposts%2F1%2Fcomment'
        )
        self.assertEqual(Comment.objects.count(), comments_counter)
