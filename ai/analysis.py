from collections import defaultdict
from datetime import datetime

def analyze_spending(rows):
    now = datetime.now()
    current_month_str = now.strftime("%Y-%m")
    
    if not rows:
        return {
            "total_spent": 0, 
            "this_month_spent": 0,
            "last_month_spent": 0,
            "top_category": "None", 
            "category_breakdown_total": {},
            "breakdown_by_month": {current_month_str: {}},
            "available_months": [current_month_str],
            "current_month": current_month_str,
            "predicted_next_month": 0
        }

    total_spent = sum(row["amount"] for row in rows)
    
    category_totals = defaultdict(float)
    monthly_totals = defaultdict(float)
    breakdown_by_month = defaultdict(lambda: defaultdict(float))
    
    for row in rows:
        category_totals[row["category"]] += row["amount"]
        month_key = row["expense_date"][:7] 
        monthly_totals[month_key] += row["amount"]
        breakdown_by_month[month_key][row["category"]] += row["amount"]
        
    top_category = max(category_totals, key=category_totals.get) if category_totals else "None"
    
    if now.month == 1:
        last_month_str = f"{now.year - 1}-12"
    else:
        last_month_str = f"{now.year}-{now.month - 1:02d}"

    this_month_spent = monthly_totals.get(current_month_str, 0.0)
    last_month_spent = monthly_totals.get(last_month_str, 0.0)

    if monthly_totals:
        latest_month = max(monthly_totals.keys())
        predicted_next_month = round(monthly_totals[latest_month], 2)
    else:
        predicted_next_month = 0.0

    bbm = {m: dict(cats) for m, cats in breakdown_by_month.items()}
    available_months = sorted(list(bbm.keys()), reverse=True)
    
    if current_month_str not in bbm:
        bbm[current_month_str] = {}
        if current_month_str not in available_months:
            available_months.insert(0, current_month_str)

    return {
        "total_spent": round(total_spent, 2),
        "this_month_spent": round(this_month_spent, 2),
        "last_month_spent": round(last_month_spent, 2),
        "top_category": top_category,
        "category_breakdown_total": dict(category_totals),
        "breakdown_by_month": bbm,
        "available_months": available_months,
        "current_month": current_month_str,
        "predicted_next_month": predicted_next_month
    }
