import json
from ai_service import get_default_service

svc = get_default_service()
print("Loaded keys:", svc.get_loaded_keys())
result = svc.generate_response(
    provider="cohere",
    model="command-xlarge-nightly",
    system_instruction="You are a helpful assistant.",
    conversation_history=[],
    user_message="Cohere test message from automated script.",
)
print(json.dumps(result, indent=2))
