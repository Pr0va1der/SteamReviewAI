import re
import requests

def extract_app_id(game_url):
    match = re.search(r'/app/(\d+)/', game_url)
    return match.group(1) if match else None

def check_game_exists(app_id):
    url = f"https://store.steampowered.com/api/appdetails?appids={app_id}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            return data.get(app_id, {}).get("success", False)
    except Exception as e:
        print(f"Ошибка проверки игры в Steam: {e}")
    return False

def format_text(text):
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'^### (.*)', r'<h3>\1</h3>', text, flags=re.MULTILINE)
    return text

