# handlers/admin_panel.py
from aiogram import Router, F, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.filters import Command, StateFilter

from database.models import Session, Group, GroupSettings, BadWord

router_admin = Router()


# -------------------------
# FSM — добавление банворда
# -------------------------
class AddBadWordState(StatesGroup):
    waiting_for_word = State()


# -------------------------
# Клавиатура: список групп
# -------------------------
def groups_kb(groups):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=name, callback_data=f"group:{gid}")]
            for gid, name in groups
        ]
    )


# -------------------------
# Клавиатура: настройки группы
# -------------------------
def group_settings_kb(group_id: int, settings: dict) -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(
            text=f"🟢 Filter Badwords{' ✅' if settings.get('filter_badwords') else ''}",
            callback_data=f"toggle:filter:{group_id}"
        )],
        [InlineKeyboardButton(
            text=f"🟢 Welcome Message{' ✅' if settings.get('welcome_enabled') else ''}",
            callback_data=f"toggle:welcome:{group_id}"
        )],
        [InlineKeyboardButton(
            text=f"🟢 AI Filtering{' ✅' if settings.get('ai_filtering') else ''}",
            callback_data=f"toggle:ai:{group_id}"
        )],
        [InlineKeyboardButton(text="➕ Добавить банворд", callback_data=f"add_badword:{group_id}")],
        [InlineKeyboardButton(text="📜 Показать банворды", callback_data=f"show_badwords:{group_id}")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


# -------------------------
# Хендлеры
# -------------------------
async def admin_panel(message: types.Message):
    if message.chat.type != "private":
        return

    bot = message.bot
    username = message.from_user.username
    if not username:
        await message.answer("❗ У вас нет username в Telegram. Установите его в настройках профиля.")
        return

    with Session() as session:
        groups = session.query(Group.id, Group.chat_id).all()

    user_groups = []
    for gid, chat_id in groups:
        try:
            admins = await bot.get_chat_administrators(chat_id)
            if username in [a.user.username for a in admins if a.user.username]:
                chat = await bot.get_chat(chat_id)
                user_groups.append((gid, chat.title))
        except Exception:
            continue

    if not user_groups:
        await message.answer("❗ Вы не являетесь администратором ни в одной зарегистрированной группе.")
        return

    await message.answer("Выберите группу для управления:", reply_markup=groups_kb(user_groups))


async def group_selected(callback: types.CallbackQuery):
    group_id = int(callback.data.split(":")[1])

    with Session() as session:
        settings = session.query(GroupSettings).filter_by(group_id=group_id).first()
        if not settings:
            settings = GroupSettings(group_id=group_id)
            session.add(settings)
            session.commit()

        settings_data = {
            "filter_badwords": settings.filter_badwords,
            "welcome_enabled": settings.welcome_enabled,
            "ai_filtering": settings.ai_filtering
        }

    await callback.message.edit_text(
        f"⚙️ Управление группой (ID: {group_id})",
        reply_markup=group_settings_kb(group_id, settings_data)
    )
    await callback.answer()


async def toggle_settings(callback: types.CallbackQuery):
    group_id = int(callback.data.split(":")[2])
    setting = callback.data.split(":")[1]

    with Session() as session:
        settings = session.query(GroupSettings).filter_by(group_id=group_id).first()
        if not settings:
            await callback.answer("Настройки группы не найдены.", show_alert=True)
            return

        if setting == "filter":
            settings.filter_badwords = not settings.filter_badwords
        elif setting == "welcome":
            settings.welcome_enabled = not settings.welcome_enabled
        elif setting == "ai":
            settings.ai_filtering = not settings.ai_filtering

        session.commit()

        settings_data = {
            "filter_badwords": settings.filter_badwords,
            "welcome_enabled": settings.welcome_enabled,
            "ai_filtering": settings.ai_filtering
        }

    await callback.message.edit_reply_markup(reply_markup=group_settings_kb(group_id, settings_data))
    await callback.answer("✅ Настройки обновлены")


async def add_badword(callback: types.CallbackQuery, state: FSMContext):
    group_id = int(callback.data.split(":")[1])
    await state.update_data(group_id=group_id)
    await state.set_state(AddBadWordState.waiting_for_word)
    await callback.message.answer("✏️ Введите слово для добавления в бан-лист:")
    await callback.answer()


async def add_badword_reply(message: types.Message, state: FSMContext):
    data = await state.get_data()
    group_id = data.get("group_id")
    word = (message.text or "").strip().lower()

    if not word:
        await message.answer("❗ Введите непустое слово.")
        return

    with Session() as session:
        if session.query(BadWord).filter_by(group_id=group_id, word=word).first():
            await message.answer(f"⚠️ Слово «{word}» уже есть в бан-листе.")
        else:
            session.add(BadWord(group_id=group_id, word=word))
            session.commit()
            await message.answer(f"✅ Слово «{word}» добавлено в бан-лист.")

    await state.clear()


async def show_badwords(callback: types.CallbackQuery):
    group_id = int(callback.data.split(":")[1])

    with Session() as session:
        words = session.query(BadWord).filter_by(group_id=group_id).order_by(BadWord.id).all()

    if not words:
        await callback.answer("📭 Бан-лист пуст.", show_alert=True)
        return

    text = "🚫 Банворды:\n" + "\n".join(f"{i+1}. {w.word}" for i, w in enumerate(words))
    await callback.message.answer(text)
    await callback.answer()


# -------------------------
# Регистрация всех хендлеров через функцию
# -------------------------
def register_admin_handlers(router: Router):
    router.message.register(admin_panel, Command("admin"))
    router.callback_query.register(group_selected, F.data.startswith("group:"))
    router.callback_query.register(toggle_settings, F.data.startswith("toggle:"))
    router.callback_query.register(add_badword, F.data.startswith("add_badword:"))
    router.message.register(add_badword_reply, StateFilter(AddBadWordState.waiting_for_word))
    router.callback_query.register(show_badwords, F.data.startswith("show_badwords:"))


# Регистрируем роутер при импорте
register_admin_handlers(router_admin)
