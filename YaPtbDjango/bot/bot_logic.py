import logging

from django.conf import settings
from telegram import ParseMode, Update
from telegram.error import (BadRequest, ChatMigrated, NetworkError, TelegramError, TimedOut, Unauthorized)
from telegram.ext import CallbackContext, Filters, MessageHandler

from .apps import BotConfig
from .models import HistoryTelegramUser, TelegramUser

logger = logging.getLogger(__name__)

#
MessagesTypes = HistoryTelegramUser.MessagesTypes


def is_admin(user_id):
    """Is telegram admin? """
    return True if user_id in settings.TELEGRAMBOT.get('SUPERADMINS', None) else False


def process_call(update: Update, context: CallbackContext, message_type: MessagesTypes.UNKNOWN) -> TelegramUser:
    """Process call and register Django data about telegram user, including history

    return: tg_user_data (all Django record)
    """
    # Create if telegram user doesn't exists or get record and return
    tg_user_data = None

    try:
        tg_user_data, created = TelegramUser.objects.update_or_create(
            user_id=update.effective_user.id,
            defaults={
                'username': update.effective_user.username,
                'first_name': update.effective_user.first_name,
                'last_name': update.effective_user.last_name
            },
        )

        # Register history
        HistoryTelegramUser.objects.create(
            tg_user=tg_user_data,
            message_type=message_type,
            data=(update.effective_message.text
                  if (message_type == MessagesTypes.TEXT or message_type == MessagesTypes.CMD) else
                  update.effective_message.dice
                  if message_type == MessagesTypes.DICE else MessagesTypes.UNKNOWN),
            full_update_data=update
        )

    except BaseException as e:
        print(repr(e))
        pass

    return tg_user_data


def tg_text(update: Update, context: CallbackContext):
    """Listening text... and send echo"""

    # Process this telegram call and register Django data about this command
    tg_user_data = process_call(update, context, message_type=MessagesTypes.TEXT)

    context.bot.send_message(
        chat_id=tg_user_data.user_id,
        text=update.effective_message.text,
        parse_mode=ParseMode.HTML
    )


def tg_dice(update: Update, context: CallbackContext):
    """Listening dice... and response"""

    # Process this telegram call and register Django data about this command
    tg_user_data = process_call(update, context, message_type=MessagesTypes.DICE)

    context.bot.send_dice(
        chat_id=tg_user_data.user_id,
        emoji=update.effective_message.dice['emoji']
    )


def tg_cmd(update: Update, context: CallbackContext):
    """Listening commands.."""

    # Process this telegram call and register Django data about this command
    tg_user_data = process_call(update, context, message_type=MessagesTypes.CMD)

    # Sanitize cmd
    cmd = update.effective_message.text.split()[0].lower()
    cmd = cmd.split("@")[0]

    text = update.effective_message.text

    # Check if ADMIN commands
    if is_admin(tg_user_data.user_id):
        logger.debug(f"Admin access: {tg_user_data.user_id} - @{tg_user_data.username} - {text}")
        if cmd == "/admin":
            msg = f"{tg_user_data.first_name}, /admin command, only for admin"
            context.bot.send_message(
                chat_id=tg_user_data.user_id,
                text=f"<b>Admin Message</b>\n{msg}",
                parse_mode=ParseMode.HTML
            )
            return

    # Example: /me
    if cmd in ["/me"]:
        context.bot.send_message(
            chat_id=tg_user_data.user_id,
            text=(
                f"<b>user_id</b>: {tg_user_data.user_id}\n"
                f"<b>first_name</b>: {tg_user_data.first_name}\n"
                f"<b>last_name</b>: {tg_user_data.last_name}\n"
                f"<b>username</b>: {tg_user_data.username}\n"
                f"<b>created (Django Db)</b>: {tg_user_data.created}\n"
                f"<b>updated (Django Db)</b>: {tg_user_data.updated}\n"
                f"<b>Is telegram admin? (Django SETTINGS)</b>: {'Yes' if is_admin(tg_user_data.user_id) else 'No'}\n"
            ),
            parse_mode=ParseMode.HTML
        )
        return

    # Example: /help /h
    if cmd in ["/help", "/h"]:
        context.bot.send_message(
            chat_id=tg_user_data.user_id,
            text=f"{tg_user_data.first_name}, <b>HELP</b> command.",
            parse_mode=ParseMode.HTML
        )
        return

    # Example: /start /restart
    if cmd in ["/start", "/restart"]:
        context.bot.send_message(
            chat_id=tg_user_data.user_id,
            text=f"{tg_user_data.first_name}, <b>START, RESTART</b> command.\n\nWelcome to {settings.APP_INFO.get('name', 'YaPtbDjango: Yet another Python Telegram Bot with Django')}",
            parse_mode=ParseMode.HTML
        )
        return


# ERROR CONTROL
def errors(update: Update, context: CallbackContext):
    """Log Errors caused by Updates.
    https://github.com/python-telegram-bot/python-telegram-bot/wiki/Exception-Handling
    """
    try:
        raise context.error
    except Unauthorized:  # User has blocked the Bot
        logger.error(f"ERROR Unauthorized {update}")

    except BadRequest:
        # handle malformed requests - read more below!
        # print("ERROR BadRequest", update)
        logger.error(f"ERROR BadRequest {update}")

    except TimedOut:
        # handle slow connection problems
        # print("ERROR TimedOut", update)
        logger.error(f"ERROR TimedOut {update}")

    except NetworkError:
        # handle other connection problems
        # print("ERROR NetworkError", update)
        logger.error(f"ERROR NetworkError {update}")

    except ChatMigrated as e:
        # the chat_id of a group has changed, use e.new_chat_id instead
        # print("ERROR ChatMigrated", e, update)
        logger.error(f"ERROR ChatMigrated {update}")

    except TelegramError:
        # handle all other telegram related errors
        # print("ERROR TelegramError", update)
        logger.error(f"ERROR TelegramError {update}")


def main():
    """Main"""

    logger.info("Loading handlers for telegram bot")

    # Default dispatcher
    dp = BotConfig.dispatcher

    # ALL Commands Handler
    dp.add_handler(MessageHandler(Filters.command, tg_cmd))

    # ALL Text Handler
    dp.add_handler(MessageHandler(Filters.text, tg_text))

    # ALL DICE Handler
    dp.add_handler(MessageHandler(Filters.dice, tg_dice))

    # log all errors
    dp.add_error_handler(errors)
