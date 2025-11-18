import uuid

import boto3
from pydantic import BaseModel

from common import PROJECT_NAME, parse_body, response, table_name, to_json
from schemas import Order, OrderItem, OrderStatus


class CreateOrderRequestItem(BaseModel):
    item_id: str
    quantity: int


class CreateOrderRequest(BaseModel):
    items: list[CreateOrderRequestItem]


def handler(event, context):
    tenant_id = event["pathParameters"]["tenant_id"]

    data, err = parse_body(CreateOrderRequest, event)
    if err != None:
        return err

    assert data != None

    if len(data.items) == 0:
        return response(400, {"message": "Order must have at least 1 item."})

    dynamodb = boto3.resource("dynamodb")
    orders = dynamodb.Table(table_name("orders"))

    new_order = Order(
        tenant_id=tenant_id,
        order_id=str(uuid.uuid4()),
        items=[
            OrderItem(
                item_id=item.item_id,
                quantity=item.quantity,
            )
            for item in data.items
        ],
        status=OrderStatus.wait_for_cook,
    )

    new_order_dict = new_order.model_dump()

    orders.put_item(Item=new_order_dict)

    events = boto3.client("events")
    events.put_events(
        Entries=[
            {
                "Source": f"{PROJECT_NAME}.orders",
                "DetailType": "order.created",
                "Detail": to_json(new_order_dict),
            }
        ]
    )

    return response(201, new_order_dict)
