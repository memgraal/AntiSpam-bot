from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware, types
from database.models import Group, Session


class GroupRegisterMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[types.Message, Dict[str, Any]], Awaitable[Any]],
        event: types.Update,
        data: Dict[str, Any],
    ) -> Any:

        # Проверяем, что пришло сообщение
        message = getattr(event, "message", None)
        if not message:
            return await handler(event, data)

        chat = message.chat
        if chat.type not in ("group", "supergroup"):
            return await handler(event, data)

        chat_id = chat.id

        # Добавляем в базу, если нет
        with Session() as session:
            group = session.query(Group).filter_by(chat_id=chat_id).first()
            if not group:
                group = Group(chat_id=chat_id)
                session.add(group)
                session.commit()

        return await handler(event, data)
