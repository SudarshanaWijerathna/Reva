def check_missing_node(state):
    required = ["property_type", "location"]
    missing = [f for f in required if not state.get("inputs", {}).get(f)]
    return {"missing_fields": missing}
