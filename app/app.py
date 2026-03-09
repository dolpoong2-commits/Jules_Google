import streamlit as st
import db
import api
import json

# Initialize database
db.init_db()

# Page configuration
st.set_page_config(
    page_title="LLM Chat Dashboard",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS to mimic LM Studio/Ollama UI slightly
st.markdown("""
    <style>
        .stChatMessage { padding: 1rem; border-radius: 0.5rem; margin-bottom: 1rem; }
        .stChatMessage[data-testid="stChatMessageUser"] { background-color: #f0f2f6; }
        .stChatMessage[data-testid="stChatMessageAssistant"] { background-color: #e1f5fe; }
    </style>
""", unsafe_allow_html=True)

# Application State Management
if "current_session_id" not in st.session_state:
    st.session_state.current_session_id = None
if "messages" not in st.session_state:
    st.session_state.messages = []

# ==========================================
# Sidebar Settings and Chat History
# ==========================================
with st.sidebar:
    st.title("⚙️ Settings")

    # 1. Endpoints & Mode Configuration
    st.subheader("Connection")
    mode = st.radio("Chat Mode", ["vLLM (OpenAI API)", "OpenClaw Agent"])

    if mode == "vLLM (OpenAI API)":
        vllm_url = st.text_input("vLLM Endpoint URL", value="http://host.docker.internal:8000/v1")
        vllm_model = st.text_input("Model Name", value="gpt-oss-20b")
    else:
        openclaw_url = st.text_input("OpenClaw API URL", value="http://host.docker.internal:8080/api/chat")

    # 2. Model Parameters
    st.subheader("Model Parameters")
    system_prompt = st.text_area("System Prompt", value="You are a helpful and harmless AI assistant.")
    temperature = st.slider("Temperature", min_value=0.0, max_value=2.0, value=0.7, step=0.1)
    max_tokens = st.slider("Max Tokens", min_value=100, max_value=8192, value=2048, step=100)

    st.divider()

    # 3. Chat Session Management
    st.subheader("💬 Chat History")

    if st.button("➕ New Chat", use_container_width=True):
        st.session_state.current_session_id = None
        st.session_state.messages = []
        st.rerun()

    sessions = db.get_sessions()

    if sessions:
        st.markdown("### Past Chats")
        for session in sessions:
            session_id, title, created_at = session
            col1, col2 = st.columns([4, 1])
            with col1:
                # Load chat history
                if st.button(f"📄 {title[:15]}...", key=f"load_{session_id}"):
                    st.session_state.current_session_id = session_id
                    raw_msgs = db.get_messages(session_id)
                    st.session_state.messages = [{"role": role, "content": content} for role, content, _ in raw_msgs]
                    st.rerun()
            with col2:
                # Delete chat
                if st.button("🗑️", key=f"del_{session_id}"):
                    db.delete_session(session_id)
                    if st.session_state.current_session_id == session_id:
                        st.session_state.current_session_id = None
                        st.session_state.messages = []
                    st.rerun()

# ==========================================
# Main Chat Interface
# ==========================================
st.title(f"🤖 Chat Dashboard ({mode})")

# Inject system prompt into the context but don't display it as a message
context_messages = [{"role": "system", "content": system_prompt}] + st.session_state.messages

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Accept user input
if prompt := st.chat_input("Type your message here..."):
    # Initialize a new session if this is the first message
    if st.session_state.current_session_id is None:
        title = prompt[:30] + "..." if len(prompt) > 30 else prompt
        st.session_state.current_session_id = db.create_session(
            title=title,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens
        )

    # Save user message to database
    db.save_message(st.session_state.current_session_id, "user", prompt)

    # Add user message to session state and display it
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Prepare messages payload
    payload_messages = [{"role": "system", "content": system_prompt}] + st.session_state.messages

    # Display assistant response and handle API call
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""

        try:
            if mode == "vLLM (OpenAI API)":
                response = api.get_vllm_response(
                    endpoint=vllm_url,
                    model=vllm_model,
                    messages=payload_messages,
                    temperature=temperature,
                    max_tokens=max_tokens
                )

                # Check if it's an error string
                if isinstance(response, str) and response.startswith("Error"):
                    full_response = response
                    message_placeholder.markdown(full_response)
                else:
                    # Stream the response
                    for chunk in response:
                        if chunk.choices[0].delta.content is not None:
                            full_response += chunk.choices[0].delta.content
                            message_placeholder.markdown(full_response + "▌")
                    message_placeholder.markdown(full_response)

            else: # OpenClaw Mode
                with st.spinner("OpenClaw Agent is thinking..."):
                    # For OpenClaw, if it returns a stream generator, handle it
                    response = api.get_openclaw_response(
                        endpoint=openclaw_url,
                        messages=payload_messages,
                        temperature=temperature,
                        max_tokens=max_tokens
                    )

                    if hasattr(response, '__iter__') and not isinstance(response, (str, dict, list)):
                        # Streaming response generator
                        for line in response:
                            if line:
                                try:
                                    # Assuming standard Server-Sent Events (SSE) formatting like OpenAI
                                    if line.startswith("data: "):
                                        data = json.loads(line[6:])
                                        if "choices" in data and data["choices"][0].get("delta", {}).get("content"):
                                            full_response += data["choices"][0]["delta"]["content"]
                                            message_placeholder.markdown(full_response + "▌")
                                except Exception as e:
                                    pass
                        message_placeholder.markdown(full_response)
                    else:
                        # Non-streaming text response
                        full_response = response
                        message_placeholder.markdown(full_response)

            # Save assistant response to DB and state
            db.save_message(st.session_state.current_session_id, "assistant", full_response)
            st.session_state.messages.append({"role": "assistant", "content": full_response})

        except Exception as e:
            st.error(f"An error occurred: {str(e)}")
