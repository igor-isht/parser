import asyncio
import os

from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import State, StatesGroup
from dotenv import load_dotenv

import parser
from middlewares import AccessMiddleware


load_dotenv()
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

URL = None  # Ссылка на страницу с объявлениями
PRICE = 0   # цена, не больше этой
TIME = 60   # время между проверками, минут

bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())
dp.middleware.setup(AccessMiddleware(TELEGRAM_CHAT_ID))


class SearchParameters(StatesGroup):
    url = State()
    price = State()


@dp.message_handler(commands=['start', 'help'])
async def send_welcome(message: types.Message):
    await message.answer(f"Привет!\nЯ парсер-бот!\nОпрашиваю сайт каждые {TIME} минут\n"
                         "Для начала работы укажите параметры поиска командой /search\n"
                         "Проверить настройки поиска: /my_setting")


@dp.message_handler(commands=['search'], state="*")
async def search_start(message: types.Message, state: FSMContext):
    await message.answer("Введите URL-адрес для поиска, либо /cancel для отмены")
    await state.set_state(SearchParameters.url.state)


@dp.message_handler(commands=['cancel'], state="*")
@dp.message_handler(Text(equals='cancel', ignore_case=True), state='*')
async def cancel_search(message: types.Message, state: FSMContext):
    await state.finish()
    global URL, PRICE
    URL = None
    PRICE = 0
    await message.answer("Поиск отменен")


@dp.message_handler(state=SearchParameters.url)
async def get_url(message: types.Message, state: FSMContext):

    try:
        req = parser.get_request(message.text)
        if req.status_code != 200:
            await message.answer("URL неверный. Введите корректный адрес")
            return await search_start()
    except Exception:
        await message.answer("URL неверный. Введите корректный адрес")
        await search_start()

    await state.update_data(url=message.text)
    await message.answer("Введите максимальную цену, либо /cancel для отмены")
    await state.set_state(SearchParameters.price.state)


@dp.message_handler(lambda message: not message.text.isdigit(), state=SearchParameters.price)
async def get_price(message: types.Message, state: FSMContext):
    return await message.reply("Введите число")


@dp.message_handler(lambda message: message.text.isdigit(), state=SearchParameters.price)
async def get_price(message: types.Message, state: FSMContext):
    await state.update_data(price=int(message.text))

    user_data = await state.get_data()
    global URL, PRICE
    URL, PRICE = user_data.get('url'), user_data.get('price')
    await message.answer("Начинаю поиск...\nпоиск можно остановить командой /cancel")
    await state.finish()

    while URL:
        items = parser.get_data(URL, PRICE)
        if items is not None:
            await send_message(items)

        await asyncio.sleep(TIME*60)


@dp.message_handler(commands=['my_setting'])
async def my_setting(message: types.Message):
    await message.answer(f'URL: {URL}\nцена: {PRICE}')
    await message.answer("/search - новый поиск")


async def send_message(items):
    await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text="Есть новые лоты, вот список:")
    for item in items:
        message = f" цена: {item.get('price')}\nописание: {item.get('description')}\nссылка: {item.get('url')}"
        await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)


if __name__ == '__main__':

    executor.start_polling(dp, skip_updates=True)
