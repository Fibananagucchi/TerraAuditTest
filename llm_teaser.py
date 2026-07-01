"""
TerraAudit — LLM Інвестиційний тізер
Groq (llama-3.3-70b) генерує інвестиційний тізер на основі даних ділянки.
"""

import os
from groq import Groq


def generate_teaser(
    community_name: str,
    area: float,
    land_type: str,
    market_price: float,
    ndvi_score: float = None,
    viirs_rad: float = None,
    sar_changed: bool = False,
) -> str:
    """
    Генерує інвестиційний тізер для Прозорро.Продажі.

    Args:
        community_name: назва локації/громади
        area: площа в гектарах
        land_type: кадастровий тип
        market_price: справедлива ринкова ціна оренди (грн/рік)
        ndvi_score: індекс рослинності (опційно, з GeoAI)
        viirs_rad: нічна яскравість (опційно, з GeoAI)
        sar_changed: чи виявлено зміни поверхні SAR (опційно)

    Returns:
        Текст тізера у форматі Markdown
    """
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        return (
            "⚠️ **Помилка:** Не знайдено `GROQ_API_KEY`.\n\n"
            "Додайте ключ у файл `.env`:\n```\nGROQ_API_KEY=your_key_here\n```"
        )

    # Формуємо супутниковий блок тільки якщо дані є
    satellite_block = ""
    if ndvi_score is not None:
        satellite_block += f"\n- NDVI (вегетація): {ndvi_score:.2f}"
    if viirs_rad is not None:
        activity = "виявлено" if viirs_rad > 2.0 else "відсутня"
        satellite_block += f"\n- Нічна активність VIIRS: {viirs_rad:.1f} нВт ({activity})"
    if sar_changed:
        satellite_block += "\n- Sentinel-1 SAR: зафіксовано зміну поверхні"

    satellite_section = (
        f"\n\nСупутниковий аналіз (Sentinel-2/VIIRS/SAR):{satellite_block}"
        if satellite_block else ""
    )

    prompt = f"""Створи короткий інвестиційний тізер для публікації на платформі Прозорро.Продажі (формат Markdown).

Дані активу:
- Локація: {community_name}
- Площа: {area} га
- Кадастровий тип: {land_type}
- Справедлива стартова ціна оренди: {market_price:,.0f} грн/рік{satellite_section}

Структура тізера (обов'язкова):
## [Заголовок — назва та тип активу]

**Короткий опис** (2-3 речення про розташування та потенціал)

### Економічний потенціал
(конкретні цифри: стартова ціна, потенційний дохід громади, строк окупності)

### Вигоди для громади
(3-4 пункти: що отримає громада від монетизації цього активу)

---
*Згенеровано ШІ-аудитором TerraAudit на основі відкритих даних. Потребує верифікації людиною перед публікацією.*

Відповідай виключно українською мовою. Виводь тільки текст тізера без вступних слів."""

    try:
        client = Groq(api_key=api_key)
        response = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Ти — експерт з муніципальних інвестицій та управління "
                        "комунальним майном в Україні. Пишеш конкретно, коротко, "
                        "без маркетингових кліше. Відповідаєш тільки українською."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.3,
            max_tokens=800,
        )
        return response.choices[0].message.content

    except Exception as e:
        return (
            f"⚠️ **Помилка Groq API:** {str(e)}\n\n"
            "Перевірте `GROQ_API_KEY` або ліміти безкоштовного тарифу."
        )