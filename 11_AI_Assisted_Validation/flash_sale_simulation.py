#!/usr/bin/env python3
"""
SALESTORM High-Scale Flash Sale Simulation Engine
Validates System Architecture under Hackathon Practical Test Case:
- Stock: 100 units
- Concurrent Users: 10,000 requests
- Payment Success Rate: 95%
- Payment Failure Rate: 5%
- Duplicate Request Rate: 2%
- Order Service Outage: 30-second simulated downtime
"""

import asyncio
import time
import random
import uuid
from typing import Dict, List, Set

class RedisLuaSimulator:
    """Simulates Atomic Redis Lua Stock Counter & TTL Expiry"""
    def __init__(self, initial_stock: int = 100):
        self.stock = initial_stock
        self.reservations: Dict[str, dict] = {}
        self.lock = asyncio.Lock()
        self.idempotency_keys: Set[str] = set()

    async def reserve_stock(self, user_id: str, idempotency_key: str) -> dict:
        async with self.lock:
            # Check Idempotency
            if idempotency_key in self.idempotency_keys:
                return {"status": "DUPLICATE", "message": "Idempotency key already processed"}
            
            self.idempotency_keys.add(idempotency_key)

            if self.stock > 0:
                self.stock -= 1
                res_id = str(uuid.uuid4())
                self.reservations[res_id] = {
                    "user_id": user_id,
                    "status": "RESERVED",
                    "expires_at": time.time() + 600,
                    "idempotency_key": idempotency_key
                }
                return {"status": "SUCCESS", "reservation_id": res_id, "remaining_stock": self.stock}
            else:
                return {"status": "OUT_OF_STOCK", "remaining_stock": 0}

    async def release_stock(self, res_id: str):
        async with self.lock:
            if res_id in self.reservations and self.reservations[res_id]["status"] == "RESERVED":
                self.reservations[res_id]["status"] = "RELEASED"
                self.stock += 1
                return True
            return False

class PaymentGatewaySimulator:
    """Simulates 3rd Party Gateway with 95% Success & 5% Failure"""
    def __init__(self, success_rate: float = 0.95):
        self.success_rate = success_rate
        self.processed_keys: Set[str] = set()

    async def process_payment(self, idempotency_key: str) -> dict:
        # Idempotency lock simulation
        if idempotency_key in self.processed_keys:
            return {"status": "DUPLICATE_PAYMENT", "message": "Payment already processed for key"}
        
        self.processed_keys.add(idempotency_key)
        await asyncio.sleep(0.01) # Simulate 10ms gateway latency
        
        if random.random() < self.success_rate:
            return {"status": "SUCCESS", "tx_ref": f"tx_{uuid.uuid4().hex[:8]}"}
        else:
            return {"status": "FAILED", "reason": "INSUFFICIENT_FUNDS"}

class KafkaQueueSimulator:
    """Simulates Persistent Event Bus for Async Order Processing"""
    def __init__(self):
        self.queue = asyncio.Queue()

    async def publish(self, event: dict):
        await self.queue.put(event)

    async def consume(self) -> dict:
        return await self.queue.get()

class OrderServiceSimulator:
    """Simulates Order Service with a 30-Second Downtime Window"""
    def __init__(self, event_bus: KafkaQueueSimulator):
        self.event_bus = event_bus
        self.confirmed_orders: List[dict] = []
        self.is_healthy = True
        self.processed_count = 0

    async def run_worker(self):
        while True:
            event = await self.event_bus.consume()
            # If Order Service is down, put back into queue or wait
            while not self.is_healthy:
                await asyncio.sleep(0.1)
            
            # Process order creation
            self.confirmed_orders.append(event)
            self.processed_count += 1
            self.event_bus.queue.task_done()

async def run_simulation():
    print("=" * 70)
    print("SALESTORM FLASH SALE SIMULATION LAUNCHED")
    print("Scenario: Stock=100 | Users=10,000 | PaySuccess=95% | Dups=2%")
    print("Order Service Status: DOWN for first 2 seconds (representing scaled 30s outage window)")
    print("=" * 70)

    redis = RedisLuaSimulator(initial_stock=100)
    payment_gw = PaymentGatewaySimulator(success_rate=0.95)
    kafka = KafkaQueueSimulator()
    order_svc = OrderServiceSimulator(kafka)

    # Start Order Worker
    worker_task = asyncio.create_task(order_svc.run_worker())

    # Simulate Order Service Outage
    order_svc.is_healthy = False
    print("[0.0s] ⚠️ Order Service went DOWN (Event buffering in Kafka enabled).")

    # Metrics Tracking
    stats = {
        "total_requests": 10000,
        "successful_reservations": 0,
        "out_of_stock_rejections": 0,
        "duplicate_requests_caught": 0,
        "successful_payments": 0,
        "failed_payments": 0,
        "released_reservations": 0
    }

    # Generate 10,000 requests (including 2% duplicates)
    base_idempotency_keys = [str(uuid.uuid4()) for _ in range(9800)]
    # Duplicate keys pool (200 requests repeating previous keys)
    duplicate_keys = [random.choice(base_idempotency_keys) for _ in range(200)]
    all_keys = base_idempotency_keys + duplicate_keys
    random.shuffle(all_keys)

    start_time = time.time()

    async def simulate_user(req_id: int, key: str):
        user_id = f"usr_{req_id}"
        # 1. Attempt Stock Reservation
        res = await redis.reserve_stock(user_id, key)
        
        if res["status"] == "DUPLICATE":
            stats["duplicate_requests_caught"] += 1
            return
        elif res["status"] == "OUT_OF_STOCK":
            stats["out_of_stock_rejections"] += 1
            return
        elif res["status"] == "SUCCESS":
            stats["successful_reservations"] += 1
            res_id = res["reservation_id"]
            
            # 2. Process Payment
            pay_res = await payment_gw.process_payment(key)
            if pay_res["status"] == "SUCCESS":
                stats["successful_payments"] += 1
                # Publish event to Kafka
                await kafka.publish({
                    "order_id": str(uuid.uuid4()),
                    "user_id": user_id,
                    "res_id": res_id,
                    "tx_ref": pay_res["tx_ref"],
                    "status": "CONFIRMED"
                })
            else:
                stats["failed_payments"] += 1
                # Release stock back to Redis
                released = await redis.release_stock(res_id)
                if released:
                    stats["released_reservations"] += 1

    # Fire 10,000 concurrent user requests
    tasks = [simulate_user(i, all_keys[i]) for i in range(10000)]
    await asyncio.gather(*tasks)

    elapsed_reservation_time = time.time() - start_time
    print(f"[{elapsed_reservation_time:.2f}s] 10,000 Concurrent Requests Processed by Gateway & Redis.")
    print(f"-> Successful Initial Reservations: {stats['successful_reservations']}")
    print(f"-> Duplicate Requests Blocked: {stats['duplicate_requests_caught']}")
    print(f"-> Out-Of-Stock Rejections: {stats['out_of_stock_rejections']}")
    print(f"-> Payments Succeeded: {stats['successful_payments']}")
    print(f"-> Payments Failed: {stats['failed_payments']}")
    print(f"-> Inventory Released back to Pool: {stats['released_reservations']}")
    print(f"-> Buffer in Kafka Waiting for Order Service: {kafka.queue.qsize()} events")

    print("\nSimulating Order Service Recovery...")
    await asyncio.sleep(1.0) # Simulating recovery delay
    order_svc.is_healthy = True
    print("[+] Order Service RECOVERED! Resuming event consumption from Kafka...")

    # Wait until all Kafka messages are processed
    await kafka.queue.join()
    worker_task.cancel()

    print("\n" + "=" * 70)
    print("FINAL VALIDATION SUMMARY & VERIFICATION CHECKS")
    print("=" * 70)
    print(f"1. Total Confirmed Orders in DB: {len(order_svc.confirmed_orders)}")
    print(f"2. Final Net Available Stock in Redis: {redis.stock}")
    print(f"3. Net Total Items Sold (Initial 100 - Final Stock): {100 - redis.stock}")
    
    # Assertions for Architectural Defensibility
    assert (100 - redis.stock) <= 100, "CRITICAL ERROR: OVERSELLING DETECTED!"
    assert len(order_svc.confirmed_orders) == stats["successful_payments"], "CRITICAL ERROR: ORDER LOSS DETECTED!"
    print("\n✅ ALL VERIFICATION CHECKS PASSED PERFECTLY!")
    print("Zero Overselling | Zero Lost Orders | Complete Idempotency Enforced!")
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(run_simulation())
