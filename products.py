"""calculator; no bank API."""
import math
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field
ProductId = Literal["demo-cdb", "demo-lci", "demo-lca"]
class Product(BaseModel):
    model_config = ConfigDict(frozen=True)
    id: ProductId
    annual_rate: float
    minimum: float
    lock_days: int
    maturity_days: int
    description_pt: str
    description_en: str

PRODUCTS = {
    "demo-cdb": Product(id="demo-cdb", annual_rate=0.12, minimum=100,
        lock_days=0, maturity_days=730,
        description_pt="CDB: voce empresta dinheiro ao banco emissor.",
        description_en="CDB: you lend money to the issuing bank."),
    "demo-lci": Product(id="demo-lci", annual_rate=0.10, minimum=1000,
        lock_days=180, maturity_days=180,
        description_pt="LCI: titulo bancario ligado ao credito imobiliario.",
        description_en="LCI: a bank-issued security linked to real estate credit."),
    "demo-lca": Product(id="demo-lca", annual_rate=0.105, minimum=1000,
        lock_days=360, maturity_days=360,
        description_pt="LCA: titulo bancario ligado ao credito do agronegocio.",
        description_en="LCA: a bank-issued security linked to agribusiness credit."),
}

class Scenario(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    amount: float = Field(default=5000, ge=1, le=1_000_000)
    days: int = Field(default=180, ge=1, le=730)
    assumed_tax_rate: float = Field(default=0, ge=0, le=0.30)
    needs_daily_liquidity: bool = True

class Simulation(BaseModel):
    product_id: ProductId
    annual_rate: float
    amount: float
    days: int
    assumed_tax_rate: float
    matches_filters: bool
    reasons: list[str]
    estimated_net_total: float 
def simulate(product: Product, scenario: Scenario) -> Simulation:
    reasons = []
    if scenario.amount < product.minimum:
        reasons.append("below_minimum")
    if scenario.days < product.lock_days:
        reasons.append("locked_at_requested_date")
    if scenario.days > product.maturity_days:
        reasons.append("beyond_maturity_no_reinvestment")
    can_calculate = not reasons
    if scenario.needs_daily_liquidity and product.lock_days:
        reasons.append("no_daily_liquidity")
    total = None
    if can_calculate:
        gain = scenario.amount * math.expm1(
            math.log1p(product.annual_rate) * scenario.days / 365
        )
        total = round(scenario.amount + gain * (1 - scenario.assumed_tax_rate), 2)
    return Simulation(product_id=product.id, annual_rate=product.annual_rate,
        amount=scenario.amount, days=scenario.days,
        assumed_tax_rate=scenario.assumed_tax_rate,
        matches_filters=not reasons, reasons=reasons, estimated_net_total=total)
