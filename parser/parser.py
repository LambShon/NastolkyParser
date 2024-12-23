import requests
from bs4 import BeautifulSoup
import psycopg2
import os


DB_CONFIG = {
    "dbname": os.getenv("POSTGRES_DB", "bredni_db"),
    "user": os.getenv("POSTGRES_USER", "postgres_user"),
    "password": os.getenv("POSTGRES_PASSWORD", "1234K7F"),
    "host": os.getenv("POSTGRES_HOST", "localhost"),
    "port": os.getenv("POSTGRES_PORT", 5432)
}

    
def db_conection():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        print(f"ошибка подключения к БД: {e}")
        return None
    

def save_games_to_db(games_list):
    conn = db_conection()
    if not conn:
        print("Ошибка: подключение к базе данных отсутствует. Завершаем выполнение.")
        return

    try:
        with conn.cursor() as cur:
            for game in games_list:
                cur.execute("""
                    INSERT INTO games (title, price, link, tags_num, tags)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (link) DO UPDATE SET
                        title = EXCLUDED.title,
                        price = EXCLUDED.price,
                        tags_num = EXCLUDED.tags_num,
                        tags = EXCLUDED.tags
                    """, (game["title"], game["price"], game["link"], game["tags_num"], game["tags"]))
                conn.commit()
    except Exception as e:
        print(f"Ошибка сохранения в бд: {e}")
    finally:
        conn.close()




def parse_game(game):
    not_title = game.find("div", class_="product-card-title")
    title = not_title.get_text(strip=True)
    link = not_title.find("a").get('href')
        
    price_now = game.find("div", class_="product-card-price").get_text(strip=False)
        
    tags = game.find("div", class_="product-card__tags").get_text(strip=False)

    price_now = price_now.split()
    price = ""
    for x in price_now:
        if (x == "₽"):
            break
        price += x
        
    tags_list = tags.split()
    tags_list_num = []
    tags_list_str = []
    for tag in tags_list:
        if (tag == "Новинка" or tag == "Дополнение" or tag == "Хит" or tag == "Предзаказ" or tag == "Eng"):
            tags_list_str.append(tag)
        else:
            tags_list_num.append(tag)
    tags_list_num = ",".join(tags_list_num)
    tags_list_str = ",".join(tags_list_str)
    price = int(price)


    return {"title": title, "price": price, "link": link, "tags_num": tags_list_num, "tags": tags_list_str}



def parse_all():
    base_url = "https://hobbygames.ru/nastolnie"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.45 Safari/537.36"
    }
    page_number = 1
    game_list = []

    while page_number < 50:
        url = f"{base_url}?page={page_number}"
        response = requests.get(url, headers=headers)
    
        if response.status_code != 200:
            print(f"Ошибка при запросе страницы {page_number}.")
            break
    
        soup = BeautifulSoup(response.text, "lxml")
    
        games = soup.find_all("div", class_="product-card")
    
        if not games:
            print(f"На странице {page_number} не найдено игр.")
            break
            
        
        for game in games:
            game_list.append(parse_game(game))
        
        page_number += 1

    save_games_to_db(game_list)

def main():
    parse_all()



if __name__ == "__main__":
    main()