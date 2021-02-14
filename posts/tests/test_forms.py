from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse

from posts.forms import Post
from posts.models import Group, User, Comment


class TestCommentForm(TestCase):
    def setUp(self):
        self.user_troll = User.objects.create_user(username='Troll')
        self.user_troll_client = Client()
        self.user_troll_client.force_login(self.user_troll)
        self.test_post = Post.objects.create(
            text='Test post',
            author=self.user_troll,
        )

    def test_add_comment(self):
        """Форма добавляет комментарий и редиректит обратно на пост."""
        comments_count = Comment.objects.count()
        form_data = {'text': 'Азаза трололо', }
        args = [self.user_troll.username, self.test_post.id]
        response = self.user_troll_client.post(
            reverse('add_comment', args=args),
            data=form_data,
            follow=True)

        expected = comments_count + 1
        msg = 'Форма не добавляет новый комментарий'
        self.assertEqual(Post.objects.count(), expected, msg)

        expected = reverse('post', args=args)
        msg = 'Форма после добавления комментария не редиректит на пост'
        self.assertRedirects(response, expected, msg_prefix=msg)


class PostFormTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='user')
        self.user_client = Client()
        self.user_client.force_login(self.user)

        self.test_post = Post.objects.create(
            text='lalalala',
            author=self.user,
        )
        self.test_group = Group.objects.create(
            title='Тестовая группа',
            slug='testgroup',
        )

    def test_add_new_post_with_image(self):
        """Форма добавляет пост с фото и редиректит на главную страницу."""
        posts_count = Post.objects.count()
        small_gif = (b'\x47\x49\x46\x38\x39\x61\x02\x00'
                     b'\x01\x00\x80\x00\x00\x00\x00\x00'
                     b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
                     b'\x00\x00\x00\x2C\x00\x00\x00\x00'
                     b'\x02\x00\x01\x00\x00\x02\x02\x0C'
                     b'\x0A\x00\x3B')
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif',
        )
        form_data = {
            'text': 'Пост',
            'image': uploaded,
        }
        response = self.user_client.post(
            reverse('new_post'),
            data=form_data,
            follow=True)

        expected = posts_count + 1
        msg = 'Форма не добавляет новый пост с фото'
        self.assertEqual(Post.objects.count(), expected, msg)

        expected = reverse('index')
        msg = 'Форма после добавления поста с фото не редиректит на главную'
        self.assertRedirects(response, expected, msg_prefix=msg)

    def test_edit_post_with_image(self):
        """Форма редактирует пост с фото и редиректит на страницу поста."""
        form_data = {
            'text': 'Новые много букв',
            'image': '',
        }
        response = self.user_client.post(
            reverse('post_edit', args=[self.user, self.test_post.id]),
            data=form_data,
            follow=True)

        self.test_post.refresh_from_db()
        msg = 'Форма не редактирует пост с фото'
        self.assertEqual(self.test_post.text, form_data['text'], msg)

        expected = reverse('post', args=[self.user, self.test_post.id])
        msg = 'Форма редактирования поста с фото не редиректит на главную'
        self.assertRedirects(response, expected, msg_prefix=msg)

    def test_add_new_post(self):
        """Форма добавляет новый пост и редиректит на главную страницу."""
        posts_count = Post.objects.count()
        form_data = {'text': 'tratatata', }
        response = self.user_client.post(
            reverse('new_post'),
            data=form_data,
            follow=True)

        expected = posts_count + 1
        msg = 'Форма не добавляет новый пост'
        self.assertEqual(Post.objects.count(), expected, msg)

        response_form_data = response.context['page'].object_list[0]
        form_text = response_form_data.text
        form_author = response_form_data.author

        post = Post.objects.latest('id')

        self.assertEqual(form_text, post.text)
        self.assertEqual(form_author, post.author)

        expected = reverse('index')
        msg = 'Форма после добавления поста не редиректит на главную'
        self.assertRedirects(response, expected, msg_prefix=msg)

    def test_form_edit_post(self):
        """Валидная форма редактирует запись и производит редирект."""
        form_data = {
            'group': self.test_group.id,
            'text': 'modified-post',
        }
        response = self.user_client.post(
            reverse('post_edit', kwargs={'username': self.user,
                                         'post_id': self.test_post.id}),
            data=form_data,
            follow=True
        )
        self.test_post.refresh_from_db()
        self.assertRedirects(response,
                             reverse('post',
                                     kwargs={'username': self.user.username,
                                             'post_id': self.test_post.id}))
        self.assertEqual(self.test_post.text, form_data['text'])
