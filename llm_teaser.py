import os
from groq import Groq

def get_groq_response(prompt):
    try:
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            return "⚠️ Помилка: Не знайдено GROQ_API_KEY. Перевірте файл .env"
            
        client = Groq(api_key=api_key)
        
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "Ти — експерт з регіональних інвестицій та урбаністики. Відповідай виключно українською мовою в діловому стилі."
                },
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            model="llama3-70b-8192",
            temperature=0.5,
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        return f"Помилка генерації Groq: {str(e)}"

def generate_teaser(community_name, area, land_type, market_price):
    prompt = f"""
    Створи короткий інвестиційний тізер для системи Прозорро.Продажі (формат Markdown).
    
    Дані активу:
    - Локація: {community_name}
    - Площа: {area} га
    - Кадастровий тип: {land_type}
    - Справедлива стартова вартість оренди: {market_price:,.0f} грн/рік.
    
    Структура:
    1. Заголовок.
    2. Опис економічного потенціалу.
    3. Вигоди для громади.
    
    Обов'язково додай в кінці курсивом: "Згенеровано ШІ-аудитором TerraAudit, потребує перевірки людиною".
    """
    return get_groq_response(prompt)