import os

import boto3

from common import resource_name
from schemas import Order

TOPIC_ARN = os.environ["ORDER_ARRIVALS_TOPIC_ARN"]


dynamodb = boto3.resource("dynamodb")
sns = boto3.client("sns")

orders = dynamodb.Table(resource_name("orders"))


def handler(event, context):
    resp = orders.get_item(
        Key={"tenant_id": event["tenant_id"], "order_id": event["order_id"]}
    )

    item: dict | None = resp.get("Item")

    if item != None:
        order = Order(**item)

        order_items = [
            f"- {item.product.name} x{item.quantity}" for item in order.items
        ]

        sns.publish(
            TopicArn=TOPIC_ARN,
            Subject="¡Tu pedido ha llegado!",
            Message=f"""
            Tu pedido ya está en tu puerta.

            Resumen del pedido:
            {"\n".join(order_items)}
            """,
            MessageAttributes={
                "tenant_id": {
                    "DataType": "String",
                    "StringValue": order.client.tenant_id,
                },
                "user_id": {
                    "DataType": "String",
                    "StringValue": order.client.user_id,
                },
            },
        )
