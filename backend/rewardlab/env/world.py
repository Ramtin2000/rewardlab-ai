"""World generation: the tickets, orders and payments an episode runs on.

Each episode gets one target ticket drawn from a scenario, plus a few
distractor orders so the agent has to look things up instead of guessing.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from enum import Enum


class Scenario(str, Enum):
    # Each scenario has exactly one correct outcome, which the verifier checks.
    CANCELED_CONFIRMED = "canceled_confirmed"  # refund, then close
    DELIVERED_REFUND_REQUEST = "delivered_refund_request"  # no refund, close
    PAYMENT_FAILED = "payment_failed"  # nothing was charged, close
    ALREADY_REFUNDED = "already_refunded"  # don't double-refund, close


REFUND_EXPECTED = {
    Scenario.CANCELED_CONFIRMED: True,
    Scenario.DELIVERED_REFUND_REQUEST: False,
    Scenario.PAYMENT_FAILED: False,
    Scenario.ALREADY_REFUNDED: False,
}

COMPLAINTS = {
    Scenario.CANCELED_CONFIRMED: "I canceled order {order_id} but I still haven't gotten my money back.",
    Scenario.DELIVERED_REFUND_REQUEST: "Order {order_id} arrived but I changed my mind. Refund me please.",
    Scenario.PAYMENT_FAILED: "Order {order_id} says canceled. Was I charged? I want a refund if so.",
    Scenario.ALREADY_REFUNDED: "Where is my refund for order {order_id}??",
}


@dataclass
class Ticket:
    id: int
    customer_id: int
    order_id: int
    complaint: str
    status: str = "open"  # open | resolved


@dataclass
class Order:
    id: int
    customer_id: int
    status: str  # delivered | canceled
    amount: float


@dataclass
class Payment:
    order_id: int
    amount: float
    status: str  # confirmed | failed | refunded


@dataclass
class World:
    scenario: Scenario
    target_ticket_id: int
    tickets: dict[int, Ticket] = field(default_factory=dict)
    orders: dict[int, Order] = field(default_factory=dict)
    payments: dict[int, Payment] = field(default_factory=dict)

    @property
    def target_ticket(self) -> Ticket:
        return self.tickets[self.target_ticket_id]

    @property
    def refund_expected(self) -> bool:
        return REFUND_EXPECTED[self.scenario]


def generate_world(seed: int, scenario: Scenario | None = None) -> World:
    rng = random.Random(seed)
    scenario = scenario or rng.choice(list(Scenario))

    customer_id = rng.randint(100, 999)
    order_id = rng.randint(1000, 9999)
    ticket_id = rng.randint(1000, 1999)
    amount = float(rng.choice([19, 34, 49, 79, 129]))

    order_status, payment_status = {
        Scenario.CANCELED_CONFIRMED: ("canceled", "confirmed"),
        Scenario.DELIVERED_REFUND_REQUEST: ("delivered", "confirmed"),
        Scenario.PAYMENT_FAILED: ("canceled", "failed"),
        Scenario.ALREADY_REFUNDED: ("canceled", "refunded"),
    }[scenario]

    world = World(scenario=scenario, target_ticket_id=ticket_id)
    world.tickets[ticket_id] = Ticket(
        id=ticket_id,
        customer_id=customer_id,
        order_id=order_id,
        complaint=COMPLAINTS[scenario].format(order_id=order_id),
    )
    world.orders[order_id] = Order(order_id, customer_id, order_status, amount)
    world.payments[order_id] = Payment(order_id, amount, payment_status)

    # Distractors: other customers' delivered orders. Never the right thing to refund.
    for _ in range(3):
        other_id = rng.randint(1000, 9999)
        if other_id in world.orders:
            continue
        other_amount = float(rng.choice([19, 34, 49, 79, 129]))
        world.orders[other_id] = Order(other_id, rng.randint(100, 999), "delivered", other_amount)
        world.payments[other_id] = Payment(other_id, other_amount, "confirmed")

    return world
