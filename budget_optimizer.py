"""
TerraAudit — Бюджетний оптимізатор
LP-модель розподілу вивільнених коштів за соціальними пріоритетами.
"""

import pulp


# Ваги соціальної корисності та обмеження по категоріях
CATEGORIES = {
    "Школи":    {"utility": 1.2, "min_pct": 0.15, "max_pct": 0.50},
    "Дороги":   {"utility": 1.0, "min_pct": 0.10, "max_pct": 0.40},
    "Медицина": {"utility": 1.5, "min_pct": 0.15, "max_pct": 0.50},
}


def optimize_budget(total_funds: float) -> dict:
    """
    Розподіляє бюджет між категоріями, максимізуючи зважену соціальну корисність.

    Зміни відносно старого коду:
    - min_pct знижено (15% замість 30/40%) → оптимізатор має реальний простір
    - max_pct обмежує монополізацію однієї категорії
    - Повертає також загальну суму та статус

    Args:
        total_funds: сума вивільнених коштів (грн)

    Returns:
        dict з розподілом по категоріях + мета-інфо
    """
    if total_funds <= 0:
        return {cat: 0 for cat in CATEGORIES} | {
            "Всього (грн)": 0,
            "Статус": "Нульовий бюджет",
        }

    prob = pulp.LpProblem("TerraAudit_BudgetAllocation", pulp.LpMaximize)

    # Змінні — сума для кожної категорії
    vars_ = {
        cat: pulp.LpVariable(
            cat,
            lowBound=total_funds * params["min_pct"],
            upBound=total_funds * params["max_pct"],
        )
        for cat, params in CATEGORIES.items()
    }

    # Ціль: максимізувати зважену суму корисності
    prob += pulp.lpSum(
        CATEGORIES[cat]["utility"] * vars_[cat]
        for cat in CATEGORIES
    )

    # Сума не перевищує бюджет
    prob += pulp.lpSum(vars_[cat] for cat in CATEGORIES) <= total_funds

    # Сума не менша за 95% бюджету (не залишаємо гроші "в повітрі")
    prob += pulp.lpSum(vars_[cat] for cat in CATEGORIES) >= total_funds * 0.95

    prob.solve(pulp.PULP_CBC_CMD(msg=0))

    result = {
        cat: int(vars_[cat].varValue or 0)
        for cat in CATEGORIES
    }

    result["Всього (грн)"] = sum(result[c] for c in CATEGORIES)
    result["Статус"] = pulp.LpStatus[prob.status]

    # Зручні ключі для app.py
    result["Школи (грн)"]    = result.pop("Школи")
    result["Дороги (грн)"]   = result.pop("Дороги")
    result["Медицина (грн)"] = result.pop("Медицина")

    return result