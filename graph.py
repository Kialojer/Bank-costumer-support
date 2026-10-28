"""Small LangGraph workflow in the style of the telecom portfolio."""

kiarash torabi .n 
28/10/2026
from typing import Literal, TypedDict
from unicodedata import combining, normalize
from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel, ConfigDict, Field
from products import PRODUCTS, ProductId, Scenario, Simulation, simulate

class Message(BaseModel):
    model_config = ConfigDict(extra="forbid")
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=2000, pattern=r"\S")
class DemoMessage(BaseModel):
    model_config = ConfigDict(extra="forbid")
    message: str = Field(min_length=1, max_length=1500, pattern=r"\S")
    language: Literal["pt-BR", "en"] = "pt-BR"
    product_id: ProductId = "demo-cdb"
    scenario: Scenario = Field(default_factory=Scenario)
    history: list[Message] = Field(default_factory=list, max_length=6)

class AgentState(TypedDict, total=False):
    request: DemoMessage
    intent: Literal["support", "simulate", "explain", "greeting"]
    reply: str
    simulation: Simulation
    handoff: bool
    queue: str
    use_llm: bool
    mode: Literal["demo", "openai", "fallback"]

def normalized(text: str) -> str:
    return "".join(c for c in normalize("NFKD", text.casefold()) if not combining(c))

def classify(state: AgentState) -> dict:
    text = normalized(state["request"].message)
    if any(word in text for word in ("atendente", "humano", "human", "support", "fraude", "fraud")):
        intent = "support"
    elif any(word in text for word in ("simul", "quanto", "render")):
        intent = "simulate"
    elif text.strip(" !?.") in ("oi", "ola", "hello", "hi"):
        intent = "greeting"
    else:
        intent = "explain"
    return {"intent": intent}
def support(state: AgentState) -> dict:
    pt = state["request"].language == "pt-BR"
    reply = ("Demonstracao: procure o canal oficial do seu banco. Nenhuma transferencia foi realizada."
             if pt else "Demo: contact your bank through its official channel. No transfer was made.")
    return {"reply": reply, "handoff": True, "queue": "bank_support_demo"}

def greeting(state: AgentState) -> dict:
    pt = state["request"].language == "pt-BR"
    return {"reply": ("Ola! Posso explicar CDB, LCI e LCA ficticios ou simular o produto selecionado."
                     if pt else "Hello! I can explain fictional CDB, LCI and LCA products or simulate the selected offer.")}

def explain(state: AgentState) -> dict:
    request = state["request"]
    product = PRODUCTS[request.product_id]
    pt = request.language == "pt-BR"
    description = product.description_pt if pt else product.description_en
    reply = (f"DEMO: {description} Taxa anual ficticia: {product.annual_rate:.1%}. "
             if pt else
             f"DEMO: {description} Fictional annual rate: {product.annual_rate:.1%}. "
    return {"reply": reply}
def simulate_offer(state: AgentState) -> dict:
    request = state["request"]
    result = simulate(PRODUCTS[request.product_id], request.scenario)
    pt = request.language == "pt-BR"
    if result.estimated_net_total is None:
        reply = ("Sem estimativa de saque para este cenario." if pt else
                 "No withdrawal estimate for this scenario.")
    else:
        label = "Total estimado" if pt else "Estimated total"
        reply = f"{label}: R$ {result.estimated_net_total:.2f}."
    caution = ("Dados ficticios. Imposto informado e uma premissa; sem taxas, IOF ou riscos reais."
               if pt else "Fictional data. Tax is an input assumption; fees, IOF and real risks are excluded.")
    # The structured result always exposes why a product fails a filter.
    if result.reasons:
        reply += (" Filtros nao atendidos: " if pt else "Unmet filters: ") + ", ".join(result.reasons) + "."
    return {"reply": reply + " " + caution, "simulation": result}

def optional_explanation(state: AgentState) -> dict:
    if not state["use_llm"]:
        return {}
    from llm import explain_with_openai
    request = state["request"]
    facts = {"product": PRODUCTS[request.product_id].model_dump(),
             "scenario": request.scenario.model_dump(),
             "simulation": state["simulation"].model_dump() if state["simulation"] else None}
    reply, mode = explain_with_openai(
        "Brazilian Portuguese" if request.language == "pt-BR" else "English",
        request.message, [m.model_dump() for m in request.history], facts, state["reply"])
    return {"reply": reply, "mode": mode}

# ۴. مسیرها مشخص‌اند؛ دیتابیس و ذخیره تاریخچه نداریم.
def build_graph():
    builder = StateGraph(AgentState)
    builder.add_node("classify", classify)
    builder.add_node("support", support)
    builder.add_node("greeting", greeting)
    builder.add_node("explain", explain)
    builder.add_node("simulate", simulate_offer)
    builder.add_node("optional_explanation", optional_explanation)
    builder.add_edge(START, "classify")
    builder.add_conditional_edges("classify", lambda s: s["intent"],
        {name: name for name in ("support", "greeting", "explain", "simulate")})
    for name in ("greeting", "explain", "simulate"):
        builder.add_edge(name, "optional_explanation")
    builder.add_edge("optional_explanation", END)
    builder.add_edge("support", END)
    return builder.compile()

graph = build_graph()

def respond(payload: DemoMessage, use_llm: bool = False) -> AgentState:
    return graph.invoke({"request": payload, "use_llm": use_llm, "mode": "demo","handoff": False, "queue": None, "simulation": None})
if __name__ == "__main__":
    result = respond(DemoMessage(message="Quanto rende?", language="pt-BR"))
    print(result["reply"])
