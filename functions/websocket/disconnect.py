import boto3
from boto3.dynamodb.conditions import Key
from pydantic import ValidationError

from common import table_name
from schemas import OrderSubscription

dynamodb = boto3.resource("dynamodb")
subscriptions = dynamodb.Table(table_name("ws-order-subscriptions"))


def handler(event, context):
    connection_id = event["requestContext"]["connectionId"]

    resp = subscriptions.query(
        IndexName="connection-id-index",
        KeyConditionExpression=Key("connection_id").eq(connection_id),
        Limit=1,
    )

    items: list[dict] = resp.get("Items", [])

    for item in items:
        sub = None

        try:
            sub = OrderSubscription(**item)
        except (KeyError, ValidationError):
            continue

        subscriptions.delete_item(
            Key={"tenant_id": sub.tenant_id, "connection_id": sub.connection_id}
        )
