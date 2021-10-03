import shutil
import os

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django import forms
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache

from posts.models import Group, Post, Comment, Follow

User = get_user_model()


class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.list_dir = os.listdir(os.getcwd())
        cls.user = User.objects.create_user(
            username='TestTestov',
            first_name='Test',
            last_name='Testov',
            email='test@test.ru')
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            slug='test_slug',
            description='Тестовое описание',
        )
        cls.other_group = Group.objects.create(
            title='Другой тестовый заголовок',
            slug='other_test_slug',
            description='Другое тестовое описание',
        )
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=cls.small_gif,
            content_type='image/gif'
        )
        cls.form_fields = {
            'text': forms.CharField,
            'group': forms.ModelChoiceField,
            'image': forms.ImageField,
        }
        amount_posts = 15
        for cls.post in range(amount_posts):
            cls.post = Post.objects.create(
                author=cls.user,
                text='Тестовый текст',
                group=cls.group,
                image=cls.uploaded
            )

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        for path in os.listdir(os.getcwd()):
            if path not in cls.list_dir:
                shutil.rmtree(path, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.author = Client()
        self.author.force_login(self.post.author)
        self.guest_client = Client()

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse(
                'posts:group_list',
                kwargs={'slug': 'test_slug'}): 'posts/group_list.html',
            reverse(
                'posts:profile',
                args=[self.user.username]): 'posts/profile.html',
            reverse(
                'posts:post_detail',
                args=[self.post.id]): 'posts/post_detail.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse('posts:post_edit', kwargs={
                'post_id': self.post.id}): 'posts/create_post.html',
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def post_check_fields(self, post):
        with self.subTest(post=post):
            self.assertEqual(post.text, self.post.text)
            self.assertEqual(post.author, self.post.author)
            self.assertEqual(post.group.id, self.post.group.id)
            self.assertEqual(post.image, self.post.image)

    def test_posts_index_page_shows_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:index'))
        self.post_check_fields(response.context['page_obj'][0])

    def test_group_list_shows_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse(
            'posts:group_list', kwargs={'slug': 'test_slug'}))
        self.assertEqual(response.context['group'].title, 'Тестовый заголовок')
        self.assertEqual(
            response.context['group'].description, 'Тестовое описание')
        self.assertEqual(response.context['group'].slug, 'test_slug')
        self.post_check_fields(response.context['page_obj'][0])

    def test_profile_page_shows_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse(
            'posts:profile', kwargs={'username': self.user.username}))
        self.assertEqual(response.context['user'], self.user)
        self.post_check_fields(response.context['page_obj'][0])

    def test_post_view_page_shows_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse(
            'posts:post_detail', kwargs={'post_id': self.post.id}))
        self.assertEqual(response.context['user'], self.user)

    def test_post_edit_page_shows_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse(
            'posts:post_edit', kwargs={'post_id': self.post.id}))
        self.assertEqual(response.context['user'], self.user)

    def test_create_post_page_shows_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_post_appeared_on_the_main_page(self):
        """Пост появляется на главной странице сайта."""
        response = self.authorized_client.get(reverse('posts:index'))
        self.assertIn(self.post, response.context['page_obj'])

    def test_post__on_group_page(self):
        """Пост появляется на странице выбранной группы."""
        response = self.authorized_client.get(reverse(
            'posts:group_list', kwargs={'slug': 'test_slug'}))
        self.assertIn(self.post, response.context['page_obj'])

    def test_post_on_profile_page(self):
        """Пост появляется в профайле пользователя."""
        response = self.authorized_client.get(reverse(
            'posts:profile', kwargs={'username': self.user.username}))
        self.assertIn(self.post, response.context['page_obj'])

    def test_post_not_on_other_groups_page(self):
        """Пост не попал в группу, для которой не был предназначен."""
        response = self.authorized_client.get(reverse(
            'posts:group_list', kwargs={'slug': 'other_test_slug'}))
        self.assertIsNot(self.post, response.context['page_obj'])


class PaginatorTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(
            username='TestTestov',
            first_name='Test',
            last_name='Testov',
            email='test@test.ru')
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            slug='test_slug',
            description='Тестовое описание',
        )
        cls.other_group = Group.objects.create(
            title='Другой тестовый заголовок',
            slug='other_test_slug',
            description='Другое тестовое описание',
        )
        amount_posts = 15
        for cls.post in range(amount_posts):
            cls.post = Post.objects.create(
                author=cls.user,
                text='Тестовый текст',
                group=cls.group
            )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.author = Client()
        self.author.force_login(self.post.author)

    def test_post_index_paginator(self):
        """На page_index количество постов должно быть 10"""
        respone = self.authorized_client.get(reverse('posts:index'))
        self.assertEqual(len(respone.context['page_obj']), 10)

    def test_second_post_index_paginator(self):
        """На первой page_index количество постов должно быть 5"""
        respone = self.authorized_client.get(reverse(
            'posts:index') + '?page=2')
        self.assertEqual(len(respone.context['page_obj']), 5)

    def test_second_post_index_paginator(self):
        """На второй page_index количество постов должно быть 5"""
        respone = self.authorized_client.get(reverse(
            'posts:index') + '?page=2')
        self.assertEqual(len(respone.context['page_obj']), 5)

    def test_group_list_paginator(self):
        """На первой group_list количество постов должно быть 10"""
        respone = self.authorized_client.get(reverse(
            'posts:group_list', kwargs={'slug': 'test_slug'}))
        self.assertEqual(len(respone.context['page_obj']), 10)

    def test_profile_paginator(self):
        """На первой profile количество постов должно быть 10"""
        respone = self.authorized_client.get(reverse(
            'posts:profile', kwargs={'username': self.user.username}))
        self.assertEqual(len(respone.context['page_obj']), 10)


class CommentTest(TestCase):
    def setUp(self):
        self.user_reader = User.objects.create_user(username='Test1')
        self.user_author = User.objects.create_user(username='Test2')
        self.authors_post = Post.objects.create(
            text='Тестовая запись',
            author=self.user_author
        )
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user_reader)

    def test_comment_guest(self):
        """Неавторизованный пользователь не может оставить коментарий"""
        comment_data = {
            'text': 'Коментарий которого не должно быть',
        }
        self.guest_client.post(
            reverse(
                'posts:add_comment',
                kwargs={
                    'post_id': self.authors_post.id,
                }
            ),
            data=comment_data,
            follow=True
        )
        self.assertEqual(
            Comment.objects.count(),
            0,
            'Неавторизованный пользователь не должен '
            'иметь возможности добавлять коментарии'
        )

    def test_comment_authorizate(self):
        """Авторизованный пользователь может оставить коментарий"""
        url_comment = f'/posts/{self.authors_post.id}/'
        comment_data = {
            'text': 'Коментарий авторизованного пользователя',
        }
        response = self.authorized_client.post(
            reverse(
                'posts:add_comment',
                kwargs={
                    'post_id': self.authors_post.id,
                }
            ),
            data=comment_data,
            follow=True
        )
        self.assertRedirects(response, url_comment)
        self.assertTrue(
            Comment.objects.filter(
                text=comment_data['text'],
                author=self.user_reader,
                post=self.authors_post
            ).exists(),
            'Коментарий не создается или сохраняется с неправильными данными'
        )


class CashTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.test_user = User.objects.create_user(username='Test')
        cls.guest_client = Client()
        number_of_posts = 13
        for num in range(1, number_of_posts + 1):
            Post.objects.create(
                text=f'Текст поста № {num}',
                author=CashTest.test_user
            )

    def test_index_page_cache(self):
        """Посты  хранятся в кэше и обновляются
            каждые 20 сек"""
        response_start = CashTest.guest_client.get(
            reverse('posts:index') + '?page=2'
        )
        Post.objects.create(
            text='Новый пост',
            author=CashTest.test_user
        )
        response_cashe = CashTest.guest_client.get(
            reverse('posts:index') + '?page=2'
        )
        cache.clear()
        response_timeout = CashTest.guest_client.get(
            reverse('posts:index') + '?page=2'
        )
        self.assertEqual(
            response_start.content,
            response_cashe.content,
            'Контент не был закеширован!')
        self.assertNotEqual(
            response_start.content,
            response_timeout.content,
            'При очистке кеша контент не изменился!')


class FollowTest(TestCase):
    def setUp(self):
        self.user_follower = User.objects.create_user(username='Follower')
        self.user_unfollower = User.objects.create_user(username='Unfollower')
        self.user_author = User.objects.create_user(username='Author')
        self.follow = Follow.objects.create(
            user=self.user_follower,
            author=self.user_author
        )
        self.authors_post = Post.objects.create(
            text='Запись автора',
            author=self.user_author
        )
        self.authorized_follower = Client()
        self.authorized_follower.force_login(self.user_follower)
        self.authorized_unfollower = Client()
        self.authorized_unfollower.force_login(self.user_unfollower)

    def test_profile_follow(self):
        """Авторизованный пользователь может подписываться на
        других пользователей и удалять их из подписок."""
        self.authorized_unfollower.get(
            reverse(
                'posts:profile_follow',
                kwargs={'username': self.user_author.username}
            ),
            follow=True
        )
        self.assertTrue(
            self.user_author.following.filter(
                user=self.user_unfollower).exists(),
            'Пользователь не может подписаться на автора'
        )

    def test_profile_unfollow(self):
        """Фолловер может отписаться"""
        self.authorized_follower.get(
            reverse(
                'posts:profile_unfollow',
                kwargs={'username': self.user_author.username}
            ),
            follow=True
        )
        self.assertFalse(
            self.user_author.following.filter(
                user=self.user_follower).exists(),
            'Пользователь не может отписаться от автора'
        )
