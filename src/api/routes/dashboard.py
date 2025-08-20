from fastapi import APIRouter
from datetime import datetime
from typing import List, Dict

router = APIRouter(prefix="/api/v1")

@router.get("/dashboard")
def get_dashboard() -> Dict:
    return {
        "current_month": {
            "income": 5500,
            "expenses": 3200,
            "net": 2300,
            "transaction_count": 127
        },
        "previous_month": {
            "income": 4900,
            "expenses": 3400,
            "net": 1500,
            "transaction_count": 119
        },
        "monthly_trends": [
            {"month": "2024-01", "income": 5000, "expenses": 3200, "net": 1800},
            {"month": "2024-02", "income": 5200, "expenses": 3100, "net": 2100},
            {"month": "2024-03", "income": 5300, "expenses": 3300, "net": 2000},
            {"month": "2024-04", "income": 5400, "expenses": 3400, "net": 2000},
            {"month": "2024-05", "income": 5500, "expenses": 3200, "net": 2300}
        ],
        "top_categories": [
            {"category_name": "Alimentação", "amount": 1200},
            {"category_name": "Transporte", "amount": 800},
            {"category_name": "Moradia", "amount": 1500},
            {"category_name": "Saúde", "amount": 400},
            {"category_name": "Lazer", "amount": 600}
        ],
        "total_transactions": 127,
        "recent_transactions": 8
    }

