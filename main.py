import requests
from bs4 import BeautifulSoup
import sqlite3

# div классы
download_class = "div.wVqUob:nth-child(2) > div.ClM7O"
score_class = ".TT9eCd"
review_class = ".EHUI5b"

def get_app_info(url):
    try:
        # отправляем get-запрос к указанной странице
        response = requests.get(url)
        response.raise_for_status()  # Проверяем статус код ответа

        # создаем объект beautifulsoup для парсинга html
        soup = BeautifulSoup(response.text, 'html.parser')

        # поиск информацию о приложении
        app_info = {}

        # название приложения
        app_info["name"] = soup.select_one("h1[itemprop='name']").get_text()

        # количество загрузок
        download_info = soup.select_one(download_class)
        if download_info:
            app_info["downloads"] = download_info.get_text()
        else:
            app_info["downloads"] = "Неизвестно"

        # средняя оценка
        score_info = soup.select_one(score_class)
        if score_info:
            app_info["rating"] = remove_star(score_info.get_text())
        else:
            app_info["rating"] = "Неизвестно"

        # количество отзывов
        review_info = soup.select_one(review_class)
        if review_info:
            app_info["reviews"] = remove_reviews(review_info.get_text())
        else:
            app_info["reviews"] = "Неизвестно"

        return app_info

    except requests.exceptions.RequestException as e:
        return f"Ошибка при выполнении запроса: {e}"
    except Exception as e:
        return f"Произошла ошибка: {e}"


# убираем  слово "star" из поля rating для удобства чтения
def remove_star(value):
    return value.replace("star", "")

# убираем  слово "reviews" из поля reviews для удобства чтения
def remove_reviews(value):
    return value.replace("reviews", "")


def main():
    try:
        # чтение входных данных из txt файла
        with open("gplay_urls.txt", "r") as file:
            input_data = [line.strip().split("\t") for line in file if len(line.strip()) > 0 and line.count("\t") == 1]

        # подключение к базе данных
        conn = sqlite3.connect("appdata.db")
        cursor = conn.cursor()

        # создание таблицы, если её ещё нет
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS elements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                domain TEXT,
                gplay_url TEXT,
                name TEXT,
                score TEXT,
                reviews TEXT,
                downloads TEXT
            )
        ''')

        # обработка каждой строки входных данных
        for domain, gplay_url in input_data:
            if not gplay_url.startswith("http://") and not gplay_url.startswith("https://"):
                gplay_url = "https://" + gplay_url

            app_info = get_app_info(gplay_url)

            # сохранение данных в базу данных
            cursor.execute("INSERT INTO elements (domain, gplay_url, name, downloads, score, reviews) VALUES (?, ?, ?, ?, ?, ?)",
                           (domain, gplay_url, app_info["name"], app_info["downloads"], app_info["rating"], app_info["reviews"]))
            conn.commit()

            print(f"Domain: {domain}, Google Play URL: {gplay_url}, App Info: {app_info}")

        # закрываем соединение с базой данных
        conn.close()

    except Exception as e:
        print(f"Произошла ошибка: {e}")

if __name__ == "__main__":
    main()
