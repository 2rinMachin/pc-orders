import json
import uuid
from datetime import datetime, timezone

import boto3
from pydantic import BaseModel

from common import PROJECT_NAME, STAGE, parse_body, resource_name, response, to_json
from schemas import AuthorizedUser, Order, OrderItem, OrderStatus


class CreateOrderRequestItem(BaseModel):
    product_id: str
    quantity: int


class CreateOrderRequest(BaseModel):
    items: list[CreateOrderRequestItem]


events = boto3.client("events")
dynamodb = boto3.resource("dynamodb")
orders = dynamodb.Table(resource_name("orders"))

lambda_client = boto3.client("lambda")


def handler(event, context):
    user = AuthorizedUser(**event["requestContext"]["authorizer"])
    tenant_id = event["pathParameters"]["tenant_id"]

    data, err = parse_body(CreateOrderRequest, event)
    if err != None:
        return err

    assert data != None

    if len(data.items) == 0:
        return response(400, {"message": "Order must have at least 1 item."})

    order_items = []

    for item in data.items:
        resp = lambda_client.invoke(
            FunctionName=f"{PROJECT_NAME}-catalog-{STAGE}-get_product_internal",
            InvocationType="RequestResponse",
            Payload=to_json(
                {"tenant_id": tenant_id, "product_id": item.product_id}
            ).encode("utf-8"),
        )

        if not "Payload" in resp:
            return response(500, {"message": "Internal server error."})

        payload = json.loads(resp["Payload"].read().decode("utf-8"))

        if payload == None:
            return response(400, {"message": "A product does not exist."})

        order_items.append(
            OrderItem(
                product=payload,
                quantity=item.quantity,
            )
        )

    new_order = Order(
        tenant_id=tenant_id,
        order_id=str(uuid.uuid4()),
        client_id=user.user_id,
        client=user,
        items=order_items,
        status=OrderStatus.wait_for_cook,
        created_at=datetime.now(timezone.utc).isoformat(),
    )

    orders.put_item(Item=new_order.model_dump(exclude_none=True))

    events.put_events(
        Entries=[
            {
                "Source": f"{PROJECT_NAME}-{STAGE}.orders",
                "DetailType": "order.created",
                "Detail": new_order.model_dump_json(),
            }
        ]
    )

    return response(201, new_order.model_dump_json())
