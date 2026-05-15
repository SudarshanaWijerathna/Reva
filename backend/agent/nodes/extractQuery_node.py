from backend.agent.services.input_data_fetch import InputDataFetchService

def extract_query(state):
    data = InputDataFetchService(state).fetch_data()
    missing = state.get("missing_fields", [])

    '''
    {
    "property_type": "land",
    "location": "colombo"
    }
    '''

    return {
    "inputs": {field: data.get(field) for field in missing}
     }
