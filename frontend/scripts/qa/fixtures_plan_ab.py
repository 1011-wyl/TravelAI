"""Shared TripPlan fixtures for phase 8.2 isolation regression (mock API only)."""

from __future__ import annotations

import copy
import json
from typing import Any


CITY = "杭州"
START = "2026-04-01"
END = "2026-04-03"


def _day(
    date: str,
    day_index: int,
    attraction_name: str,
    description: str,
) -> dict[str, Any]:
    return {
        "date": date,
        "day_index": day_index,
        "city": CITY,
        "description": description,
        "transportation": "地铁",
        "accommodation": "酒店",
        "hotel": {
            "name": f"{attraction_name}-Hotel",
            "address": "测试路 1 号",
            "price_range": "400-600",
            "rating": "4.5",
            "distance": "1km",
            "type": "舒适型",
            "estimated_cost": 500,
        },
        "attractions": [
            {
                "name": attraction_name,
                "address": "测试景点路",
                "location": {"longitude": 120.15, "latitude": 30.25},
                "visit_duration": 120,
                "description": description,
                "ticket_price": 80,
            }
        ],
        "meals": [
            {
                "type": "lunch",
                "name": f"{attraction_name}-Lunch",
                "estimated_cost": 60,
            }
        ],
    }


def make_plan(marker: str) -> dict[str, Any]:
    """marker distinguishes plans that share city/dates."""
    return {
        "city": CITY,
        "cities": [CITY],
        "start_date": START,
        "end_date": END,
        "days": [
            _day(START, 1, f"UNIQUE-{marker}-ATTR", f"DESC-{marker}-DAY1"),
            _day("2026-04-02", 2, f"UNIQUE-{marker}-ATTR-2", f"DESC-{marker}-DAY2"),
        ],
        "weather_info": [
            {
                "date": START,
                "city": CITY,
                "day_weather": "晴",
                "night_weather": "晴",
                "day_temp": 24,
                "night_temp": 16,
                "wind_direction": "东风",
                "wind_power": "2级",
            }
        ],
        "overall_suggestions": f"SUGGEST-{marker}",
        "budget": {
            "total_attractions": 160,
            "total_hotels": 1000,
            "total_meals": 120,
            "total_transportation": 80,
            "total": 1360,
        },
    }


def make_graph(marker: str) -> dict[str, Any]:
    return {
        "nodes": [
            {
                "id": f"n-{marker}",
                "name": f"UNIQUE-{marker}-ATTR",
                "category": 0,
                "symbolSize": 40,
            }
        ],
        "edges": [],
        "categories": [{"name": "景点"}],
    }


def status_payload(plan_id: str, marker: str) -> dict[str, Any]:
    return {
        "task_id": plan_id,
        "plan_id": plan_id,
        "status": "completed",
        "stage": "completed",
        "progress": 100,
        "message": "done",
        "result": {
            "success": True,
            "message": "ok",
            "plan_id": plan_id,
            "data": make_plan(marker),
            "graph_data": make_graph(marker),
        },
    }


PLAN_A = make_plan("A")
PLAN_B = make_plan("B")
GRAPH_A = make_graph("A")
GRAPH_B = make_graph("B")

assert PLAN_A["city"] == PLAN_B["city"]
assert PLAN_A["start_date"] == PLAN_B["start_date"]
assert PLAN_A["end_date"] == PLAN_B["end_date"]
assert PLAN_A["days"][0]["attractions"][0]["name"] != PLAN_B["days"][0]["attractions"][0]["name"]


def dumps(obj: Any) -> str:
    return json.dumps(copy.deepcopy(obj), ensure_ascii=False)
