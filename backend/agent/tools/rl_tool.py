from backend.core.cache_service import get_reccomendations

def get_recommendations(property_type):
    reccpmendations= get_reccomendations()
    if not reccpmendations:
        return {"error": "No recommendations available"}
    action_labels = reccpmendations.get("action_labels", [])
    if property_type == "land":
        return {"recommendation for land": action_labels[0] if len(action_labels) > 0 else "No recommendation"}
    elif property_type == "housing":
        return {"recommendation for housing": action_labels[1] if len(action_labels) > 1 else "No recommendation"}
    elif property_type == "rental":
        return {"recommendation for rental": action_labels[2] if len(action_labels) > 2 else "No recommendation"}
    
