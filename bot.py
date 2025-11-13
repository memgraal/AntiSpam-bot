import asyncio
from aiogram import Bot, Dispatcher, F, types
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage

from config import TOKEN
from handlers.captcha import captcha_ok
from handlers.messages import handle_message
from handlers.admin_panel import router_admin

from middlewares.db_middleware import db_session_middleware
from middlewares.message_middleware import AuthorizedMessageMiddleware
from middlewares.bandword_middleware import CensorshipMiddleware
from middlewares.chat_id_middleware import GroupRegisterMiddleware


async def main():
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
    dp = Dispatcher(storage=MemoryStorage())

    # --- Middleware ---
    dp.update.middleware(db_session_middleware)
    dp.update.middleware(GroupRegisterMiddleware())
    dp.message.middleware(CensorshipMiddleware())
    dp.message.middleware(AuthorizedMessageMiddleware())

    # --- Callback-хендлеры ---
    dp.callback_query.register(captcha_ok, F.data.startswith("captcha_ok:"))

    # --- Подключаем админский роутер полностью ---
    dp.include_router(router_admin)

    # --- Все остальные текстовые сообщения ---
    dp.message.register(handle_message, F.text)

    print("🤖 Бот запущен...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
