'''from backend.rl.agent_services import get_recommendation
from backend.core.cache_service import get_cached_sentiment

dummy_state = [
    # Property 0
    1.0, 0.5, 0.01, 0.2, 0.0, 10, 0.5, 3,
    # Property 1
    5.0, 0.3, 0.005, 0.03, 0.0, 3, 7, 12,
    # Property 2
    2.0, -0.2, -0.005, 0.04, 1.0, 1, 5, 2,
    # Cash
    1.2
    ]

idx, vec, labels, _, _ = get_recommendation(dummy_state)

print("Action Index:", idx)
print("Action Vector:", vec)
print("Recommendation:", labels)   ''' 
if __name__ == "__main__":
    from backend.core.cache_service import get_cached_sentiment
    print(get_cached_sentiment())