import json

import boto3
from boto3.dynamodb.conditions import Attr, Key

from common import resource_name, response, to_json

dynamodb = boto3.resource("dynamodb")


def handler(event, context):
    tenant_id = event["pathParameters"]["tenant_id"]
    query = event.get("queryStringParameters") or {}

    limit = int(query.get("limit") or 10)
    last_key = json.loads(query["last_key"]) if "last_key" in query else None

    status = query.get("status") or ""
    client_id = query.get("client_id")
    cook_id = query.get("cook_id")
    dispatcher_id = query.get("dispatcher_id")
    driver_id = query.get("driver_id")

    orders = dynamodb.Table(resource_name("orders"))

    if client_id != None:
        resp = orders.query(
            IndexName="tenant-client-idx",
            KeyConditionExpression=(
                Key("tenant_id").eq(tenant_id)
                & Key("client_id#created_at").begins_with(f"{client_id}#")
            ),
            ScanIndexForward=True,
        )
    elif cook_id != None:
        resp = orders.query(
            IndexName="tenant-cook-idx",
            KeyConditionExpression=(
                Key("tenant_id").eq(tenant_id)
                & Key("cook_id#created_at").begins_with(f"{cook_id}#")
            ),
            ScanIndexForward=True,
            FilterExpression=Attr("status").begins_with(status),
        )
    elif dispatcher_id != None:
        resp = orders.query(
            IndexName="tenant-dispatcher-idx",
            KeyConditionExpression=(
                Key("tenant_id").eq(tenant_id)
                & Key("dispatcher_id#created_at").begins_with(f"{dispatcher_id}#")
            ),
            ScanIndexForward=True,
            FilterExpression=Attr("status").begins_with(status),
        )
    elif driver_id != None:
        resp = orders.query(
            IndexName="tenant-driver-idx",
            KeyConditionExpression=(
                Key("tenant_id").eq(tenant_id)
                & Key("driver_id#created_at").begins_with(f"{driver_id}#")
            ),
            ScanIndexForward=True,
            FilterExpression=Attr("status").begins_with(status),
        )
    elif status:
        resp = orders.query(
            IndexName="tenant-status-idx",
            KeyConditionExpression=(
                Key("tenant_id").eq(tenant_id)
                & Key("status#created_at").begins_with(f"{status}#")
            ),
            ScanIndexForward=True,
        )
    elif last_key:
        resp = orders.query(
            IndexName="tenant-created-at-idx",
            KeyConditionExpression=Key("tenant_id").eq(tenant_id),
            ScanIndexForward=True,
            ExclusiveStartKey=last_key,
            Limit=limit,
        )
    else:
        resp = orders.query(
            IndexName="tenant-created-at-idx",
            KeyConditionExpression=Key("tenant_id").eq(tenant_id),
            ScanIndexForward=True,
            Limit=limit,
        )

    orders = resp["Items"]

    new_last_key = resp.get("LastEvaluatedKey")

    return response(
        200,
        {
            "items": orders,
            "next_key": to_json(new_last_key) if new_last_key else None,
        },
    )
