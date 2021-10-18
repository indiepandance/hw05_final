from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Group(models.Model):
    title = models.CharField(
        max_length=200,
        help_text='Введите название группы',
        verbose_name='Название группы')
    slug = models.SlugField(
        max_length=200,
        unique=True,
        help_text='Введите URL группы',
        verbose_name='URL группы')
    description = models.TextField(
        help_text='Введите описание группы',
        verbose_name='Описание группы')

    def __str__(self):
        return self.title


class Post(models.Model):
    text = models.TextField(
        help_text='Введите текст поста',
        verbose_name='Текст поста')
    pub_date = models.DateTimeField(
        auto_now_add=True,
        help_text='Введите дату публикации',
        verbose_name='Дата публикации')
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='posts',
        help_text='Введите имя автора',
        verbose_name='Имя автора')
    group = models.ForeignKey(
        Group,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='posts',
        help_text='Выберите группу',
        verbose_name='Группа')
    image = models.ImageField(
        upload_to='posts/',
        blank=True,
        help_text='Загрузите картинку',
        verbose_name='Картинка'
    )

    class Meta:
        ordering = ('-pub_date', )
        verbose_name_plural = 'Даты',
        verbose_name = 'Дата'

    def __str__(self):
        return self.text[:15]


class Comment(models.Model):
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Комментируемое сообщение'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Автор комментария'
    )
    text = models.TextField(
        verbose_name='Текст комментария',
        help_text='Прокомментируйте',
    )
    created = models.DateTimeField(
        verbose_name='Дата и время публикации комментария',
        auto_now_add=True,
        db_index=True,
    )

    class Meta:
        ordering = ('-created', )
        verbose_name_plural = 'Даты',
        verbose_name = 'Дата'

    def __str__(self):
        return self.text[:5]


class Follow(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following'
    )

    class Meta:
        constraints = (
            models.UniqueConstraint(
                fields=('user', 'author', ),
                name='unique_follow'
            ),
        )

    def __str__(self):
        return self.user
