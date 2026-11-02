from collections import defaultdict
from datetime import datetime

def analyze_spending(rows):
    if not rows:
        return {
            "total_spent": 0, 
            "this_month_spent": 0,
            "last_month_spent": 0,
            "top_category": "None", 
            "category_breakdown": {}, 
            "predicted_next_month": 0
        }

    total_spent = sum(row["amount"] for row in rows)
    
    category_totals = defaultdict(float)
    monthly_totals = defaultdict(float)
    
    for row in rows:
        category_totals[row["category"]] += row["amount"]
        month_key = row["expense_date"][:7] 
        monthly_totals[month_key] += row["amount"]
        
    top_category = max(category_totals, key=category_totals.get) if category_totals else "None"
    
    # Calculate exact current and previous calendar months
    now = datetime.now()
    current_month_str = now.strftime("%Y-%m")
    if now.month == 1:
        last_month_str = f"{now.year - 1}-12"
    else:
        last_month_str = f"{now.year}-{now.month - 1:02d}"

    this_month_spent = monthly_totals.get(current_month_str, 0.0)
    last_month_spent = monthly_totals.get(last_month_str, 0.0)

    # Base prediction on the most recent month with recorded expenses
    if monthly_totals:
        latest_month = max(monthly_totals.keys())
        predicted_next_month = round(monthly_totals[latest_month], 2)
    else:
        predicted_next_month = 0.0

    return {
        "total_spent": round(total_spent, 2),
        "this_month_spent": round(this_month_spent, 2),
        "last_month_spent": round(last_month_spent, 2),
        "top_category": top_category,
        "category_breakdown": dict(category_totals),
        "predicted_next_month": predicted_next_month
    }
