import pulp

def optimize_budget(total_funds):
    prob = pulp.LpProblem("BudgetOptimization", pulp.LpMaximize)

    schools = pulp.LpVariable('Schools', lowBound=0)
    roads = pulp.LpVariable('Roads', lowBound=0)
    medicine = pulp.LpVariable('Medicine', lowBound=0)

    # Максимізація соціальної користі
    prob += 1.2 * schools + 1.0 * roads + 1.5 * medicine, "Social_Utility"

    # Обмеження витрат
    prob += schools + roads + medicine <= total_funds, "Total_Budget"

    # Мінімальні потреби (симуляція базових вимог)
    prob += schools >= total_funds * 0.3 
    prob += medicine >= total_funds * 0.4
    prob += roads >= total_funds * 0.1

    prob.solve()

    return {
        "Школи (грн)": int(schools.varValue) if schools.varValue else 0,
        "Дороги (грн)": int(roads.varValue) if roads.varValue else 0,
        "Медицина (грн)": int(medicine.varValue) if medicine.varValue else 0,
        "Status": pulp.LpStatus[prob.status]
    }