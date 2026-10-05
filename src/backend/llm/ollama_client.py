import os
import re
import json
import requests
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field

from backend.models import (
    MachineProfile,
    Parameter,
    NumberConfig,
    CategoryConfig,
    BooleanConfig,
    TextConfig,
    DatetimeConfig
)
from backend.llm.keyword_parser import parse_description_with_keywords


class ParsedMachineResponse(BaseModel):
    name: str = Field(default="Custom Machine", description="Extracted short name for the machine")
    suggested_domain: str = Field(default="IoT / Manufacturing", description="Suggested domain template")
    parameters: List[Parameter] = Field(default_factory=list, description="Extracted sensor and input parameters")


class LLMClient:
    """Abstract interface for LLM extraction clients."""
    def parse_machine(self, description: str) -> Dict[str, Any]:
        raise NotImplementedError()

    def get_status(self) -> Dict[str, Any]:
        raise NotImplementedError()


SYSTEM_PROMPT = """You are an expert industrial IoT and dataset schema extraction engineer.
Your task is to parse a text description of a machine, equipment, or business system into a structured list of inputs/sensors/parameters and a suggested domain.

RULES:
1. Return ONLY inputs that are explicitly mentioned or clearly implied in the user paragraph.
2. Do not invent unrelated sensors.
3. Assign sensible default min, max ranges, units, and categories.
4. Parameter types must be one of: "number", "category", "text", "boolean", "datetime".
5. For "number" parameters, min must be strictly lower than max.
6. For "category" parameters, provide at least 2 distinct non-empty string values in values[].
7. For "boolean" parameters, true_share must be between 0 and 100.
8. Parameter names must be unique (case-insensitive).
9. Suggested domain must be one of: "IoT / Manufacturing", "Logistics", "Finance", "Healthcare", "E-commerce".

WORKED EXAMPLE 1:
Input paragraph:
"A water pump station with a temperature sensor (0-100 C), pressure gauge (1-10 bar), flow rate meter, operating mode (idle/running/error), emergency stop button, and 5-second interval timestamps."
Output JSON:
{
  "name": "Water Pump Station",
  "suggested_domain": "IoT / Manufacturing",
  "parameters": [
    {"name": "temperature", "type": "number", "number": {"min": 0.0, "max": 100.0, "unit": "°C", "distribution": "normal"}},
    {"name": "pressure", "type": "number", "number": {"min": 1.0, "max": 10.0, "unit": "bar", "distribution": "uniform"}},
    {"name": "flow_rate", "type": "number", "number": {"min": 5.0, "max": 100.0, "unit": "L/min", "distribution": "normal"}},
    {"name": "operating_mode", "type": "category", "category": {"values": ["idle", "running", "error"]}},
    {"name": "emergency_stop", "type": "boolean", "boolean": {"true_share": 10.0}},
    {"name": "timestamp", "type": "datetime", "datetime": {"interval": "every 5 seconds"}}
  ]
}

WORKED EXAMPLE 2:
Input paragraph:
"A smart vending machine that tracks item inventory stock level, internal temperature, payment method (cash/card/mobile), network connectivity status (connected/disconnected), and door open sensor."
Output JSON:
{
  "name": "Smart Vending Machine",
  "suggested_domain": "IoT / Manufacturing",
  "parameters": [
    {"name": "inventory_stock", "type": "number", "number": {"min": 0.0, "max": 50.0, "unit": "items", "distribution": "uniform"}},
    {"name": "internal_temp", "type": "number", "number": {"min": 2.0, "max": 8.0, "unit": "°C", "distribution": "normal"}},
    {"name": "payment_method", "type": "category", "category": {"values": ["cash", "card", "mobile"]}},
    {"name": "network_status", "type": "category", "category": {"values": ["connected", "disconnected"]}},
    {"name": "door_open", "type": "boolean", "boolean": {"true_share": 15.0}}
  ]
}
"""


class OllamaClient(LLMClient):
    def __init__(self):
        self.ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434").rstrip("/")
        self.configured_model = os.getenv("OLLAMA_MODEL", "").strip()
        self.timeout = int(os.getenv("OLLAMA_TIMEOUT_SECONDS", "60"))

    def get_status(self) -> Dict[str, Any]:
        reachable = False
        models_installed = []
        model_in_use = None
        using_fallback = True

        try:
            res = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
            if res.status_code == 200:
                reachable = True
                data = res.json()
                models_installed = [m.get("name") for m in data.get("models", []) if isinstance(m, dict)]

                if self.configured_model and self.configured_model in models_installed:
                    model_in_use = self.configured_model
                    using_fallback = False
                elif models_installed:
                    chat_models = [m for m in models_installed if "embed" not in m.lower()]
                    if chat_models:
                        model_in_use = chat_models[0]
                        using_fallback = False
                    elif models_installed:
                        model_in_use = models_installed[0]
                        using_fallback = False
        except Exception:
            reachable = False
            using_fallback = True

        return {
            "reachable": reachable,
            "models_installed": models_installed,
            "model_in_use": model_in_use,
            "using_fallback": using_fallback
        }

    def _strip_think_tags(self, text: str) -> str:
        """Strip <think>...</think> tags if reasoning model is used."""
        return re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()

    def parse_machine(self, description: str) -> Dict[str, Any]:
        """
        Parse machine description using local Ollama model with structured JSON output,
        retrying once on malformed JSON, falling back cleanly to keyword parser on failure.
        """
        if not description or not description.strip():
            raise ValueError("Describe your machine first")

        words = description.strip().split()
        if len(words) < 8:
            raise ValueError("Add a little more detail so we can find the inputs")

        status = self.get_status()
        if not status["reachable"] or not status["model_in_use"]:
            # Fall back to keyword parser
            fallback_res = parse_description_with_keywords(description)
            fallback_res["notice"] = "Local AI offline or model missing, using basic keyword parser"
            return fallback_res

        model_name = status["model_in_use"]
        json_schema = ParsedMachineResponse.model_json_schema()

        payload = {
            "model": model_name,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Extract parameters from this paragraph:\n\n{description}"}
            ],
            "stream": False,
            "keep_alive": "30m",
            "format": json_schema,
            "options": {
                "temperature": 0
            }
        }

        # Attempt call with 1 retry on parse failure
        for attempt in range(2):
            try:
                res = requests.post(f"{self.ollama_url}/api/chat", json=payload, timeout=self.timeout)
                if res.status_code == 200:
                    body = res.json()
                    raw_content = body.get("message", {}).get("content", "")
                    clean_content = self._strip_think_tags(raw_content)

                    # Parse JSON
                    data = json.loads(clean_content)
                    parsed_obj = ParsedMachineResponse.model_validate(data)

                    # Validate parameter names uniqueness & minimum parameter requirement
                    if not parsed_obj.parameters:
                        if attempt == 0:
                            continue
                        break

                    # Construct MachineProfile parameters list
                    mp = MachineProfile(
                        name=parsed_obj.name,
                        description=description,
                        suggested_domain=parsed_obj.suggested_domain,
                        domain=parsed_obj.suggested_domain,
                        parameters=parsed_obj.parameters
                    )

                    return {
                        "name": mp.name,
                        "description": mp.description,
                        "suggested_domain": mp.suggested_domain,
                        "domain": mp.domain,
                        "parameters": [p.model_dump() for p in mp.parameters],
                        "using_fallback": False,
                        "model_used": model_name
                    }
            except Exception as err:
                if attempt == 0:
                    continue

        # If Ollama parsing failed after retry or threw exception, fall back gracefully
        fallback_res = parse_description_with_keywords(description)
        fallback_res["notice"] = f"Local AI model ({model_name}) produced invalid output, using basic keyword parser"
        return fallback_res
