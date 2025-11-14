import os
from typing import Callable, Dict, Any, Awaitable


from aiogram import BaseMiddleware, types
from dotenv import load_dotenv
from pydantic import BaseModel, Field
import pymorphy3

from config import BANNED_WORDS

load_dotenv()


morph = pymorphy3.MorphAnalyzer()


class CensorshipMiddleware(BaseMiddleware):

    async def __call__(
        self,
        handler: Callable[[types.Message, Dict[str, Any]], Awaitable[Any]],
        event: types.Message,
        data: Dict[str, Any],
    ) -> Any:

        if event.chat.type not in ("group", "supergroup"):
            return await handler(event, data)

        text = (event.text or "").lower()
        words = text.split()

        for word in words:
            lemma = morph.parse(word)[0].normal_form
            for banned in BANNED_WORDS:
                if banned in lemma:
                    await event.delete()
                    return

        return await handler(event, data)
