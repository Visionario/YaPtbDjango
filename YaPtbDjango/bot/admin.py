# -*- coding: utf-8 -*-
from django.contrib import admin

from .models import HistoryTelegramUser, TelegramUser


@admin.register(TelegramUser)
class TelegramUserAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'user_id',
        'username',
        'first_name',
        'last_name',
        'comments',
        'created',
        'updated',
        'is_admin',
    )
    list_filter = ('created', 'updated', 'is_admin')


@admin.register(HistoryTelegramUser)
class HistoryTelegramUserAdmin(admin.ModelAdmin):
    list_display = ('id', 'tg_user', 'message_type', 'data', 'full_update_data', 'date_time_stamp')
    list_filter = ('tg_user', 'date_time_stamp')
    readonly_fields = ['tg_user', 'message_type', 'data', 'full_update_data', 'date_time_stamp']
