from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.http import JsonResponse, HttpResponse, HttpResponseBadRequest
from django.utils.translation import get_language
import json
from django.shortcuts import render
from core.utils import extract_app_id, format_text, check_game_exists
import asyncio
from .get_review import process_game_reviews
from .filter_ai import search_games
import markdown

page_language = get_language()  # Это 'en' или 'ru', в зависимости от текущего языка

def index(request):
    return render(request, 'index.html')

@csrf_exempt
@require_POST
def process(request):
    try:
        game_url = request.POST.get('game_url', "").strip()
        limit = request.POST.get('limit', "").strip()

        if not game_url:
            return JsonResponse({"error": "Ошибка: пустое поле/неверный запрос"}, status=400)

        if not limit.isdigit() or int(limit) <= 0:
            return JsonResponse({"error": "Ошибка: введите корректное число отзывов"}, status=400)

        app_id = extract_app_id(game_url)
        if not app_id:
            return JsonResponse({"error": "Ошибка: неверный URL игры"}, status=400)

        # Получаем текущий язык пользователя
        

        # Асинхронный вызов обработки отзывов
        raw_result = asyncio.run(process_game_reviews(app_id, int(limit), language='english', page_language=page_language))
        formatted_result = format_text(raw_result)

        # Преобразуем markdown в HTML
        html_result = markdown.markdown(formatted_result)

        return JsonResponse({"success": True, "review": html_result})

    except ValueError as e:
        return JsonResponse({"error": f"Ошибка: {str(e)}"}, status=400)
    except Exception as e:
        print(f"Ошибка на сервере: {e}")
        return JsonResponse({"error": f"Server error: {str(e)}"}, status=500)

@csrf_exempt
def search_games_view(request):
    if request.method == 'POST':
        tags = request.body.decode('utf-8').strip()

        if not tags:
            return JsonResponse({"error": "Ошибка: пустое поле/неверный запрос"}, status=400)
        
        # Получаем текущий язык пользователя
        page_language = get_language()  # Это 'en' или 'ru', в зависимости от текущего языка
        
        games_result = search_games(tags, page_language=page_language)

        if not games_result:
            return JsonResponse({"error": "Ошибка: по вашему запросу ничего не найдено"}, status=400)

        # Генерация HTML-таблицы
        if page_language == "ru":
                keys = {
                    "logo": "Лого",
                    "name": "Название",
                    "price": "Цена",
                    "tags": "Метки",
                    "link": "Ссылка"
                }
                header_logo = "Лого"
                header_info = "Информация"
                open_link_text = "Открыть в Steam"
        else:
            keys = {
                "logo": "Logo",
                "name": "Name",
                "price": "Price",
                "tags": "Tags",
                "link": "Link"
            }
            header_logo = "Cover"
            header_info = "Info"
            open_link_text = "Open in Steam"
    
        result = f"""
        <table style="width: 100%; border-collapse: collapse;">
            <thead>
                <tr style="background-color: #f2f2f2;">
                    <th style="border: 1px solid #ddd; padding: 8px;">{header_logo}</th>
                    <th style="border: 1px solid #ddd; padding: 8px;">{header_info}</th>
                </tr>
            </thead>
            <tbody>
        """
    
        for game in games_result:
            result += f"""
                <tr>
                    <td style="border: 1px solid #ddd; padding: 8px; text-align: center; width: 240px;">
                        <img src="{game[keys['logo']]}" alt="Game cover" style="width: 360px; height: auto; border-radius: 5px; position: relative; right: 13%">
                    </td>
                    <td style="border: 1px solid #ddd; padding: 8px; line-height: 1.2;">
                        <strong style="font-size: 26px; font-weight: bold;">{game[keys['name']]}</strong><br>
                        <span style="color: #66ff00; font-size: 21px; font-weight: bold;">{game[keys['price']]}</span><br>
                        <small style="font-size: 19px;">{', '.join(game[keys['tags']][:5])}</small><br>
                        <a href="{game[keys['link']]}" target="_blank" style="color: #007bff; font-size: 19px;">{open_link_text}</a>
                    </td>
                </tr>
            """
    
        result += """
            </tbody>
        </table>
        """

        return HttpResponse(result, content_type="text/html; charset=utf-8")

    return HttpResponseBadRequest("Метод не поддерживается")
