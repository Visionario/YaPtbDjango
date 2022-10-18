from django.db import models


class TelegramUser(models.Model):
    """ Telegram users

        Telegram Limits
        https://limits.tginfo.me/en
        .
    """

    class Meta:
        verbose_name = 'Tg user'
        verbose_name_plural = 'Tg users'

    # Telegram user Data
    user_id = models.BigIntegerField('Telegram user_id', unique=True)
    username = models.CharField('Telegram username', max_length=32, blank=True)
    first_name = models.CharField('Telegram first_name', max_length=64, blank=True)
    last_name = models.CharField('Telegram last_name', max_length=64, blank=True)

    # Local info about this telegram user
    # tos_accepted = models.BooleanField(default=False)
    comments = models.TextField(max_length=1024, default='', blank=True)
    created = models.DateTimeField('Created', auto_now_add=True)
    updated = models.DateTimeField('Updated', auto_now=True)
    is_admin = models.BooleanField('Is telegram admin?', default=False)

    def __str__(self):
        return f"@{self.username} / {self.user_id}"


class HistoryTelegramUser(models.Model):
    """ History and activities

        .
    """

    class Meta:
        verbose_name = 'TG user history'
        verbose_name_plural = 'TG users histories'

    class MessagesTypes(models.IntegerChoices):
        UNKNOWN = 0
        CMD = 1
        TEXT = 2
        DICE = 3

    tg_user = models.ForeignKey(TelegramUser, on_delete=models.CASCADE, verbose_name='Telegram user')
    message_type = models.IntegerField('Telegram message type', choices=MessagesTypes.choices, default=MessagesTypes.UNKNOWN)
    data = models.CharField('Data', max_length=4096, blank=True, null=True)
    full_update_data = models.TextField('Full update data', max_length=8192, blank=False, null=False)
    date_time_stamp = models.DateTimeField('Datetime', auto_now_add=True)
