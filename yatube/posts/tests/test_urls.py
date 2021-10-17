from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from http import HTTPStatus

from ..models import Group, Post

User = get_user_model()


class StaticURLTests(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_homepage(self):
        response = self.guest_client.get('/')
        self.assertEqual(response.status_code, HTTPStatus.OK)


class PostURLTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug'
        )
        cls.user_more = User.objects.create_user(username='testuser1')
        cls.user = User.objects.create_user(username='testuser2')
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.user,
            group=cls.group
        )
        cls.post_more = Post.objects.create(
            text='Еще тестовый текст',
            author=cls.user_more,
            group=None
        )
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.guest_client = Client()

    def test_templates_url(self):
        templates_urls = {
            '/': 'posts/index.html',
            '/group/test_slug/': 'posts/group_list.html',
            '/profile/testuser2/': 'posts/profile.html',
            '/posts/1/': 'posts/post_detail.html',
            '/create/': 'posts/create_post.html',
            '/posts/1/edit/': 'posts/create_post.html'
        }
        for adress, template in templates_urls.items():
            with self.subTest(adress=adress):
                response = self.authorized_client.get(adress)
                self.assertTemplateUsed(response, template)

    def test_http_status(self):
        list_html_status = {
            '/': HTTPStatus.OK,
            '/group/test_slug/': HTTPStatus.OK,
            '/profile/testuser1/': HTTPStatus.OK,
            '/posts/1/': HTTPStatus.OK,
        }
        for adress, status_code in list_html_status.items():
            with self.subTest(adress=adress):
                response = self.guest_client.get(adress)
                self.assertEqual(response.status_code, status_code)

    def test_http_status_404(self):
        adress_404 = '/unexisting_page/'
        response = self.guest_client.get(adress_404)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_auth_available(self):
        adress_create = '/create/'
        response = self.authorized_client.get(adress_create)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_not_auth_available(self):
        adress_create = '/create/'
        response = self.guest_client.get(adress_create)
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_auth_author(self):
        adress_edit = '/posts/1/edit/'
        response = self.authorized_client.get(adress_edit)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_redirect_guest(self):
        adress_edit = '/posts/1/edit/'
        response = self.guest_client.get(adress_edit)
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_redirect_not_author(self):
        adress_edit = '/posts/2/edit/'
        response = self.authorized_client.get(adress_edit)
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_url_add_comment(self):
        comment_page = '/posts/1/comment'
        response = self.authorized_client.get(comment_page)
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_url_follow(self):
        follow = '/profile/testuser1/follow'
        response = self.authorized_client.get(follow)
        self.assertEqual(response.status_code, HTTPStatus.MOVED_PERMANENTLY)

    def test_url_unfollow(self):
        unfollow = '/profile/testuser1/unfollow'
        response = self.authorized_client.get(unfollow)
        self.assertEqual(response.status_code, HTTPStatus.MOVED_PERMANENTLY)
