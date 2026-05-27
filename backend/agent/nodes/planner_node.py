from backend.agent.services.intent_classifier import IntentContextClassifier


def planner_node(state):

    #Context
    #Intent
    classifier = IntentContextClassifier(state)
    context = classifier.ContextClassifier()
    intent = classifier.IntentClassifier()
    intent_value = intent.get("intent", None) if isinstance(intent, dict) else None
    context_value = context.get("context", None) if isinstance(context, dict) else None
    requirements = {
        "prediction": ["property_type", "location"],
        "investment": ["property_type", "location"],
        "analysis": ["property_type", "location"]
    }

    return {
        "intent": intent_value,
        "context": context_value,
        "missing_fields": requirements.get(intent_value, []),
        "required_fields": requirements.get(intent_value, [])
        }
    
