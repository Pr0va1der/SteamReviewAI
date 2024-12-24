import json
import requests
import tiktoken
from tqdm import tqdm

# Инициализация токенизатора для GPT-3 или GPT-4
enc = tiktoken.get_encoding("cl100k_base")

# Настройки для ограничения количества токенов
MAX_TOTAL_TOKENS = 32768  # Максимальное количество токенов (включая входные и выходные)
RESERVED_TOKENS = 500  # Зарезервированное количество токенов для ответа

# Функция для точного подсчета токенов
def count_tokens(text):
    return len(enc.encode(text))

# Функция для разбиения текста на части, если он слишком длинный для одного запроса
def split_text(text, max_length=2000):
    """Разбиваем текст на части, если он слишком длинный для одного запроса."""
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

# Функция для разбиения текста на части, если итоговый отзыв слишком длинный
def split_large_text_into_parts(text):
    """Разбиваем длинный итоговый текст на части, чтобы избежать превышения лимита токенов."""
    parts = []
    max_tokens_per_part = MAX_TOTAL_TOKENS - RESERVED_TOKENS  # Учитываем количество токенов для ответа

    current_part = ""
    for sentence in text.split('. '):
        temp_part = current_part + sentence + '. '
        if count_tokens(temp_part) > max_tokens_per_part:
            if current_part:
                parts.append(current_part.strip())
            current_part = sentence + '. '
        else:
            current_part = temp_part

    if current_part:
        parts.append(current_part.strip())

    return parts

# Функция для обработки отдельного фрагмента текста
def process_chunk(client, chunk, is_positive=True):
    try:
        if is_positive:
            message = f"Это положительные отзывы об игре. Сформируй ключевые положительные аспекты игры, укажи только положительные черты. Если отзыв на английском - переводи на русский. Пиши кратко, избегай повторений: {chunk}"
        else:
            message = f"Это отрицательные отзывы об игре. Сформируй ключевые негативные аспекты игры. Пиши кратко, избегай повторений: {chunk}"

        input_tokens = count_tokens(chunk)
        max_new_tokens = MAX_TOTAL_TOKENS - input_tokens - RESERVED_TOKENS
        if max_new_tokens < 1:
            print("Слишком много токенов для этого текста.")
            return ""
        max_new_tokens = max(500, min(max_new_tokens, 3000))  # Ограничиваем диапазон

        result = client.predict(
            message=message,
            system_message="You are a helpful assistant. Please be brief and concise.",
            max_tokens=max_new_tokens,
            temperature=0.7,
            top_p=0.8,
            api_name="/chat"
        )
        return result.strip()
    except Exception as e:
        print(f"Ошибка при обработке: {e}")
        return ""

# Функция для создания итогового отзыва с рекомендацией
def process_final_review_in_parts(client, positive_summary, negative_summary):
    final_message = (
        f"Сформируй итоговый отзыв об игре, указав не более 5 основных положительных аспектов и не более 5 основных отрицательных аспектов. "
        f"Выбери только самые важные и значимые тезисы. Избегай повторов. Если отзыв на английском - переводи на русский. "
        f"На основе этого анализа сделай вывод: рекомендуешь ли ты игру к покупке или нет. "
        f"Для обозначения форматирования текста (жирность, заголовок, список, и т.д.) используй HTML теги"
        f"Рекомендация должна быть четкой: 'Рекомендуется' или 'Не рекомендуется', с кратким пояснением.\n\n"
        f"Положительные аспекты:\n{positive_summary}\n\n"
        f"Отрицательные аспекты:\n{negative_summary}"
    )

    # Разбиение итогового текста на части
    parts = split_large_text_into_parts(final_message)

    final_result = []

    for part in parts:
        try:
            input_tokens = count_tokens(part)
            max_new_tokens = MAX_TOTAL_TOKENS - input_tokens - RESERVED_TOKENS
            if max_new_tokens < 1:
                print("Слишком много токенов для этого текста.")
                return ""
            max_new_tokens = max(500, min(max_new_tokens, 3000))  # Ограничиваем диапазон

            result = client.predict(
                message=part,
                system_message="You are a helpful assistant. Please be brief and concise.",
                max_tokens=max_new_tokens,
                temperature=0.7,
                top_p=0.8,
                api_name="/chat"
            )

            final_result.append(result.strip())
        except Exception as e:
            print(f"Ошибка при создании итогового отзыва: {e}")
            return ""

    # Объединение результатов в один итоговый текст
    return " ".join(final_result)

# Функция для получения отзывов из Steam
def fetch_reviews_limited(app_id, limit=200000, language='english', num_per_page=100):
    url = f"https://store.steampowered.com/appreviews/{app_id}"
    params = {
        'json': 1,
        'filter': 'all',
        'language': language,
        'num_per_page': num_per_page,
        'cursor': '*',
    }

    all_reviews = []
    total_reviews_fetched = 0

    while total_reviews_fetched < limit:
        response = requests.get(url, params=params)

        if response.status_code != 200:
            print(f"Ошибка: {response.status_code}")
            break

        data = response.json()
        reviews = data.get('reviews', [])

        # Проверяем, есть ли отзывы
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

# Основной процесс обработки отзывов
def process_game_reviews(app_id, limit=1000, language='english'):
    from gradio_client import Client  # Импортируем Client
    client = Client("llamameta/Qwen2.5-Coder-32B-Instruct-Chat-Assistant")  # Создаем клиент один раз

    reviews = fetch_reviews_limited(app_id, limit, language)

    if isinstance(reviews, dict) and "error" in reviews:
        # Если нет отзывов, выбрасываем исключение
        raise ValueError(reviews["error"])

    positive_reviews = [review['review'] for review in reviews if review['voted_up']]
    negative_reviews = [review['review'] for review in reviews if not review['voted_up']]

    positive_summaries = []
    for review in tqdm(positive_reviews, desc="Обработка положительных отзывов"):
        sections = split_text(review)
        for section in sections:
            summary = process_chunk(client, section, is_positive=True)
            if summary:
                positive_summaries.append(summary)

    negative_summaries = []
    for review in tqdm(negative_reviews, desc="Обработка отрицательных отзывов"):
        sections = split_text(review)
        for section in sections:
            summary = process_chunk(client, section, is_positive=False)
            if summary:
                negative_summaries.append(summary)

    positive_text = " ".join(positive_summaries)
    negative_text = " ".join(negative_summaries)

    final_positive_summary = process_final_review_in_parts(client, positive_text, negative_text)

    return final_positive_summary