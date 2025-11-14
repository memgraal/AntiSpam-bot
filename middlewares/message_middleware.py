from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware, types
from database.models import ChatUser  # Предполагается, что ChatUser имеет поля username и group_id
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
        chat_id = event.chat.id

        # 1. Пропускаем, если нет пользователя (например, системные сообщения без отправителя)
        if not user:
            return await handler(event, data)

        # 2. Пропускаем все личные чаты (private), чтобы не блокировать /admin
        if event.chat.type not in ("group", "supergroup"):
            return await handler(event, data)

        # Мы находимся в группе/супергруппе
        username = user.username or f"id_{user.id}"

        # 3. Фильтрация стикеров
        if event.sticker and event.sticker.emoji in ("🔞", "🍓"):
            await event.delete()
            return

        # 4. Проверка на глобальный бан (если ChatUser.is_user_banned проверяет по username)
        if ChatUser.is_user_banned(session, username):
            await event.delete()
            return

        # 5. 🟢 ИСПРАВЛЕНИЕ: Ищем пользователя по связке username И group_id
        db_user = session.query(ChatUser).filter_by(
            username=username,
            group_id=chat_id  # Добавляем фильтр по group_id
        ).first()

        # 6. Если пользователь новый в этой группе - регистрируем
        if not db_user:
            db_user = ChatUser(
                username=username,
                is_verified=False,
                is_banned=False,
                is_captcha_sent=False,
                group_id=chat_id,  # Устанавливаем group_id
            )
            session.add(db_user)
            session.commit()
            await event.delete()  # Удаляем первое сообщение от неавторизованного пользователя

            # 7. Отправляем капчу сразу после регистрации
            await send_captcha(event.bot, event)
            db_user.is_captcha_sent = True
            session.commit()
            return

        # 8. Если пользователь зарегистрирован, но не верифицирован, и капча еще не отправлена
        if not db_user.is_verified and not db_user.is_captcha_sent:
            await send_captcha(event.bot, event)
            db_user.is_captcha_sent = True
            session.commit()
            return

        # 9. Если пользователь зарегистрирован, но не верифицирован (и капча уже отправлена)
        if not db_user.is_verified:
            await event.delete()
            return

        # 10. Пользователь верифицирован, пропускаем сообщение
        return await handler(event, data)