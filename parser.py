import requests
from bs4 import BeautifulSoup
from hyper.contrib import HTTP20Adapter


def get_request(url):
    """ Функция делает запрос к url. """
    req = requests.Session()
    req.mount('https://', HTTP20Adapter())
    headers = {
        'User-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36',
    }
    return req.get(url, headers=headers)


def get_data(url, price):
    """ Собственно парсер. Сравнивает полученные данные с имеющимися (в data.txt),
    при наличии новых данных записывает в файл и возвращает их. """

    req = get_request(url)

    soup = BeautifulSoup(req.text, 'lxml')
    scr_list = soup.find_all(
        'div',
        class_='iva-item-root-_lk9K photo-slider-slider-S15A_ iva-item-list-rfgcH iva-item-redesign-rop6P iva-item-responsive-_lbhG items-item-My3ih items-listItem-Gd1jN js-catalog-item-enum'
    )

    try:
        with open('data.txt', 'r', encoding='utf-8') as file:
            data = file.read()
    except OSError:
        data = []
    except Exception as error:
        print(f'Возникла ошибка: {error}')
    new_data = []
    new_data_base = []

    for item in scr_list:
        price_item = item.find(class_='price-price-JP7qe').find('meta', attrs={"itemprop": "price"}).get('content')
        price_item = int(price_item)
        if price_item <= price:
            url = 'https://www.avito.ru' + item.find(class_='iva-item-sliderLink-uLz1v').get("href")
            try:
                description = item.find(
                    class_='iva-item-text-Ge6dR iva-item-description-FDgK4 text-text-LurtD text-size-s-BxGpL'
                ).text
            except AttributeError:
                description = 'Без описания'
            if url not in data:
                new_data.append(
                    {
                        "url": url,
                        "price": price_item,
                        "description": description.replace('\n', ' ').encode().decode('utf-8')
                    }
                )
                new_data_base.append(
                    {
                        "url": url,
                        "price": price_item,
                    }
                )

    if new_data:
        with open('data.txt', 'a', encoding='utf-8') as file:
            for data in new_data_base:
                file.write(str(data) + '\n')
        return new_data
    return None
