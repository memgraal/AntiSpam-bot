from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware, types
from database.models import ChatUser
from handlers.captcha import send_captcha


class AuthorizedMessageMiddleware(BaseMiddleware):

    async def __call__(
        self,
        handler: Callable[[types.Message, Dict[str, Any]], Awaitable[Any]],
        event: types.Message,
        data: Dict[str, Any],
    ) -> Any:

        session = data.get("session")
        user = event.from_user

        if not user:
            return await handler(event, data)

        if event.chat.type not in ("group", "supergroup"):
            return await handler(event, data)

        if event.sticker and event.sticker.emoji in ("🔞", "🍓"):
            await event.delete()
            return

        username = user.username or f"id_{user.id}"
        chat_id = event.chat.id

        if ChatUser.is_user_banned(session, username):
            await event.delete()
            return

        db_user = session.query(ChatUser).filter_by(username=username).first()

        if not db_user:
            db_user = ChatUser(
                username=username,
                is_verified=False,
                is_banned=False,
                is_captcha_sent=False,
                group_id=chat_id,
            )
            session.add(db_user)
            session.commit()
            await event.delete()

        if not db_user.is_verified and not db_user.is_captcha_sent:
            await send_captcha(event.bot, event)
            db_user.is_captcha_sent = True
            db_user.group_id = chat_id
            session.commit()
            return

        if not db_user.is_verified:
            await event.delete()
            return

        return await handler(event, data)
