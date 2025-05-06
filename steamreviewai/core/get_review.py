import json
import re
import httpx
import asyncio
import tiktoken
from tqdm import tqdm
from itertools import cycle

# Инициализация токенизатора
enc = tiktoken.get_encoding("cl100k_base")

# Настройки
MAX_TOTAL_TOKENS = 6000
RESERVED_TOKENS = 500
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

# Загрузка API-ключей из файла
def load_api_keys(filename="core/api_keys.txt"):
    """Загружает API-ключи из файла и создает итератор для циклического переключения."""
    with open(filename, "r") as f:
        keys = [line.strip() for line in f if line.strip()]
    if not keys:
        raise ValueError("Файл api_keys.txt пуст или отсутствуют ключи")
    return cycle(keys)  # Итератор для циклического переключения API-ключей

api_keys = load_api_keys()
current_api_key = next(api_keys)

# Подсчет токенов
def count_tokens(text):
    return len(enc.encode(text))

# Разбиение текста на части
def split_text(text, max_length=2000):
    sentences = text.split('. ')
    chunks = []
    current_chunk = ""
    for sentence in sentences:
        if len(current_chunk) + len(sentence) + 1 <= max_length:
            current_chunk += sentence + '. '
        else:
            chunks.append(current_chunk.strip())
            current_chunk = sentence + '. '
    if current_chunk:
        chunks.append(current_chunk.strip())
    return chunks

# Разбиение текста на куски по токенам
def split_by_tokens(text, max_tokens=MAX_TOTAL_TOKENS):
    words = text.split()  
    chunks = []
    current_chunk = []
    current_tokens = 0

    for word in words:
        word_tokens = count_tokens(word)  # Считаем токены для слова
        if current_tokens + word_tokens > max_tokens:  # Если превысили лимит
            chunks.append(" ".join(current_chunk))  # Добавляем текущий кусок
            current_chunk = [word]  # Начинаем новый
            current_tokens = word_tokens
        else:
            current_chunk.append(word)
            current_tokens += word_tokens

    if current_chunk:
        chunks.append(" ".join(current_chunk))  # Добавляем последний кусок

    return chunks

# Асинхронный запрос с разбиением по токенам
async def send_request_groq(prompt):
    """Отправляет запрос в API Groq, разбивая текст, если он слишком длинный."""
    current_api_key = next(api_keys)  # Берем следующий ключ
    headers = {
        "Authorization": f"Bearer {current_api_key}",
        "Content-Type": "application/json"
    }

    # Разбиваем текст на куски, если он длиннее 6000 токенов
    text_chunks = split_by_tokens(prompt, MAX_TOTAL_TOKENS - RESERVED_TOKENS)

    responses = []  # Список для хранения всех ответов

    async with httpx.AsyncClient() as client:
        for chunk in text_chunks:
            payload = {
                "model": "llama3-70b-8192",
                "messages": [
                    {"role": "system", "content": "Будь кратким и лаконичным."},
                    {"role": "user", "content": chunk}
                ],
                "temperature": 0.7,
                "max_tokens": 1024
            }

            response = await client.post(GROQ_API_URL, json=payload, headers=headers)

            if response.status_code == 200:
                content_raw = response.json().get("choices", [{}])[0].get("message", {}).get("content", "").strip()
                # Удаляем блоки <think>...</think>
                content_clean = re.sub(r"<think>.*?</think>", "", content_raw, flags=re.DOTALL).strip()
                responses.append(content_clean)
            else:
                print(f"Ошибка {response.status_code}: {response.text} (Ключ: {current_api_key})")

    return " ".join(responses)  # Объединяем ответы в один

# Обработка кусков отзывов через Groq
async def process_chunk_ru(chunk, is_positive=True):
    message = (
        f"Это {'положительные' if is_positive else 'отрицательные'} отзывы об игре. "
        f"Сформируй ключевые {'положительные' if is_positive else 'негативные'} аспекты. "
        "Если отзыв на английском — переведи на русский. Пиши кратко. "
        f"Текст отзыва: {chunk}"
    )
    return await send_request_groq(message)

# Итоговый анализ игры
async def process_final_review_ru(positive_summary, negative_summary):
    message = (
        "Сформируй итоговый отзыв об игре. Выбери 5 главных положительных и 5 главных отрицательных аспектов. "
        "Избегай повторов. Если отзыв на английском — переведи на русский. Пиши кратко. "
        "Ответ должен быть представлен в Markdown. Только заголовок с положительными аспектами, и заголовок с отрицательными. Для заголовков используй заголовок третьего уровня."
    )
    return await send_request_groq(message)

'''
"Сформируй итоговый отзыв об игре. Выбери 5 главных положительных и 5 главных отрицательных аспектов. "
        "Избегай повторов. Если отзыв на английском — переведи на русский. Пиши кратко. "
        "Ответ должен быть в Markdown: <b>заголовки</b>, <ul><li>списки</li></ul>.\n\n"
        f"<b>Положительные аспекты:</b>\n{positive_summary}\n\n"
        f"<b>Отрицательные аспекты:</b>\n{negative_summary}"
'''

# Обработка кусков отзывов через Groq (на английском)
async def process_chunk_en(chunk, is_positive=True):
    message = (
        f"These are {'positive' if is_positive else 'negative'} reviews of a game. "
        f"Identify the key {'positive' if is_positive else 'negative'} aspects. "
        "If the review is not in English, translate it into English. Be concise. "
        f"Review text: {chunk}"
    )
    return await send_request_groq(message)

# Итоговый анализ игры (на английском)
async def process_final_review_en(positive_summary, negative_summary):
    message = (
        "Create a final review of the game. Choose 5 main positive and 5 main negative aspects. "
        "Avoid repetition. If a review is not in English, translate it into English. Be concise. "
        "The answer must be in Markdown format. Use a level-three heading for the positive and negative sections.\n\n"
        f"Positive aspects:\n{positive_summary}\n\n"
        f"Negative aspects:\n{negative_summary}"
    )
    return await send_request_groq(message)

# Получение отзывов из Steam
async def fetch_reviews_limited(app_id, limit=200000, language='english', num_per_page=100):
    url = f"https://store.steampowered.com/appreviews/{app_id}"
    params = {'json': 1, 'filter': 'all', 'language': language, 'num_per_page': num_per_page, 'cursor': '*'}

    all_reviews = []
    total_reviews_fetched = 0

    async with httpx.AsyncClient() as client:
        while total_reviews_fetched < limit:
            response = await client.get(url, params=params)
            if response.status_code != 200:
                print(f"Ошибка: {response.status_code}")
                break

            data = response.json()
            reviews = data.get('reviews', [])
            if not reviews and total_reviews_fetched == 0:
                return {"error": "У этой игры нет отзывов"}

            if not reviews:
                break

            all_reviews.extend(reviews)
            total_reviews_fetched += len(reviews)
            print(f"Загружено {len(reviews)} отзывов, всего: {total_reviews_fetched}")

            if not data.get('cursor'):
                break
            params['cursor'] = data['cursor']

    return all_reviews[:limit]

async def process_game_reviews(app_id, limit=1000, language='english', page_language='ru'):
    """
    app_id: ID игры в Steam
    limit: лимит отзывов
    language: язык отзывов в Steam
    page_language: 'ru' для русской версии сайта, 'en' для английской
    """
    reviews = await fetch_reviews_limited(app_id, limit, language)
    if isinstance(reviews, dict) and "error" in reviews:
        raise ValueError(reviews["error"])
       
    if len(reviews) > 30:
        raise ValueError(f"Ошибка: слишком много отзывов ({len(reviews)}). Лимит — 30.")

    positive_reviews = [review['review'] for review in reviews if review['voted_up']]
    negative_reviews = [review['review'] for review in reviews if not review['voted_up']]

    # Выбор функций в зависимости от языка страницы
    if page_language == 'ru':
        chunk_processor = process_chunk_ru
        final_processor = process_final_review_ru
    else:
        chunk_processor = process_chunk_en
        final_processor = process_final_review_en

    # Обработка положительных и отрицательных отзывов
    tasks = [chunk_processor(chunk, is_positive=True) for review in positive_reviews for chunk in split_text(review)]
    positive_summaries = await asyncio.gather(*tasks)

    tasks = [chunk_processor(chunk, is_positive=False) for review in negative_reviews for chunk in split_text(review)]
    negative_summaries = await asyncio.gather(*tasks)

    positive_text = " ".join(positive_summaries)
    negative_text = " ".join(negative_summaries)

    final_summary = await final_processor(positive_text, negative_text)
    return final_summary