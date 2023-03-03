from http import HTTPStatus

from django.test import Client, TestCase
from django.urls import reverse


class TestUrlAbout (TestCase):
    def test_url_exists_at_desired_location(self):
        path_list = (reverse('about:author'), reverse('about:tech'))
        for path in path_list:
            with self.subTest(addres=path):
                guest_client = Client()
                response = guest_client.get(path)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_url_uses_correct_template(self):
        templates_page_names = {reverse('about:author'): 'about/author.html',
                                reverse('about:tech'): 'about/tech.html'}
        for path, template in templates_page_names.items():
            with self.subTest(address=path):
                guest_client = Client()
                response = guest_client.get(path)
                self.assertTemplateUsed(response, template)
