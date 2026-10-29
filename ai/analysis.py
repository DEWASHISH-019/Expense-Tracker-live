from collections import defaultdict

def analyze_spending(rows):
    if not rows:
        return {"total_spent": 0, "top_category": "None", "category_breakdown": {}, "predicted_next_month": 0}

    total_spent = sum(row["amount"] for row in rows)
    
    category_totals = defaultdict(float)
    for row in rows:
        category_totals[row["category"]] += row["amount"]
        
    top_category = max(category_totals, key=category_totals.get) if category_totals else "None"
    average_expense = total_spent / len(rows)
    predicted_next_month = round(total_spent + average_expense, 2)

    return {
        "total_spent": round(total_spent, 2),
        "top_category": top_category,
        "category_breakdown": dict(category_totals),
        "predicted_next_month": predicted_next_month
    }
