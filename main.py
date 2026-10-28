#kiarash
import os
from typing import Literal

from fastapi import FastAPI
from pydantic import BaseModel

from graph import DemoMessage, respond
from products import PRODUCTS, Product, Simulation

app = FastAPI(title="Bank Customer Support Demo", version="1.0.0")

class DemoReply(BaseModel):
    demo: bool = True
    product_id: str
    intent: str
    reply: str
    mode: Literal["demo", "openai", "fallback"]
    handoff: bool
    queue: str | None
    simulation: Simulation | None

@app.get("/health")
def health() -> dict:
    return {"status": "ok", "mode": "fictional-demo",
            "llm_enabled": os.getenv("USE_OPENAI", "false").lower() == "true"}

@app.get("/products", response_model=list[Product])
def products() -> list[Product]:
    return list(PRODUCTS.values())

@app.post("/webhook/demo", response_model=DemoReply)
def demo_webhook(payload: DemoMessage) -> DemoReply:
    use_llm = os.getenv("USE_OPENAI", "false").lower() == "true"
    result = respond(payload, use_llm=use_llm)
    return DemoReply(product_id=payload.product_id, intent=result["intent"],
        reply=result["reply"], mode=result["mode"], handoff=result["handoff"],
        queue=result["queue"], simulation=result["simulation"])
