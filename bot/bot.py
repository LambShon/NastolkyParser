from aiogram import Bot, Dispatcher, types, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
import asyncpg

API_TOKEN = "7945812652:AAEt9nhY6SlAT7mig8Jd2Yo9KGaUwB9LIM8"  # ТОКЕН

bot = Bot(token=API_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

class FilterStates(StatesGroup):
    choosing_filter = State()
    filtering_by_title = State()
    filtering_by_tags = State()

main_menu_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Фильтрация по названию"), KeyboardButton(text="Фильтрация по тегам")],
        [KeyboardButton(text="Выход")]
    ],
    resize_keyboard=True
)

back_menu_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Назад")],
    ],
    resize_keyboard=True
)

async def get_db_connection():
    return await asyncpg.connect(
        user="postgres_user",
        password="1234K7F",
        database="bredni_db",
        host="localhost"
    )

async def fetch_games_from_db(filter_title=None, filter_tags=None, offset=0):
    conn = await get_db_connection()
    try:
        query = """
            SELECT title, price, link, tags_num, tags FROM games
            WHERE TRUE
        """
        conditions = []
        params = []

        if filter_title:
            conditions.append("title ILIKE $1")
            params.append(f"%{filter_title}%")

        if filter_tags:
            if len(filter_tags.split()) == 2:
                oper, num = filter_tags.split()
                try:
                    if oper == "PlayerCount:":
                        filter_tags = str(num) + ","
                    elif oper == "AgeLimit:":
                        filter_tags = "," + str(num)
                    conditions.append("tags_num ILIKE $1")
                    params.append(f"%{filter_tags}%")
                except ValueError:
                    await message.answer("Ошибка: некорректное числовое значение. Попробуйте еще раз.")
                    return
            else:
                conditions.append("tags ILIKE $1")
                params.append(f"%{filter_tags}%")
                

        if conditions:
            query += " AND " + " AND ".join(conditions)
        
        query += " ORDER BY RANDOM() LIMIT 10"

        games = await conn.fetch(query, *params)
        return games
    finally:
        await conn.close()


@dp.message(F.text == "/start")
async def send_welcome(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Привет! Выберите фильтр:", reply_markup=main_menu_kb)

@dp.message(F.text == "Фильтрация по названию")
async def filter_by_title_start(message: Message, state: FSMContext):
    await state.set_state(FilterStates.filtering_by_title)
    await message.answer("Введите часть названия игры для фильтрации:", reply_markup=back_menu_kb)

@dp.message(F.text == "Фильтрация по тегам")
async def filter_by_tags_start(message: Message, state: FSMContext):
    await state.set_state(FilterStates.filtering_by_tags)
    await message.answer("Введите теги для фильтрации: \nПример: PlayerCount: 1-4 (или 2, 1-5, 2-5)\nПример: AgeLimit: 13+ \nИли один из тэгов: [Новинка, Дополнение, Хит, Предзаказ, Eng]", reply_markup=back_menu_kb)

@dp.message(FilterStates.filtering_by_title)
async def handle_title_filter(message: Message, state: FSMContext):
    if message.text == "Назад":
        await send_welcome(message, state)
        return

    title_part = message.text.strip()
    games = await fetch_games_from_db(filter_title=title_part)
    if not games:
        await message.answer("Ничего не найдено. Попробуйте еще раз.")
    else:
        response = "\n".join([f" {game['title']} - {game['price']}₽\nСсылка: {game['link']}" for game in games])
        await message.answer(response)
        await message.answer("Введите \"Назад\", чтобы вернуть или попробуйте приминить другие тэги")

@dp.message(FilterStates.filtering_by_tags)
async def handle_tags_filter(message: Message, state: FSMContext):
    if message.text == "Назад":
        await send_welcome(message, state)
        return

    tags_part = message.text.strip()

    games = await fetch_games_from_db(filter_tags=tags_part)
    if not games:
        await message.answer("Ничего не найдено. Попробуйте еще раз.")
    else:
        response = "\n".join([f"{game['title']} - {game['price']}₽\nСсылка: {game['link']}" for game in games])
        await message.answer(response)

@dp.message(F.text == "Выход")
async def cancel_action(message: Message, state: FSMContext):
    await message.answer("Бот прощается с вами и завершает свою работу ", reply_markup=types.ReplyKeyboardRemove())
    await dp.stop_polling() 

async def main():
    print("Бот запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
