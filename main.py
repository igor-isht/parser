import time
import requests
import codecs
import json
import os
import telegram
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

URL = 'https://www.avito.ru/moskva/noutbuki?cd=1&q=macbook+air+m1&user=1'
PRICE = 65000  # цена, не больше этой
TIME = 60  # время между проверками, минут


def get_data(url):
    """Собственно парсер"""
    req = requests.get(url)
    if req.status_code != 200:
        print(f'Ошибка при запросе, код {req.status_code}')
    soup = BeautifulSoup(req.text, 'lxml')
    scr_list = soup.find_all(
        'div',
        class_='iva-item-root-_lk9K photo-slider-slider-S15A_ iva-item-list-rfgcH iva-item-redesign-rop6P iva-item-responsive-_lbhG items-item-My3ih items-listItem-Gd1jN js-catalog-item-enum'
    )

    try:
        with codecs.open('data.json', 'r', 'utf-8') as file:
            data = file.read()
    except OSError:
        data = []
    except Exception as error:
        print(f'Возникла ошибка: {error}')
    new_data = []

    for item in scr_list:
        price_item = item.find(class_='price-price-JP7qe').find('meta', attrs={"itemprop": "price"}).get('content')
        price_item = int(price_item)
        if price_item <= PRICE:
            url = 'https://www.avito.ru/' + item.find(class_='iva-item-sliderLink-uLz1v').get("href")
            description = item.find(
                class_='iva-item-text-Ge6dR iva-item-description-FDgK4 text-text-LurtD text-size-s-BxGpL'
            ).text
            if url not in data:
                new_data.append(
                    {
                        "url": url,
                        "price": price_item,
                        "description": description.replace('\n', ' ').encode().decode('utf-8')
                    }
                )

    if new_data:
        with codecs.open('data.json', 'a', encoding='utf-8') as file:
            json.dump(new_data, file, indent=4)
        return new_data
    return None


def send_message(bot, items):
    """Отправляем сообщения в чат"""
    bot.send_message(TELEGRAM_CHAT_ID, "Есть новые лоты, вот список:")
    time.sleep(1)
    for item in items:
        message = f" цена: {item.get('price')}\nописание: {item.get('description')}\nссылка: {item.get('url')}"
        bot.send_message(TELEGRAM_CHAT_ID, message)


def main():
    while True:
        items = get_data(URL)
        bot = telegram.Bot(token=TELEGRAM_TOKEN)
        if items is not None:
            send_message(bot, items)
        print('Я работаю!')  # чтобы не паниковать при работе парсера)
        time.sleep(TIME*60)


if __name__ == '__main__':
    main()
