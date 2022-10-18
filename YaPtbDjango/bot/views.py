# coding=utf-8
import json
import logging
import sys

from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpRequest, JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from telegram import Bot, Update
from telegram.error import (TelegramError)

from .apps import BotConfig

logger = logging.getLogger(__name__)


@staff_member_required
def home(request: HttpRequest):
    context = {'bot_list': BotConfig.ptb_bot, 'update_mode': settings.TELEGRAMBOT.get('MODE', 'WEBHOOK')}
    return render(request, 'bot/index.html', context)


@csrf_exempt
def webhook(request: HttpRequest):
    bot_token = settings.TELEGRAMBOT.get('TOKEN', None)
    settings_secret_token = settings.TELEGRAMBOT.get('WEBHOOK_SECRET_TOKEN', None)
    logger.debug(f"WEBHOOK_SECRET_TOKEN: '{settings_secret_token}'")

    # look for 'X-Telegram-Bot-Api-Secret-Token' in request.headers
    header_secret_token = request.headers.get('X-Telegram-Bot-Api-Secret-Token', None)
    logger.debug(f"X-Telegram-Bot-Api-Secret-Token: '{header_secret_token}'")
    if header_secret_token is None:
        logger.warning('X-Telegram-Bot-Api-Secret-Token not found in request.headers')
        return JsonResponse({})

    if header_secret_token != settings_secret_token:
        if header_secret_token is None:
            logger.critical('X-Telegram-Bot-Api-Secret-Token doesnt match WEBHOOK_SECRET_TOKEN in settings')
            return JsonResponse({})

    bot: Bot = BotConfig.getBot()
    if bot is None:
        logger.warning('Request for not found token : {}'.format(bot_token))
        return JsonResponse({})

    try:
        data = json.loads(request.body.decode("utf-8"))

    except:
        logger.warning('Telegram bot <{}> receive invalid request : {}'.format(bot.username, repr(request)))
        return JsonResponse({})

    dispatcher = BotConfig.getDispatcher()
    if dispatcher is None:
        logger.error('Dispatcher for bot <{}> not found : {}'.format(bot.username, bot_token))
        return JsonResponse({})

    try:
        update: Update = Update.de_json(data, bot)
        dispatcher.process_update(update)
        logger.debug('Bot <{}> : Processed update {}'.format(bot.username, update))
    # Dispatch any errors
    except TelegramError as e:
        logger.warning("Bot <{}> : Error was raised while processing Update.".format(bot.username))
        dispatcher.dispatchError(update, e)

    # All other errors should not stop the thread, just print them
    except:
        logger.error("Bot <{}> : An uncaught error was raised while processing an update\n{}".format(bot.username, sys.exc_info()[0]))

    finally:
        return JsonResponse({})
