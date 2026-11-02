from collections import defaultdict

def analyze_spending(rows):
    if not rows:
        return {"total_spent": 0, "top_category": "None", "category_breakdown": {}, "predicted_next_month": 0}

    total_spent = sum(row["amount"] for row in rows)
    
    category_totals = defaultdict(float)
    monthly_totals = defaultdict(float)
    
    for row in rows:
        category_totals[row["category"]] += row["amount"]
        # Extract YYYY-MM from the date string
        month_key = row["expense_date"][:7] 
        monthly_totals[month_key] += row["amount"]
        
    top_category = max(category_totals, key=category_totals.get) if category_totals else "None"
    
    # Base prediction on the most recent month with recorded expenses
    if monthly_totals:
        latest_month = max(monthly_totals.keys())
        predicted_next_month = round(monthly_totals[latest_month], 2)
    else:
        predicted_next_month = 0.0

    return {
        "total_spent": round(total_spent, 2),
        "top_category": top_category,
        "category_breakdown": dict(category_totals),
        "predicted_next_month": predicted_next_month
    }
