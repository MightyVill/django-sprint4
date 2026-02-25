from django.contrib.auth import get_user_model
from django.db import models
from django.db.models import Count
from django.db.models.functions import Now

from .constants import CHARFIELD_LEN

User = get_user_model()


class PublishedModel(models.Model):
    is_published = (models
                    .BooleanField('Опубликовано',
                                  default=True,
                                  help_text='Снимите галочку,'
                                            ' чтобы скрыть публикацию.'))
    created_at = models.DateTimeField('Добавлено',
                                      auto_now_add=True)

    class Meta:
        abstract = True


class Category(PublishedModel):
    title = models.CharField('Заголовок', max_length=CHARFIELD_LEN)
    description = models.TextField('Описание')
    slug = (models.
            SlugField('Идентификатор', unique=True,
                      help_text='Идентификатор страницы для URL;'
                                ' разрешены символы латиницы,'
                                ' цифры, дефис и подчёркивание.'))

    class Meta:
        verbose_name = 'категория'
        verbose_name_plural = 'Категории'

    def __str__(self):
        return self.title[:15]


class Location(PublishedModel):
    name = models.CharField('Название места', max_length=CHARFIELD_LEN)

    class Meta:
        verbose_name = 'местоположение'
        verbose_name_plural = 'Местоположения'

    def __str__(self):
        return self.name[:15]


class PublishedManager(models.Manager):
    def get_queryset(self) -> models.QuerySet:
        return super().get_queryset().filter(is_published=True,
                                             category__is_published=True,
                                             pub_date__lte=Now()).annotate(
            comment_count=Count('comments')).order_by(
            '-pub_date'
        )


class Post(PublishedModel):
    help_txt = ('Если установить дату и время в будущем'
                ' — можно делать отложенные публикации.')
    title = models.CharField('Заголовок', max_length=CHARFIELD_LEN)
    text = models.TextField('Текст')
    pub_date = (models
                .DateTimeField('Дата и время публикации',
                               help_text=help_txt))
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор публикации',
        related_name='posts'
    )
    location = models.ForeignKey(Location,
                                 on_delete=models.SET_NULL,
                                 null=True,
                                 blank=True,
                                 verbose_name='Местоположение')
    category = models.ForeignKey(Category,
                                 on_delete=models.SET_NULL,
                                 null=True,
                                 verbose_name='Категория',
                                 related_name='posts')
    objects = models.Manager()
    published_posts = PublishedManager()
    image = models.ImageField('Фото', upload_to='posts_images', blank=True)

    class Meta:
        verbose_name = 'публикация'
        verbose_name_plural = 'Публикации'
        ordering = ["-pub_date"]

    def __str__(self):
        return self.title[:15]


class Comment(PublishedModel):
    post = models.ForeignKey(Post,
                             on_delete=models.CASCADE,
                             verbose_name='Публикация',
                             related_name='comments')
    author = models.ForeignKey(User,
                               on_delete=models.CASCADE,
                               verbose_name='Автор комментария')
    text = models.TextField('Текст комментария')
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Добавлено'
    )

    class Meta:
        verbose_name = 'комментарий'
        verbose_name_plural = 'Комментарии'

    def __str__(self):
        return f'Комментарий от {self.author} к "{self.post}"'
