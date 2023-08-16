import requests
from bs4 import BeautifulSoup
import sqlite3
import datetime

download_class = "div.wVqUob:nth-child(2) > div.ClM7O"
score_class = ".TT9eCd"
review_class = ".EHUI5b"

def convert_to_number(value):
    if value.endswith("k"):
        return int(float(value[:-1]) * 1000)
    elif value.endswith("m+"):
        return int(float(value[:-2]) * 1000000)
    elif value.replace(".", "", 1).isdigit():
        return int(float(value.replace(".", "")))
    else:
        return value

def remove_star_from_rating(value):
    return value.replace(" star", "")

def get_app_info(url):
    try:
        # Отправляем GET-запрос к указанной странице
        response = requests.get(url)
        response.raise_for_status()  # Проверяем статус код ответа

        # Создаем объект BeautifulSoup для парсинга HTML
        soup = BeautifulSoup(response.text, 'html.parser')

        # Ищем информацию о приложении
        app_info = {}

        # Название приложения
        app_info["name"] = soup.select_one("h1[itemprop='name']").get_text()

        # Количество загрузок
        download_info = soup.select_one("div.wVqUob:nth-child(2) > div.ClM7O")
        if download_info:
            app_info["downloads"] = convert_to_number(download_info.get_text())
        else:
            app_info["downloads"] = "Неизвестно"

        # Количество отзывов
        score_info = soup.select_one("div.wVqUob:nth-child(1) > div.ClM7O")
        if score_info:
            app_info["rating"] = remove_star_from_rating(score_info.get_text())
        else:
            app_info["rating"] = "Неизвестно"

        # Количество загрузок
        review_info = soup.select_one(review_class)
        if review_info:
            app_info["reviews"] = convert_to_number(review_info.get_text())
        else:
            app_info["reviews"] = "Неизвестно"

        return app_info

    except requests.exceptions.RequestException as e:
        return f"Ошибка при выполнении запроса: {e}"
    except Exception as e:
        return f"Произошла ошибка: {e}"

def create_table():
    conn = sqlite3.connect('app_data.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS elements (
                      id INTEGER PRIMARY KEY AUTOINCREMENT,
                      domain TEXT,
                      gplay_url TEXT,
                      name TEXT,
                      score REAL,
                      reviews INTEGER,
                      downloads INTEGER,
                      data_date TEXT)''')
    conn.commit()
    conn.close()

def insert_app_data(domain, gplay_url, app_data):
    conn = sqlite3.connect('app_data.db')
    cursor = conn.cursor()

    current_date = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    cursor.execute('''INSERT OR REPLACE INTO elements (domain, gplay_url, name, score, reviews, downloads, data_date)
                      VALUES (?, ?, ?, ?, ?, ?, ?)''', (
        domain,
        gplay_url,
        app_data["name"],
        app_data["rating"],
        app_data["reviews"],
        app_data["downloads"],
        current_date,
    ))

    conn.commit()
    conn.close()

def main():
    try:
        create_table()

        with open("gplay_urls.txt", "r") as file:
            input_data = [line.strip().split("\t") for line in file if len(line.strip()) > 0 and line.count("\t") == 1]

        for domain, gplay_url in input_data:
            if not gplay_url.startswith("http://") and not gplay_url.startswith("https://"):
                gplay_url = "https://" + gplay_url

            app_info = get_app_info(gplay_url)
            print(f"Domain: {domain}, Google Play URL: {gplay_url}, App Info: {app_info}")

            if isinstance(app_info, dict):
                insert_app_data(domain, gplay_url, app_info)
                print(f"Данные сохранены в базу данных.")
            else:
                print(app_info)  # Выводим сообщение об ошибке

    except Exception as e:
        print(f"Произошла ошибка: {e}")

if __name__ == "__main__":
    main()
