from decimal import Decimal
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel


class UserRole(str, Enum):
    client = "client"
    cook = "cook"
    dispatcher = "dispatcher"
    driver = "driver"
    admin = "admin"


class AuthorizedUser(BaseModel):
    tenant_id: str
    user_id: str
    email: str
    username: str
    role: UserRole


class User(BaseModel):
    tenant_id: str
    user_id: str
    email: str
    username: str
    role: UserRole


class Product(BaseModel):
    tenant_id: str
    product_id: str
    name: str
    price: Decimal
    image_url: Optional[str] = None


class OrderItem(BaseModel):
    product: Product
    quantity: int


class OrderStatus(str, Enum):
    wait_for_cook = "wait_for_cook"
    cooking = "cooking"
    wait_for_dispatcher = "wait_for_dispatcher"
    dispatching = "dispatching"
    wait_for_deliverer = "wait_for_deliverer"
    delivering = "delivering"
    complete = "complete"


class OrderHistoryEntry(BaseModel):
    user: AuthorizedUser
    status: OrderStatus
    date: str


class Order(BaseModel):
    tenant_id: str
    order_id: str
    client_id: str
    client: AuthorizedUser
    items: list[OrderItem]
    status: OrderStatus
    execution_arn: Optional[str] = None
    task_token: Optional[str] = None
    created_at: str

    cook_id: Optional[str] = None
    cook: Optional[User] = None
    dispatcher_id: Optional[str] = None
    dispatcher: Optional[User] = None
    driver_id: Optional[str] = None
    driver: Optional[User] = None

    history: list[OrderHistoryEntry] = []


class FullOrder(Order):
    execution_history: Optional[Any] = None


class OrderSubscription(BaseModel):
    tenant_id: str
    order_id: Optional[str] = None
    connection_id: str
    connected_at: int


class WebSocketMessageKind(str, Enum):
    subscription_success = "subscription_success"
    subscription_failed = "subscription_failed"
    order_created = "order_created"
    order_status_updated = "order_status_updated"


class WebSocketMessage(BaseModel):
    kind: WebSocketMessageKind
    data: dict
