import os
from typing import List, Dict, Optional

from dotenv import load_dotenv
import requests

try:
    import cohere
except Exception:
    cohere = None

# Load .env if present; if keys not found, fallback to .env.example for convenience
load_dotenv()
if not os.getenv("COHERE_API_KEY") and os.path.exists(".env.example"):
    # load example file without overriding real env vars
    load_dotenv(dotenv_path=".env.example", override=False)


class AIService:
    def __init__(self):
        # Read keys from environment (loaded from .env or .env.example)
        self.cohere_api_key = os.getenv("COHERE_API_KEY")
        self.hf_api_token = os.getenv("HUGGINGFACE_API_TOKEN")

    def get_loaded_keys(self) -> Dict[str, bool]:
        return {"cohere_loaded": bool(self.cohere_api_key), "huggingface_loaded": bool(self.hf_api_token)}

    def construct_prompt(self, system_instruction: str, conversation_history: List[Dict], user_message: str) -> str:
        parts = []
        if system_instruction:
            parts.append(f"System: {system_instruction}\n")

        # include recent conversation history (role: content)
        for msg in conversation_history[-10:]:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            parts.append(f"{role.title()}: {content}\n")

        parts.append(f"User: {user_message}\nAssistant:")
        return "\n".join(parts)

    def send_cohere(
        self,
        system_instruction: str,
        conversation_history: List[Dict],
        user_message: str,
        model: str = "command-xlarge-nightly",
        max_tokens: int = 200,
    ) -> Dict:
        # Prefer HTTP Chat API for Cohere (Generate API removed); support SDK if it has chat method
        if not self.cohere_api_key:
            return {"success": False, "error": "Missing COHERE_API_KEY in environment. Copy .env.example to .env or set COHERE_API_KEY in your environment."}

        # If SDK provides Chat, try to use it
        # Ensure model is a Cohere chat-capable model; if caller passed an HF model like 'gpt2', override it
        if model and model.lower().startswith("gpt"):
            model = "command-xlarge-nightly"

        try:
            if cohere is not None:
                client = cohere.Client(self.cohere_api_key)
                if hasattr(client, "chat"):
                    # construct messages from system, history, and current user message
                    messages = []
                    if system_instruction:
                        messages.append({"role": "system", "content": system_instruction})
                    for msg in conversation_history[-10:]:
                        r = msg.get("role", "user")
                        c = msg.get("content", "")
                        messages.append({"role": r, "content": c})
                    messages.append({"role": "user", "content": user_message})
                    resp = client.chat(model=model, messages=messages, max_tokens=max_tokens)
                    # SDK may return a nested structure
                    if hasattr(resp, "message") and getattr(resp.message, "content", None):
                        return {"success": True, "text": resp.message.content}
                    if hasattr(resp, "generations") and resp.generations:
                        gen = resp.generations[0]
                        text = getattr(gen, "text", None) or str(gen)
                        return {"success": True, "text": text}
        except Exception:
            # fall through to HTTP approach
            pass

        # HTTP fallback to Cohere Chat API (v2)
        url = "https://api.cohere.com/v2/chat"
        headers = {"Authorization": f"Bearer {self.cohere_api_key}", "Content-Type": "application/json"}

        # Build canonical v2 chat messages: list of {role, content} where content is a string
        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        # include a few recent history messages if present
        for msg in conversation_history[-6:]:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if content:
                messages.append({"role": role, "content": content})
        messages.append({"role": "user", "content": user_message})

        payload = {"stream": False, "model": model, "messages": messages, "max_tokens": max_tokens}

        try:
            r = requests.post(url, headers=headers, json=payload, timeout=30)
        except requests.exceptions.RequestException as e:
            return {"success": False, "error": f"Connection error: {str(e)}"}

        try:
            parsed = r.json()
        except Exception:
            parsed = r.text

        

        if r.status_code != 200:
            return {"success": False, "error": f"Cohere API error {r.status_code}: {parsed}"}

        # Extract assistant text from response.message.content which is list of content blocks
        if isinstance(parsed, dict) and parsed.get("message"):
            msg = parsed.get("message")
            content_blocks = msg.get("content") if isinstance(msg.get("content"), list) else None
            if content_blocks:
                # find first text block
                for blk in content_blocks:
                    if isinstance(blk, dict) and (blk.get("type") == "text" or "text" in blk):
                        text = blk.get("text") or blk.get("content") or blk.get("text")
                        if text:
                            return {"success": True, "text": text}
            # fallback: maybe message has a top-level 'content' string
            if isinstance(msg.get("content"), str):
                return {"success": True, "text": msg.get("content")}

        # As a last resort, try common fields
        if isinstance(parsed, dict) and parsed.get("generations"):
            gens = parsed.get("generations")
            if isinstance(gens, list) and gens:
                gen = gens[0]
                if isinstance(gen, dict) and gen.get("text"):
                    return {"success": True, "text": gen.get("text")}

        return {"success": False, "error": f"Unexpected Cohere response: {parsed}"}

    def send_huggingface(self, prompt: str, model: str = "gpt2", max_tokens: int = 200) -> Dict:
        if not self.hf_api_token:
            return {"success": False, "error": "Missing HUGGINGFACE_API_TOKEN in environment."}

        url = f"https://api-inference.huggingface.co/models/{model}"
        headers = {"Authorization": f"Bearer {self.hf_api_token}"}
        payload = {"inputs": prompt, "parameters": {"max_new_tokens": max_tokens}}
        try:
            r = requests.post(url, headers=headers, json=payload, timeout=30)
            if r.status_code == 200:
                parsed = r.json()
                # HF may return different structures depending on model (list or dict)
                if isinstance(parsed, list) and parsed:
                    text = parsed[0].get("generated_text", "")
                elif isinstance(parsed, dict) and parsed.get("generated_text"):
                    text = parsed.get("generated_text")
                elif isinstance(parsed, dict) and "error" in parsed:
                    return {"success": False, "error": parsed.get("error")}
                else:
                    # try to coerce to string
                    text = str(parsed)

                return {"success": True, "text": text}
            elif r.status_code == 401:
                return {"success": False, "error": "Unauthorized. Check your Hugging Face token."}
            elif r.status_code == 429:
                return {"success": False, "error": "Rate limited by Hugging Face API."}
            else:
                return {"success": False, "error": f"Hugging Face API error: {r.status_code} - {r.text}"}
        except requests.exceptions.RequestException as e:
            return {"success": False, "error": f"Connection error: {str(e)}"}

    def generate_response(
        self,
        provider: str,
        model: str,
        system_instruction: str,
        conversation_history: List[Dict],
        user_message: str,
    ) -> Dict:
        prompt = self.construct_prompt(system_instruction, conversation_history, user_message)

        if provider == "cohere":
            return self.send_cohere(
                system_instruction=system_instruction,
                conversation_history=conversation_history,
                user_message=user_message,
                model=model,
            )
        elif provider == "huggingface":
            return self.send_huggingface(prompt=prompt, model=model)
        else:
            return {"success": False, "error": f"Unknown provider: {provider}"}


def get_default_service() -> AIService:
    return AIService()
