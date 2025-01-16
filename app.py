from flask import Flask, request, jsonify, render_template
from get_review import process_game_reviews
from filter_ai import search_games
import re
import requests

def extract_app_id(game_url):
    # Регулярное выражение для извлечения app_id
    match = re.search(r'/app/(\d+)/', game_url)
    if match:
        return match.group(1)  # Возвращаем только app_id
    return None

def check_game_exists(app_id):
    """
    Проверяет, существует ли игра в Steam на основе app_id.
    """
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
    """
    Функция для замены **текст** на <strong>текст</strong> и ###заголовок### на <h3>заголовок</h3>.
    """
    # Заменяем **текст** на <strong>текст</strong>
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    
    # Заменяем ###заголовок### на <h3>заголовок</h3>
    text = re.sub(r'^### (.*)', r'<h3>\1</h3>', text, flags=re.MULTILINE)
    
    return text

app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process():
    try:
        game_url = request.form.get('game_url')
        limit = int(request.form.get('limit', 1000))

        if not game_url:
            return jsonify({"error": "URL игры обязателен!"}), 400

        # Извлечение app_id из game_url
        app_id = extract_app_id(game_url)
        if not app_id:
            return jsonify({"error": "Неверный URL игры!"}), 400

        # Обработка отзывов
        raw_result = process_game_reviews(app_id, limit)

        # Преобразуем текст с учётом форматирования
        formatted_result = format_text(raw_result)

        return jsonify({"success": True, "review": formatted_result})
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        print(f"Ошибка на сервере: {e}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500


@app.route("/search_games", methods=["POST"])
def search_games_route():
    tags = request.data.decode("utf-8")  # Получаем текст как есть
    
    if not tags.strip():
        return "Теги не указаны", 400
    
    games_result = search_games(tags)  # Отправляем текст в search_games
    
    #if not games_result.strip():
    #    return "Игры не найдены", 404
    
     # Генерируем HTML-таблицу
    result = """
    <table style="width: 100%; border-collapse: collapse;">
        <thead>
            <tr style="background-color: #f2f2f2;">
                <th style="border: 1px solid #ddd; padding: 8px;">Название</th>
                <th style="border: 1px solid #ddd; padding: 8px;">Цена</th>
                <th style="border: 1px solid #ddd; padding: 8px;">Ссылка</th>
                <th style="border: 1px solid #ddd; padding: 8px;">Метки</th>
            </tr>
        </thead>
        <tbody>
    """
    
    for game in games_result:
        result += f"""
            <tr>
                <td style="border: 1px solid #ddd; padding: 8px;">{game['Название']}</td>
                <td style="border: 1px solid #ddd; padding: 8px;">{game['Цена']}</td>
                <td style="border: 1px solid #ddd; padding: 8px;">
                    <a href="{game['Ссылка']}" target="_blank" style="color: #007bff;">Открыть</a>
                </td>
                <td style="border: 1px solid #ddd; padding: 8px;">{', '.join(game['Метки'])}</td>
            </tr>
        """
    
    result += """
        </tbody>
    </table>
    """
    
    return result, 200, {"Content-Type": "text/html; charset=utf-8"}


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)