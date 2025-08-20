"""
Analytics Routes for Finance App API.
"""

from datetime import date, datetime, timedelta
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, extract

from src.models import get_db, Transaction, Category, TransactionType
from src.api.middleware.auth import get_current_user

router = APIRouter()


class MonthlyTrend(BaseModel):
    """Monthly trend data model."""
    month: str
    income: float
    expenses: float
    net: float
    transaction_count: int


class CategoryBreakdown(BaseModel):
    """Category breakdown model."""
    category_id: Optional[int]
    category_name: str
    amount: float
    percentage: float
    transaction_count: int


class DashboardStats(BaseModel):
    """Dashboard statistics model."""
    current_month: Dict[str, float]
    previous_month: Dict[str, float]
    monthly_trends: List[MonthlyTrend]
    top_categories: List[CategoryBreakdown]
    recent_transactions: int
    total_transactions: int


@router.get("/dashboard", response_model=DashboardStats)
async def get_dashboard_stats(
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
    months: int = Query(12, ge=1, le=24, description="Number of months for trends")
):
    """
    Get dashboard statistics and trends.
    """
    
    # Calculate date ranges
    today = date.today()
    current_month_start = today.replace(day=1)
    previous_month_end = current_month_start - timedelta(days=1)
    previous_month_start = previous_month_end.replace(day=1)
    trends_start = current_month_start - timedelta(days=30 * months)
    
    # Current month stats
    current_month_query = db.query(
        func.sum(Transaction.amount).filter(Transaction.amount > 0).label('income'),
        func.sum(Transaction.amount).filter(Transaction.amount < 0).label('expenses'),
        func.count(Transaction.id).label('count')
    ).filter(
        Transaction.date >= current_month_start,
        Transaction.date <= today
    ).first()
    
    current_month_income = float(current_month_query.income or 0)
    current_month_expenses = abs(float(current_month_query.expenses or 0))
    current_month_net = current_month_income - current_month_expenses
    current_month_count = current_month_query.count or 0
    
    # Previous month stats
    previous_month_query = db.query(
        func.sum(Transaction.amount).filter(Transaction.amount > 0).label('income'),
        func.sum(Transaction.amount).filter(Transaction.amount < 0).label('expenses'),
        func.count(Transaction.id).label('count')
    ).filter(
        Transaction.date >= previous_month_start,
        Transaction.date <= previous_month_end
    ).first()
    
    previous_month_income = float(previous_month_query.income or 0)
    previous_month_expenses = abs(float(previous_month_query.expenses or 0))
    previous_month_net = previous_month_income - previous_month_expenses
    previous_month_count = previous_month_query.count or 0
    
    # Monthly trends
    monthly_trends_query = db.query(
        extract('year', Transaction.date).label('year'),
        extract('month', Transaction.date).label('month'),
        func.sum(Transaction.amount).filter(Transaction.amount > 0).label('income'),
        func.sum(Transaction.amount).filter(Transaction.amount < 0).label('expenses'),
        func.count(Transaction.id).label('count')
    ).filter(
        Transaction.date >= trends_start
    ).group_by(
        extract('year', Transaction.date),
        extract('month', Transaction.date)
    ).order_by(
        extract('year', Transaction.date),
        extract('month', Transaction.date)
    ).all()
    
    monthly_trends = []
    for trend in monthly_trends_query:
        income = float(trend.income or 0)
        expenses = abs(float(trend.expenses or 0))
        monthly_trends.append(MonthlyTrend(
            month=f"{int(trend.year)}-{int(trend.month):02d}",
            income=income,
            expenses=expenses,
            net=income - expenses,
            transaction_count=trend.count or 0
        ))
    
    # Top categories (current month)
    top_categories_query = db.query(
        Category.id,
        Category.name,
        func.sum(func.abs(Transaction.amount)).label('total_amount'),
        func.count(Transaction.id).label('count')
    ).join(
        Transaction, Category.id == Transaction.category_id
    ).filter(
        Transaction.date >= current_month_start,
        Transaction.date <= today
    ).group_by(
        Category.id, Category.name
    ).order_by(
        func.sum(func.abs(Transaction.amount)).desc()
    ).limit(10).all()
    
    # Calculate total for percentages
    total_categorized = sum(float(cat.total_amount or 0) for cat in top_categories_query)
    
    top_categories = []
    for cat in top_categories_query:
        amount = float(cat.total_amount or 0)
        percentage = (amount / total_categorized * 100) if total_categorized > 0 else 0
        
        top_categories.append(CategoryBreakdown(
            category_id=cat.id,
            category_name=cat.name,
            amount=amount,
            percentage=percentage,
            transaction_count=cat.count or 0
        ))
    
    # Recent transactions count (last 7 days)
    week_ago = today - timedelta(days=7)
    recent_transactions = db.query(Transaction).filter(
        Transaction.date >= week_ago
    ).count()
    
    # Total transactions
    total_transactions = db.query(Transaction).count()
    
    return DashboardStats(
        current_month={
            "income": current_month_income,
            "expenses": current_month_expenses,
            "net": current_month_net,
            "transaction_count": current_month_count
        },
        previous_month={
            "income": previous_month_income,
            "expenses": previous_month_expenses,
            "net": previous_month_net,
            "transaction_count": previous_month_count
        },
        monthly_trends=monthly_trends,
        top_categories=top_categories,
        recent_transactions=recent_transactions,
        total_transactions=total_transactions
    )


@router.get("/trends/monthly")
async def get_monthly_trends(
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
    months: int = Query(12, ge=1, le=36, description="Number of months"),
    category_id: Optional[int] = Query(None, description="Filter by category")
):
    """
    Get monthly trends data.
    """
    
    # Calculate date range
    today = date.today()
    start_date = today - timedelta(days=30 * months)
    
    # Build query
    query = db.query(
        extract('year', Transaction.date).label('year'),
        extract('month', Transaction.date).label('month'),
        func.sum(Transaction.amount).filter(Transaction.amount > 0).label('income'),
        func.sum(Transaction.amount).filter(Transaction.amount < 0).label('expenses'),
        func.count(Transaction.id).label('count')
    ).filter(
        Transaction.date >= start_date
    )
    
    # Apply category filter
    if category_id:
        query = query.filter(Transaction.category_id == category_id)
    
    # Group and order
    trends = query.group_by(
        extract('year', Transaction.date),
        extract('month', Transaction.date)
    ).order_by(
        extract('year', Transaction.date),
        extract('month', Transaction.date)
    ).all()
    
    # Format response
    result = []
    for trend in trends:
        income = float(trend.income or 0)
        expenses = abs(float(trend.expenses or 0))
        result.append({
            "month": f"{int(trend.year)}-{int(trend.month):02d}",
            "income": income,
            "expenses": expenses,
            "net": income - expenses,
            "transaction_count": trend.count or 0
        })
    
    return result


@router.get("/categories/breakdown")
async def get_category_breakdown(
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
    start_date: Optional[date] = Query(None, description="Start date"),
    end_date: Optional[date] = Query(None, description="End date"),
    transaction_type: Optional[str] = Query(None, description="income or expense"),
    limit: int = Query(20, ge=1, le=100, description="Maximum categories")
):
    """
    Get category breakdown analysis.
    """
    
    # Build query
    query = db.query(
        Category.id,
        Category.name,
        Category.category_type,
        func.sum(func.abs(Transaction.amount)).label('total_amount'),
        func.count(Transaction.id).label('count')
    ).outerjoin(
        Transaction, Category.id == Transaction.category_id
    )
    
    # Apply filters
    filters = []
    
    if start_date:
        filters.append(Transaction.date >= start_date)
    
    if end_date:
        filters.append(Transaction.date <= end_date)
    
    if transaction_type == "income":
        filters.append(Transaction.amount > 0)
    elif transaction_type == "expense":
        filters.append(Transaction.amount < 0)
    
    if filters:
        query = query.filter(and_(*filters))
    
    # Group and order
    categories = query.group_by(
        Category.id, Category.name, Category.category_type
    ).order_by(
        func.sum(func.abs(Transaction.amount)).desc()
    ).limit(limit).all()
    
    # Calculate total for percentages
    total_amount = sum(float(cat.total_amount or 0) for cat in categories)
    
    # Format response
    result = []
    for cat in categories:
        amount = float(cat.total_amount or 0)
        percentage = (amount / total_amount * 100) if total_amount > 0 else 0
        
        result.append({
            "category_id": cat.id,
            "category_name": cat.name,
            "category_type": cat.category_type,
            "amount": amount,
            "percentage": percentage,
            "transaction_count": cat.count or 0
        })
    
    return result


@router.get("/spending/patterns")
async def get_spending_patterns(
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
    days: int = Query(90, ge=7, le=365, description="Number of days to analyze")
):
    """
    Analyze spending patterns and trends.
    """
    
    # Calculate date range
    end_date = date.today()
    start_date = end_date - timedelta(days=days)
    
    # Daily spending
    daily_spending = db.query(
        Transaction.date,
        func.sum(func.abs(Transaction.amount)).filter(Transaction.amount < 0).label('daily_expenses')
    ).filter(
        Transaction.date >= start_date,
        Transaction.amount < 0
    ).group_by(
        Transaction.date
    ).order_by(
        Transaction.date
    ).all()
    
    # Weekly patterns (day of week)
    weekly_pattern = db.query(
        extract('dow', Transaction.date).label('day_of_week'),
        func.sum(func.abs(Transaction.amount)).filter(Transaction.amount < 0).label('total_expenses'),
        func.count(Transaction.id).filter(Transaction.amount < 0).label('transaction_count')
    ).filter(
        Transaction.date >= start_date,
        Transaction.amount < 0
    ).group_by(
        extract('dow', Transaction.date)
    ).order_by(
        extract('dow', Transaction.date)
    ).all()
    
    # Top merchants/counterparts
    top_merchants = db.query(
        Transaction.counterpart_name,
        func.sum(func.abs(Transaction.amount)).label('total_amount'),
        func.count(Transaction.id).label('transaction_count')
    ).filter(
        Transaction.date >= start_date,
        Transaction.counterpart_name.isnot(None),
        Transaction.amount < 0
    ).group_by(
        Transaction.counterpart_name
    ).order_by(
        func.sum(func.abs(Transaction.amount)).desc()
    ).limit(10).all()
    
    # Format response
    day_names = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
    
    return {
        "daily_spending": [
            {
                "date": spending.date.isoformat(),
                "amount": float(spending.daily_expenses or 0)
            }
            for spending in daily_spending
        ],
        "weekly_pattern": [
            {
                "day_of_week": day_names[int(pattern.day_of_week)],
                "day_number": int(pattern.day_of_week),
                "total_expenses": float(pattern.total_expenses or 0),
                "transaction_count": pattern.transaction_count or 0
            }
            for pattern in weekly_pattern
        ],
        "top_merchants": [
            {
                "name": merchant.counterpart_name,
                "total_amount": float(merchant.total_amount or 0),
                "transaction_count": merchant.transaction_count or 0
            }
            for merchant in top_merchants
        ]
    }

