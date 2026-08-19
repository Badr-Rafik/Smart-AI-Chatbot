import streamlit as st
from ai_service import AIService

st.set_page_config(page_title="Smart AI Chatbot", layout="wide")

st.title("Smart AI Chatbot")

# Sidebar: provider and model selection
with st.sidebar:
    st.header("Configuration")
    provider = st.selectbox("AI Provider", ["cohere", "huggingface"], index=0)
    default_model = "command-xlarge-nightly" if provider == "cohere" else "gpt2"
    model = st.text_input("Model name", value=default_model)
    system_instruction = st.text_area("System instruction", value="You are a helpful assistant.")
    st.markdown("---")
    st.markdown("Load your API keys into environment variables or a `.env` file. See README for details.")

# Initialize session state for messages
if "messages" not in st.session_state:
    st.session_state.messages = []

def append_message(role: str, content: str):
    st.session_state.messages.append({"role": role, "content": content})

def clear_conversation():
    st.session_state.messages = []


def _safe_rerun():
    try:
        st.experimental_rerun()
    except Exception:
        # Some streamlit builds may not expose experimental_rerun; ignore silently
        pass

ai = AIService()

col1, col2 = st.columns([3, 1])

with col1:
    # Display conversation
    st.subheader("Conversation")
    if not st.session_state.messages:
        st.info("No messages yet — send a message to start the conversation.")

    for msg in st.session_state.messages:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        if role == "user":
            st.markdown(f"**User:** {content}")
        elif role == "assistant":
            st.markdown(f"**Assistant:** {content}")
        else:
            st.markdown(f"**{role.title()}:** {content}")

    st.markdown("---")
    user_input = st.text_area("Your message", height=120)
    send = st.button("Send")

with col2:
    st.subheader("Actions")
    if st.button("Clear Conversation"):
        clear_conversation()
        _safe_rerun()

    st.markdown("**Status**")
    keys = ai.get_loaded_keys()
    st.write(keys)

if send:
    if not user_input or not user_input.strip():
        st.error("Please enter a message before sending.")
    else:
        append_message("user", user_input.strip())
        with st.spinner("Contacting AI..."):
            result = ai.generate_response(
                provider=provider,
                model=model,
                system_instruction=system_instruction,
                conversation_history=st.session_state.messages,
                user_message=user_input.strip(),
            )

        if result.get("success"):
            assistant_text = result.get("text", "")
            append_message("assistant", assistant_text)
            _safe_rerun()
        else:
            st.error(f"Error: {result.get('error')}")
