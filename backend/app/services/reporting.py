# SPDX-License-Identifier: MIT
"""Compose administrator reports from repository query results."""

from datetime import datetime

from app.repositories.reporting import ReportingRepository


def dashboard(connection) -> dict:
    repository = ReportingRepository(connection.cursor())
    return {
        "metrics": repository.dashboard_metrics(),
        "monthly_revenue": repository.monthly_revenue(),
        "top_products": repository.top_products(),
        "recent_orders": repository.recent_orders(),
        "today_customers": repository.today_customers(),
        "generated_at": datetime.now().isoformat(),
    }


def revenue(connection) -> dict:
    repository = ReportingRepository(connection.cursor())
    return {
        "summary": repository.revenue_summary(),
        "categories": repository.revenue_by_category(),
        "months": repository.monthly_revenue(include_order_count=True),
    }
