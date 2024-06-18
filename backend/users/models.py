from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import UniqueConstraint

from .constants import FIRST_NAME_LENGTH, LAST_NAME_LENGTH


class User(AbstractUser):
    first_name = models.CharField(max_length=FIRST_NAME_LENGTH,
                                  blank=False, null=False,
                                  verbose_name='Имя')
    last_name = models.CharField(max_length=LAST_NAME_LENGTH,
                                 blank=False, null=False,
                                 verbose_name='Фамилия')
    email = models.EmailField(blank=False, null=False,
                              unique=True,
                              verbose_name='Почта')
    avatar = models.ImageField(upload_to='users/',
                               null=True,
                               verbose_name='Аватар')

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    class Meta:
        verbose_name = 'пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.email


class Subscribe(models.Model):
    subscriber = models.ForeignKey(User,
                                   on_delete=models.CASCADE,
                                   related_name='subscriber',
                                   verbose_name='Подписчик')
    user = models.ForeignKey(User,
                             on_delete=models.CASCADE,
                             related_name='following',
                             verbose_name='Пользователь на которого подписан')

    class Meta:
        verbose_name = 'подписка'
        verbose_name_plural = 'Подписки'
        constraints = (UniqueConstraint(fields=['subscriber', 'user'],
                                        name='unique_subscribe'), )

    def __str__(self):
        return (f'Пользователь {self.subscriber.email} подписан '
                f'на {self.user.email}')
