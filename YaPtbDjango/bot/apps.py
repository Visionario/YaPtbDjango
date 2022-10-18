import importlib
import logging
import os.path

import pytz
import telegram
from django.apps import AppConfig, apps
from django.conf import settings
from django.utils.module_loading import module_has_submodule
from telegram import ParseMode
from telegram.error import InvalidToken, TelegramError
from telegram.ext import Defaults, Dispatcher, Updater, messagequeue as mq
from telegram.utils.request import Request

from .mqbot import MQBot

logger = logging.getLogger(__name__)

# bot_logic.py contains all bot logic.
TELEGRAM_BOT_MODULE_NAME = 'bot_logic'
WEBHOOK_MODE, POLLING_MODE = range(2)


class classproperty(property):
    def __get__(self, obj, objtype=None):
        return super(classproperty, self).__get__(objtype)

    def __set__(self, obj, value):
        super(classproperty, self).__set__(type(obj), value)

    def __delete__(self, obj):
        super(classproperty, self).__delete__(type(obj))


class BotConfig(AppConfig):
    # Original code
    # https://github.com/JungDev/django-telegrambot/blob/master/django_telegrambot/apps.py
    default_auto_field = "django.db.models.BigAutoField"
    name = "bot"
    verbose_name = 'Telegram Bot Core'

    ready_run = False
    ptb_dispatcher = None
    ptb_bot = None
    ptb_updater = None

    @classproperty
    def dispatcher(cls):
        return cls.ptb_dispatcher

    @classproperty
    def updater(cls):
        return cls.ptb_updater

    @classmethod
    def get_dispatcher(cls):
        return cls.ptb_dispatcher

    @classmethod
    def getDispatcher(cls):
        return cls.get_dispatcher()

    @classmethod
    def get_bot(cls):
        return cls.ptb_bot

    @classmethod
    def getBot(cls):
        return cls.get_bot()

    @classmethod
    def get_updater(cls):
        return cls.ptb_updater

    @classmethod
    def getUpdater(cls):
        return cls.get_updater()

    def ready(self):

        # Do not execute bot when environment YAPTBDJANGO_BOT is not 'OK'
        # Useful when migrating or django only
        if os.environ.get('YAPTBDJANGO_BOT', 'NO') == 'NO':
            return

        if BotConfig.ready_run:
            return

        BotConfig.ready_run = True

        self.mode = WEBHOOK_MODE
        if settings.TELEGRAMBOT.get('MODE', 'WEBHOOK') == 'POLLING':
            self.mode = POLLING_MODE

        modes = ['WEBHOOK', 'POLLING']

        logger.info(f'Telegram Bot <{modes[self.mode]} mode>')

        token = settings.TELEGRAMBOT.get('TOKEN', None)
        if token is None:
            logger.critical('Required TOKEN missing in settings')
            return

        certificate = None
        webhook_site = None
        webhook_base = None
        proxy = settings.TELEGRAMBOT.get('PROXY', None)

        if self.mode == WEBHOOK_MODE:
            webhook_site = settings.TELEGRAMBOT.get('WEBHOOK_SITE', None)
            if not webhook_site:
                logger.warning('Required TELEGRAM_WEBHOOK_SITE missing in settings')
                return
            if webhook_site.endswith("/"):
                webhook_site = webhook_site[:-1]

            webhook_base = settings.TELEGRAMBOT.get('WEBHOOK_PREFIX', '/')
            if webhook_base.startswith("/"):
                webhook_base = webhook_base[1:]
            if webhook_base.endswith("/"):
                webhook_base = webhook_base[:-1]

            cert = settings.TELEGRAMBOT.get('WEBHOOK_CERTIFICATE', None)
            if cert and os.path.exists(cert):
                logger.info(f'WEBHOOK_CERTIFICATE found in {cert}')
                certificate = open(cert, 'rb')
            elif cert:
                logger.error(f'WEBHOOK_CERTIFICATE not found in {cert} ')

            allowed_updates = settings.TELEGRAMBOT.get('ALLOWED_UPDATES', None)
            timeout = settings.TELEGRAMBOT.get('TIMEOUT', None)

            try:
                if settings.TELEGRAMBOT.get('MESSAGEQUEUE_ENABLED', False):
                    q = mq.MessageQueue(
                        all_burst_limit=settings.TELEGRAMBOT.get('MESSAGEQUEUE_ALL_BURST_LIMIT', 29),
                        all_time_limit_ms=settings.TELEGRAMBOT.get('MESSAGEQUEUE_ALL_TIME_LIMIT_MS', 1024)
                    )
                    if proxy:
                        request = Request(
                            proxy_url=proxy['proxy_url'],
                            urllib3_proxy_kwargs=proxy['urllib3_proxy_kwargs'],
                            con_pool_size=settings.TELEGRAMBOT.get('MESSAGEQUEUE_REQUEST_CON_POOL_SIZE', 8)
                        )
                    else:
                        request = Request(con_pool_size=settings.TELEGRAMBOT.get('MESSAGEQUEUE_REQUEST_CON_POOL_SIZE', 8))
                    bot = MQBot(token, request=request, mqueue=q)
                else:
                    request = None
                    if proxy:
                        request = Request(proxy_url=proxy['proxy_url'], urllib3_proxy_kwargs=proxy['urllib3_proxy_kwargs'])
                    bot = telegram.Bot(token=token, request=request)

                BotConfig.ptb_dispatcher = Dispatcher(bot, None, workers=0)

                hookurl = f'{webhook_site}{f"/{webhook_base}" if webhook_base else ""}/{token}/'
                max_connections = settings.TELEGRAMBOT.get('WEBHOOK_MAX_CONNECTIONS', 40)
                drop_pending_updates = settings.TELEGRAMBOT.get('WEBHOOK_DROP_PENDING_UPDATES', False)
                secret_token = settings.TELEGRAMBOT.get('WEBHOOK_SECRET_TOKEN', None)

                setted = bot.setWebhook(
                    url=hookurl,
                    certificate=certificate,
                    timeout=timeout,
                    max_connections=max_connections,
                    allowed_updates=allowed_updates,
                    drop_pending_updates=drop_pending_updates,
                    secret_token=secret_token
                )
                webhook_info = bot.getWebhookInfo()
                real_allowed = webhook_info.allowed_updates if webhook_info.allowed_updates else ["ALL"]

                bot.more_info = webhook_info
                logger.info(
                    f'Telegram Bot <{bot.username}> '
                    f'setting webhook [ {webhook_info.url} ] '
                    f'max connections:{webhook_info.max_connections} '
                    f'allowed updates:{real_allowed} '
                    f'pending updates:{webhook_info.pending_update_count} : {setted}'
                )

            except InvalidToken:
                logger.error(f'Invalid Token : {token}')
                return
            except TelegramError as e:
                logger.error(f'Error : {repr(e)}')
                return

            # Notify bot is online to declared SUPERADMINS in settings
            for i in settings.TELEGRAMBOT.get('SUPERADMINS', []):
                bot.send_message(
                    i, f"{settings.APP_INFO.get('app_name', 'YaPtbDjango')}\nVer: {settings.APP_INFO.get('app_version', '0.x.x')}\nIs online\n/start",
                    parse_mode=ParseMode.HTML
                )



        else:  # POLLING MODE
            try:
                # https://github.com/python-telegram-bot/python-telegram-bot/wiki/Adding-defaults-to-your-bot
                # Set defaults
                defaults = Defaults(parse_mode=ParseMode.HTML, tzinfo=pytz.timezone('UTC'))

                updater = Updater(token=token, request_kwargs=proxy, defaults=defaults)
                bot = updater.bot
                bot.delete_webhook()
                BotConfig.ptb_updater = updater
                BotConfig.ptb_dispatcher = updater.dispatcher
            except InvalidToken:
                logger.error(f'Invalid Token : {token}')
                return
            except TelegramError as e:
                logger.error(f'Error : {repr(e)}')
                return

        # Set Bot
        BotConfig.ptb_bot = bot
        logger.debug(f'Telegram Bot <{BotConfig.ptb_bot.username}> set as default bot')

        def module_imported(module_name, method_name, execute):
            try:
                m = importlib.import_module(module_name)
                if execute and hasattr(m, method_name):
                    logger.debug(f'Run {module_name}.{method_name}()')
                    getattr(m, method_name)()
                else:
                    logger.debug(f'Run {module_name}')

            except ImportError as e:
                if settings.TELEGRAMBOT.get('STRICT_INIT'):
                    raise e
                else:
                    logger.error(f'{module_name} : {repr(e)}')
                    return False

            return True

        # import telegram bot handlers for all INSTALLED_APPS
        for app_config in apps.get_app_configs():
            if module_has_submodule(app_config.module, TELEGRAM_BOT_MODULE_NAME):
                module_name = f'{app_config.name}.{TELEGRAM_BOT_MODULE_NAME}'
                if module_imported(module_name, 'main', True):
                    logger.info(f'Loaded {module_name}')

        if self.mode == POLLING_MODE:
            updater = BotConfig.get_updater()

    logger.info('BotConfig READY')
