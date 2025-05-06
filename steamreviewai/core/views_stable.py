from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.http import JsonResponse, HttpResponse, HttpResponseBadRequest
import json
from django.shortcuts import render
from core.utils import extract_app_id, format_text, check_game_exists
import asyncio
from .get_review import process_game_reviews
from .filter_ai import search_games

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

        # Асинхронный вызов обработки отзывов
        raw_result = asyncio.run(process_game_reviews(app_id, int(limit)))
        formatted_result = format_text(raw_result)

        return JsonResponse({"success": True, "review": formatted_result})

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

        games_result = search_games(tags)

        if not games_result:
            return JsonResponse({"error": "Ошибка: по вашему запросу ничего не найдено"}, status=400)

        # Генерация HTML-таблицы
        result = """
        <table style="width: 100%; border-collapse: collapse;">
            <thead>
                <tr style="background-color: #f2f2f2;">
                    <th style="border: 1px solid #ddd; padding: 8px;">Лого</th>
                    <th style="border: 1px solid #ddd; padding: 8px;">Информация</th>
                </tr>
            </thead>
            <tbody>
        """

        for game in games_result:
            result += f"""
                <tr>
                    <td style="border: 1px solid #ddd; padding: 8px; text-align: center; width: 240px;">
                        <img src="{game['Лого']}" alt="Обложка игры" style="width: 360px; height: auto; border-radius: 5px; position: relative; right: 13%">
                    </td>
                    <td style="border: 1px solid #ddd; padding: 8px; line-height: 1.2;">
                        <strong style="font-size: 26px; font-weight: bold;">{game['Название']}</strong><br>
                        <span style="color: #66ff00; font-size: 21px; font-weight: bold;">{game['Цена']}</span><br>
                        <small style="font-size: 19px;">{', '.join(game['Метки'][:5])}</small><br>
                        <a href="{game['Ссылка']}" target="_blank" style="color: #007bff; font-size: 19px;">Открыть в Steam</a>
                    </td>
                </tr>
            """

        result += """
            </tbody>
        </table>
        """

        return HttpResponse(result, content_type="text/html; charset=utf-8")

    return HttpResponseBadRequest("Метод не поддерживается")
