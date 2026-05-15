def check_missing_node(state):
    required = state.get("missing_fields", [])
    missing = [f for f in required if not state.get("inputs", {}).get(f)]
    return {"missing_fields": missing}
