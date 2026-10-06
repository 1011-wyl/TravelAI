"""Rich TripPlan fixtures for phase 8.3 visual/a11y QA (mock API only)."""

from __future__ import annotations

import copy
import json
from typing import Any

CITY_ROUTE = ["杭州", "苏州"]
START = "2026-04-01"
END = "2026-04-05"

LONG_NAME = "西湖断桥残雪与白堤春晓超长景点名称用于验收是否被裁切"
LONG_DESC = (
    "这段说明刻意写得很长，用来检查每日行程卡片、概览明信片和导出对话框外围"
    "是否会把文字裁掉或造成横向溢出。" * 3
)


def _loc(lng: float, lat: float) -> dict[str, float]:
    return {"longitude": lng, "latitude": lat}


def _attraction(name: str, desc: str, price: float, lng: float, lat: float, image: str | None = None) -> dict[str, Any]:
    item: dict[str, Any] = {
        "name": name,
        "address": "杭州市西湖区龙井路 1 号超长地址用于检查表格换行",
        "location": _loc(lng, lat),
        "visit_duration": 150,
        "description": desc,
        "ticket_price": price,
        "category": "景点",
        "rating": 4.7,
    }
    if image:
        item["image_url"] = image
    return item


def _meal(kind: str, name: str, cost: float) -> dict[str, Any]:
    return {
        "type": kind,
        "name": name,
        "address": "美食街 88 号",
        "location": _loc(120.16, 30.26),
        "description": "本地推荐",
        "estimated_cost": cost,
    }


def _hotel(name: str, cost: float) -> dict[str, Any]:
    return {
        "name": name,
        "address": "湖滨路 100 号",
        "location": _loc(120.16, 30.25),
        "price_range": "500-800",
        "rating": "4.6",
        "distance": "800m",
        "type": "舒适型",
        "estimated_cost": cost,
    }


def _day(
    date: str,
    day_index: int,
    city: str,
    attractions: list[dict[str, Any]],
    meals: list[dict[str, Any]],
    hotel: dict[str, Any] | None,
    description: str,
) -> dict[str, Any]:
    return {
        "date": date,
        "day_index": day_index,
        "city": city,
        "description": description,
        "transportation": "地铁 2 号线转公交",
        "accommodation": hotel["name"] if hotel else "当日离开",
        "hotel": hotel,
        "attractions": attractions,
        "meals": meals,
    }


def make_rich_plan() -> dict[str, Any]:
    days = [
        _day(
            "2026-04-01",
            1,
            "杭州",
            [
                _attraction(LONG_NAME, LONG_DESC, 80, 120.14, 30.25, "https://example.com/ok.jpg"),
                _attraction("灵隐寺", "古刹晨钟。", 45, 120.10, 30.24),
            ],
            [_meal("breakfast", "豆浆油条", 18), _meal("lunch", "楼外楼西湖醋鱼", 128), _meal("dinner", "河坊街小吃", 60)],
            _hotel("湖畔舒适酒店", 620),
            "杭州首日：" + LONG_DESC[:80],
        ),
        _day(
            "2026-04-02",
            2,
            "杭州",
            [_attraction("龙井村", "茶园步道。", 0, 120.12, 30.22, "https://example.com/fail.jpg")],
            [_meal("lunch", "茶餐厅简餐", 45)],
            _hotel("龙井民宿", 480),
            "茶山半日。",
        ),
        _day(
            "2026-04-03",
            3,
            "杭州",
            [_attraction("西溪湿地", "水巷与观鸟。", 70, 120.06, 30.27)],
            [_meal("lunch", "湿地农家菜", 88)],
            _hotel("西溪度假酒店", 760),
            "湿地慢游。",
        ),
        _day(
            "2026-04-04",
            4,
            "苏州",
            [
                _attraction("拙政园", "江南园林。", 90, 120.62, 31.32),
                _attraction("平江路", "石板街夜色。", 0, 120.63, 31.31),
            ],
            [_meal("lunch", "苏式面", 32), _meal("dinner", "松鼠桂鱼", 158)],
            _hotel("观前商务酒店", 540),
            "转场苏州。",
        ),
        _day(
            "2026-04-05",
            5,
            "苏州",
            [_attraction("虎丘", "斜塔与剑池。", 60, 120.57, 31.33)],
            [_meal("lunch", "生煎包", 24)],
            None,
            "返程日，活动较少。",
        ),
    ]
    return {
        "city": "杭州",
        "cities": CITY_ROUTE,
        "start_date": START,
        "end_date": END,
        "days": days,
        "weather_info": [
            {
                "date": "2026-04-01",
                "city": "杭州",
                "day_weather": "晴",
                "night_weather": "晴",
                "day_temp": 24,
                "night_temp": 15,
                "wind_direction": "东风",
                "wind_power": "2级",
            },
            {
                "date": "2026-04-02",
                "city": "杭州",
                "day_weather": "小雨",
                "night_weather": "阴",
                "day_temp": 18,
                "night_temp": 12,
                "wind_direction": "北风",
                "wind_power": "3级",
            },
            {
                "date": "2026-04-03",
                "city": "杭州",
                "day_weather": "雷阵雨",
                "night_weather": "多云",
                "day_temp": 20,
                "night_temp": 14,
                "wind_direction": "东南风",
                "wind_power": "4级",
            },
            {
                "date": "2026-04-04",
                "city": "苏州",
                "day_weather": "未知天气码XYZ",
                "night_weather": "",
                "day_temp": 19,
                "night_temp": 11,
                "wind_direction": "",
                "wind_power": "",
            },
            {
                "date": "",
                "city": "苏州",
                "day_weather": "",
                "night_weather": "",
                "day_temp": 0,
                "night_temp": 0,
                "wind_direction": "",
                "wind_power": "",
            },
        ],
        "overall_suggestions": "多城五日：杭州三天转苏州两天。" + LONG_DESC[:120],
        "budget": {
            "total_attractions": 345,
            "total_hotels": 2400,
            "total_meals": 553,
            "total_transportation": 180,
            "total_inter_city_transport": 90,
            "total": 3568,
        },
    }


def make_rich_graph() -> dict[str, Any]:
    return {
        "nodes": [
            {"id": "n-westlake", "name": "西湖", "category": 0, "symbolSize": 48},
            {"id": "n-westlake-dup", "name": "西湖", "category": 0, "symbolSize": 32},
            {"id": "n-lingyin", "name": "灵隐寺", "category": 0, "symbolSize": 36},
            {"id": "n-meal", "name": "楼外楼", "category": 1, "symbolSize": 28},
            {"id": "n-hotel", "name": "湖畔舒适酒店", "category": 2, "symbolSize": 28},
            {"id": "n-orphan", "name": "孤立茶亭", "category": 0, "symbolSize": 22},
        ],
        "edges": [
            {"source": "n-westlake", "target": "n-lingyin", "label": "同城"},
            {"source": "n-westlake", "target": "n-meal", "label": "午餐"},
            {"source": "n-lingyin", "target": "n-hotel", "label": "住宿"},
        ],
        "categories": [
            {"name": "景点"},
            {"name": "餐饮"},
            {"name": "酒店"},
            {"name": "交通"},
        ],
    }


def make_empty_graph_plan() -> dict[str, Any]:
    plan = make_rich_plan()
    plan["overall_suggestions"] = "EMPTY-GRAPH-PLAN"
    return plan


def make_sparse_weather_plan() -> dict[str, Any]:
    plan = make_rich_plan()
    plan["weather_info"] = []
    plan["overall_suggestions"] = "SPARSE-WEATHER-PLAN"
    return plan


def status_payload(plan_id: str, plan: dict[str, Any], graph: dict[str, Any] | None) -> dict[str, Any]:
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
            "data": plan,
            "graph_data": graph,
        },
    }


def history_items() -> list[dict[str, Any]]:
    return [
        {
            "plan_id": "plan-rich",
            "task_id": "plan-rich",
            "city": "杭州",
            "start_date": START,
            "end_date": END,
            "travel_days": 5,
            "updated_at": "2026-04-01T10:00:00Z",
            "overall_suggestions": "多城五日",
        }
    ]


def dumps(obj: Any) -> str:
    return json.dumps(copy.deepcopy(obj), ensure_ascii=False)


RICH_PLAN = make_rich_plan()
RICH_GRAPH = make_rich_graph()
EMPTY_GRAPH_PLAN = make_empty_graph_plan()
SPARSE_WEATHER_PLAN = make_sparse_weather_plan()
