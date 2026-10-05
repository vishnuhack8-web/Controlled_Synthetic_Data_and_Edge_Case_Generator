import re
from typing import Dict, Any, List
from backend.models import Parameter, NumberConfig, CategoryConfig, BooleanConfig, DatetimeConfig, TextConfig


def parse_description_with_keywords(description: str) -> Dict[str, Any]:
    """
    Fallback deterministic parser.
    Parses machine description paragraph into parameters and suggested domain.
    """
    if not description or not description.strip():
        raise ValueError("Describe your machine first")

    words = description.strip().split()
    if len(words) < 8:
        raise ValueError("Add a little more detail so we can find the inputs")

    text = description.lower()

    # Determine suggested domain based on keywords
    suggested_domain = "IoT / Manufacturing"
    if any(k in text for k in ["logistics", "shipment", "truck", "warehouse", "delivery", "fleet", "gps"]):
        suggested_domain = "Logistics"
        default_name = "Fleet Vehicle"
    elif any(k in text for k in ["finance", "atm", "transaction", "payment", "bank", "account", "credit", "fraud"]):
        suggested_domain = "Finance"
        default_name = "Banking / ATM System"
    elif any(k in text for k in ["health", "patient", "heart", "vital", "hospital", "medical", "ecg"]):
        suggested_domain = "Healthcare"
        default_name = "Medical Monitor"
    elif any(k in text for k in ["e-commerce", "ecommerce", "cart", "checkout", "store", "product", "user session"]):
        suggested_domain = "E-commerce"
        default_name = "E-commerce Platform"
    else:
        suggested_domain = "IoT / Manufacturing"
        default_name = "Industrial Machine"

    parameters: List[Parameter] = []

    # Check for specific numeric sensors & metrics
    # Temperature
    if any(k in text for k in ["temp", "temperature", "heat", "thermal"]):
        parameters.append(Parameter(
            name="temperature",
            type="number",
            number=NumberConfig(min=10.0, max=95.0, unit="°C", distribution="normal")
        ))

    # Pressure
    if any(k in text for k in ["pressure", "psi", "bar"]):
        parameters.append(Parameter(
            name="pressure",
            type="number",
            number=NumberConfig(min=1.0, max=10.0, unit="bar", distribution="uniform")
        ))

    # Vibration / RPM / Speed / Flow Rate
    if any(k in text for k in ["vibration", "vibrate", "freq", "hz"]):
        parameters.append(Parameter(
            name="vibration",
            type="number",
            number=NumberConfig(min=0.1, max=15.0, unit="mm/s", distribution="uniform")
        ))

    if any(k in text for k in ["flow", "flow rate", "gpm", "l/min"]):
        parameters.append(Parameter(
            name="flow_rate",
            type="number",
            number=NumberConfig(min=5.0, max=120.0, unit="L/min", distribution="normal")
        ))

    if any(k in text for k in ["rpm", "rotation", "speed", "velocity"]):
        parameters.append(Parameter(
            name="motor_speed",
            type="number",
            number=NumberConfig(min=500.0, max=3500.0, unit="RPM", distribution="normal")
        ))

    # Voltage / Power / Current / Battery
    if any(k in text for k in ["voltage", "power", "current", "battery", "amp", "watt"]):
        parameters.append(Parameter(
            name="power_draw",
            type="number",
            number=NumberConfig(min=12.0, max=480.0, unit="W", distribution="uniform")
        ))

    # Inventory / Items / Quantity / Stock / Volume
    if any(k in text for k in ["inventory", "stock", "items", "capacity", "volume", "fill level"]):
        parameters.append(Parameter(
            name="fill_level",
            type="number",
            number=NumberConfig(min=0.0, max=100.0, unit="%", distribution="uniform")
        ))

    # Financial / Transaction amount / Balance
    if any(k in text for k in ["amount", "balance", "price", "cost", "withdrawal"]):
        parameters.append(Parameter(
            name="transaction_amount",
            type="number",
            number=NumberConfig(min=10.0, max=5000.0, unit="USD", distribution="normal")
        ))

    # Network Status vs Machine/Operational Status keyword handling (Rule 8/10 distinction)
    # Check explicitly for network status
    if "network status" in text or "network" in text or "connectivity" in text or "wifi" in text:
        parameters.append(Parameter(
            name="network_status",
            type="category",
            category=CategoryConfig(values=["connected", "disconnected", "degraded"], weights=[0.85, 0.10, 0.05])
        ))

    # Check for operational / machine status (without confusing with network status)
    if any(k in text for k in ["machine status", "operational status", "state", "mode", "operation mode"]) or (
        "status" in text and "network" not in text and "connectivity" not in text
    ):
        parameters.append(Parameter(
            name="machine_status",
            type="category",
            category=CategoryConfig(values=["running", "idle", "maintenance", "error"], weights=[0.70, 0.15, 0.10, 0.05])
        ))

    # Boolean flags
    if any(k in text for k in ["door", "hatch", "valve"]):
        parameters.append(Parameter(
            name="valve_open",
            type="boolean",
            boolean=BooleanConfig(true_share=60.0)
        ))

    if any(k in text for k in ["alarm", "alert", "warning light"]):
        parameters.append(Parameter(
            name="alarm_active",
            type="boolean",
            boolean=BooleanConfig(true_share=5.0)
        ))

    # Datetime / timestamp
    if any(k in text for k in ["interval", "periodically", "every", "real-time", "timestamp", "sensor", "pump", "machine", "device"]):
        parameters.append(Parameter(
            name="timestamp",
            type="datetime",
            datetime=DatetimeConfig(interval="every 5 seconds")
        ))

    # If no specific parameters matched, generate 2 default fallback parameters based on domain
    if not parameters:
        parameters = [
            Parameter(name="primary_sensor", type="number", number=NumberConfig(min=0.0, max=100.0, unit="units")),
            Parameter(name="operating_status", type="category", category=CategoryConfig(values=["normal", "alert"]))
        ]

    # Deduplicate parameter names (case-insensitive) just in case
    unique_params = []
    seen = set()
    for p in parameters:
        if p.name.lower() not in seen:
            seen.add(p.name.lower())
            unique_params.append(p)

    return {
        "name": default_name,
        "suggested_domain": suggested_domain,
        "parameters": unique_params,
        "using_fallback": True
    }
