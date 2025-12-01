import os

import boto3
from boto3.dynamodb.conditions import Attr, Key

from common import resource_name
from common.websocket import WEBSOCKET_ENDPOINT
from schemas import Order, OrderSubscription, WebSocketMessage, WebSocketMessageKind

dynamodb = boto3.resource("dynamodb")
subscriptions = dynamodb.Table(resource_name("ws-order-subscriptions"))
api_gw = boto3.client("apigatewaymanagementapi", endpoint_url=WEBSOCKET_ENDPOINT)


def handler(event, context):
    order = Order(**event["detail"])

    message = WebSocketMessage(
        kind=WebSocketMessageKind.order_status_updated,
        data=order.model_dump(),
    )
    message_data = message.model_dump_json()

    resp = subscriptions.query(
        KeyConditionExpression=Key("tenant_id").eq(order.tenant_id),
        FilterExpression=(
            Attr("order_id").eq(order.order_id) | Attr("order_id").eq(None)
        ),
    )

    items: list[dict] = resp["Items"]

    for item in items:
        try:
            sub = OrderSubscription(**item)

            if sub.order_id == None or sub.order_id == order.order_id:
                api_gw.post_to_connection(
                    ConnectionId=sub.connection_id,
                    Data=message_data,
                )
        except:
            pass
