import logging

from django.core.management.base import BaseCommand

from bot.apps import BotConfig


# Original code
# https://github.com/JungDev/django-telegrambot/blob/master/django_telegrambot/management/commands/botpolling.py

class Command(BaseCommand):
    help = "Run telegram bot in polling mode"
    can_import_settings = True

    def add_arguments(self, parser):
        parser.add_argument('--username', '-i', help="Bot username", default=None)
        parser.add_argument('--token', '-t', help="Bot token", default=None)
        pass

    def get_updater(self, username=None, token=None):
        updater = None
        if username is not None:
            updater = BotConfig.get_updater()
            if not updater:
                self.stderr.write("Cannot find default bot with username {}".format(username))
        elif token:
            updater = BotConfig.get_updater()
            if not updater:
                self.stderr.write("Cannot find bot with token {}".format(token))
        return updater

    def handle(self, *args, **options):
        from django.conf import settings
        from telegram.ext import Updater
        if settings.TELEGRAMBOT.get('MODE', 'WEBHOOK') == 'WEBHOOK':
            self.stderr.write("Webhook mode active in settings.py, change in POLLING if you want use polling update")
            return

        updater: Updater = self.get_updater(username=options.get('username'), token=options.get('token'))
        if not updater:
            self.stderr.write("Bot not found")
            return
        # Enable Logging
        logging.basicConfig(
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            level=logging.INFO
        )
        logger = logging.getLogger("telegrambot")
        logger.setLevel(logging.DEBUG)
        console = logging.StreamHandler()
        console.setLevel(logging.DEBUG)
        console.setFormatter(logging.Formatter('%(name)s - %(levelname)s - %(message)s'))
        logger.addHandler(console)

        bot_set = settings.TELEGRAMBOT.get('TOKEN', None)
        if bot_set is None:
            self.stderr.write("Cannot find bot settings")
            return

        allowed_updates = settings.TELEGRAMBOT.get('ALLOWED_UPDATES', None)
        timeout = settings.TELEGRAMBOT.get('TIMEOUT', 10)
        poll_interval = settings.TELEGRAMBOT.get('POLL_INTERVAL', 0.0)
        clean = settings.TELEGRAMBOT.get('POLL_CLEAN', False)
        bootstrap_retries = settings.TELEGRAMBOT.get('POLL_BOOTSTRAP_RETRIES', -1)
        read_latency = settings.TELEGRAMBOT.get('POLL_READ_LATENCY', 2.0)

        self.stdout.write("Run polling...")
        updater.start_polling(
            poll_interval=poll_interval,
            timeout=timeout,
            drop_pending_updates=clean,
            bootstrap_retries=bootstrap_retries,
            read_latency=read_latency,
            allowed_updates=allowed_updates
        )
        self.stdout.write("the bot is started and runs until we press Ctrl-C on the command line.")

        # Notify bot is online to declared SUPERADMINS in settings
        for i in settings.TELEGRAMBOT.get('SUPERADMINS', []):
            updater.bot.send_message(
                i, f"{settings.APP_INFO.get('app_name', 'YaPtbDjango')}\nVer: {settings.APP_INFO.get('app_version', '0.x.x')}\nis online\n/start"
            )

        updater.idle()
