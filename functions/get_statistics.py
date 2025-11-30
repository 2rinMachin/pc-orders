from collections import Counter, defaultdict
from datetime import datetime

import boto3
from boto3.dynamodb.conditions import Key

from common import response, table_name
from schemas import Order

dynamodb = boto3.resource("dynamodb")
orders = dynamodb.Table(table_name("orders"))


def parse_iso(dt: str) -> datetime:
    return datetime.fromisoformat(dt.replace("Z", "+00:00"))


def handler(event, context):
    tenant_id = event["pathParameters"]["tenant_id"]

    resp = orders.query(
        IndexName="tenant-created-at-idx",
        KeyConditionExpression=Key("tenant_id").eq(tenant_id),
    )

    items: list[dict] = resp["Items"]
    all_orders = [Order(**item) for item in items]

    # Basic status count
    status_count = Counter(order.status for order in all_orders)

    # Worker stats
    cook_count = Counter()
    dispatcher_count = Counter()
    driver_count = Counter()
    client_count = Counter()

    # Time buckets
    orders_per_day = Counter()

    # Stage durations
    stage_pairs = [
        ("wait_for_cook", "cooking"),
        ("cooking", "wait_for_dispatcher"),
        ("wait_for_dispatcher", "dispatching"),
        ("dispatching", "wait_for_deliverer"),
        ("wait_for_deliverer", "delivering"),
        ("delivering", "complete"),
    ]

    stage_totals = defaultdict(float)
    stage_counts = defaultdict(int)

    total_durations = []

    for order in all_orders:
        # Worker metrics
        if order.cook_id:
            cook_count[order.cook_id] += 1
        if order.dispatcher_id:
            dispatcher_count[order.dispatcher_id] += 1
        if order.driver_id:
            driver_count[order.driver_id] += 1

        client_count[order.client.user_id] += 1

        # Orders per day
        try:
            d = parse_iso(order.created_at).date().isoformat()
            orders_per_day[d] += 1
        except Exception:
            pass

        # Stage durations from history
        history = order.history or []
        status_ts = {}
        for h in history:
            try:
                status_ts[h.status] = parse_iso(h.date)
            except Exception:
                continue

        # Stage-by-stage timing
        for a, b in stage_pairs:
            if a in status_ts and b in status_ts:
                dt = (status_ts[b] - status_ts[a]).total_seconds()
                if dt >= 0:
                    key = f"{a} -> {b}"
                    stage_totals[key] += dt
                    stage_counts[key] += 1

        # Total duration (created_at → complete)
        if "complete" in status_ts:
            try:
                dt_total = (
                    status_ts["complete"] - parse_iso(order.created_at)
                ).total_seconds()
                if dt_total >= 0:
                    total_durations.append(dt_total)
            except Exception:
                pass

    # Compute averages
    avg_stage_durations = {
        stage: (stage_totals[stage] / stage_counts[stage])
        for stage in stage_totals
        if stage_counts[stage] > 0
    }

    avg_total_duration = (
        sum(total_durations) / len(total_durations) if total_durations else None
    )

    return response(
        200,
        {
            "total_orders": len(all_orders),
            "status_count": dict(status_count),
            "orders_by_cook": dict(cook_count),
            "orders_by_dispatcher": dict(dispatcher_count),
            "orders_by_driver": dict(driver_count),
            "orders_by_client": dict(client_count),
            "orders_per_day": dict(orders_per_day),
            "avg_stage_durations_seconds": avg_stage_durations,
            "avg_total_duration_seconds": avg_total_duration,
        },
    )
