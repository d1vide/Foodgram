from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import CheckConstraint, UniqueConstraint, Q

from .constants import FIRST_NAME_LENGTH, LAST_NAME_LENGTH


class User(AbstractUser):
    first_name = models.CharField('Имя',
                                  max_length=FIRST_NAME_LENGTH)
    last_name = models.CharField('Фамилия',
                                 max_length=LAST_NAME_LENGTH)
    email = models.EmailField('Почта',
                              unique=True)
    avatar = models.ImageField('Аватар',
                               upload_to='users/',
                               null=True)

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
                                        name='unique_subscribe'),
                       CheckConstraint(check=~Q(subscriber=models.F('user')),
                                       name='check_self_subscribe'))

    def __str__(self):
        return (f'Пользователь {self.subscriber.email} подписан '
                f'на {self.user.email}')
