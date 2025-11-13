from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database.models import ChatUser


async def send_captcha(bot, message: types.Message):
    if message.chat.type not in ("group", "supergroup"):
        return

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Я не бот",
                    callback_data=f"captcha_ok:{message.from_user.username}",
                )
            ]
        ]
    )

    await bot.send_message(
        chat_id=message.chat.id,
        text=f"Привет, {message.from_user.first_name}! Подтверди, что ты не бот 👇",
        reply_markup=kb,
    )


async def captcha_ok(callback: types.CallbackQuery, session):
    if callback.message.chat.type not in ("group", "supergroup"):
        await callback.answer("Капча доступна только в группах", show_alert=True)
        return

    username = callback.data.split(":")[1]
    db_user = session.query(ChatUser).filter_by(username=username).first()

    if not db_user:
        await callback.answer("Пользователь не найден. Напиши снова в чат.")
        return

    db_user.is_verified = True
    session.commit()

    await callback.message.edit_text("✅ Капча успешно пройдена! Добро пожаловать!")
    await callback.answer("Спасибо, подтверждение пройдено ✅", show_alert=True)
