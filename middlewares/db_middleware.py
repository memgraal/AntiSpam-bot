from database.models import Session

async def db_session_middleware(handler, event, data):
    # создаём сессию
    session = Session()
    data["session"] = session
    try:
        return await handler(event, data)
    finally:
        session.close()  # обязательно закрываем
