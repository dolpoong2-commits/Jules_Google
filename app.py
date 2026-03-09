import streamlit as st
import os
import db
import time
from rag import RAGManager
from llm import LLMClient
from dotenv import load_dotenv

# Initialize session state for UI if not present
if "rag_manager" not in st.session_state:
    st.session_state.rag_manager = RAGManager()
if "current_session_id" not in st.session_state:
    st.session_state.current_session_id = None
if "messages" not in st.session_state:
    st.session_state.messages = []

# Load environment variables (if any)
load_dotenv()

st.set_page_config(page_title="Local LLM RAG & Fine-Tune Hub", layout="wide", page_icon="🧠")

def format_bytes(mb: float) -> str:
    if mb > 1024:
        return f"{mb/1024:.2f} GB"
    return f"{mb:.0f} MB"

def show_dashboard():
    st.title("🎛️ 대시보드 및 설정 (Dashboard & Settings)")
    st.markdown("여기서 로컬 LLM 서버 연결과 시스템 상태를 확인하고 설정할 수 있습니다.")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("LLM 서버 설정")
        # Tooltips using help parameter
        base_url = st.text_input(
            "Local LLM Base URL",
            value=st.session_state.get("llm_base_url", "http://localhost:8000/v1"),
            help="vLLM, Ollama 등 로컬 LLM 서버의 주소를 입력하세요. (예: http://localhost:8000/v1)"
        )
        st.session_state.llm_base_url = base_url

        model_name = st.text_input(
            "Model Name",
            value=st.session_state.get("llm_model_name", "Exaone-4.0-32b"),
            help="로컬 서버에서 구동 중인 모델의 이름을 정확히 입력하세요."
        )
        st.session_state.llm_model_name = model_name

        api_key = st.text_input(
            "API Key",
            value=st.session_state.get("llm_api_key", "EMPTY"), type="password",
            help="대부분의 로컬 서버는 API Key를 요구하지 않지만, 필요한 경우 입력하세요."
        )
        st.session_state.llm_api_key = api_key

    with col2:
        st.subheader("시스템 및 VRAM 상태")
        client = LLMClient(base_url=base_url, api_key=api_key, model=model_name)
        vram_info = client.get_vram_usage()

        if vram_info["status"] == "ok":
            for gpu in vram_info["gpus"]:
                st.write(f"**GPU {gpu['id']}: {gpu['name']}**")

                # Progress bar color logic: warning if > 90%
                percent = gpu["percent_used"]

                if percent > 90:
                    st.error(f"🚨 VRAM 사용량 초과 위험! ({percent:.1f}%)")
                elif percent > 75:
                    st.warning(f"⚠️ VRAM 사용량 높음 ({percent:.1f}%)")
                else:
                    st.success(f"✅ VRAM 여유 있음 ({percent:.1f}%)")

                st.progress(min(percent / 100.0, 1.0))
                st.caption(f"Used: {format_bytes(gpu['used_mb'])} / Total: {format_bytes(gpu['total_mb'])}")

        elif vram_info["status"] == "unavailable":
            st.info("NVIDIA GPU가 감지되지 않았거나 `nvidia-ml-py`가 설치되지 않았습니다. CPU 또는 다른 디바이스를 사용 중일 수 있습니다.")
        else:
            st.error(f"VRAM 상태를 가져오는 중 오류 발생: {vram_info.get('error', 'Unknown Error')}")

        st.subheader("RAG 벡터 DB 통계")
        stats = st.session_state.rag_manager.get_document_stats()
        st.metric("저장된 문서 청크(조각) 수", stats.get("document_chunks", 0))
        st.metric("저장된 대화 기록 수", stats.get("history_chunks", 0))

def show_chat():
    st.title("💬 로컬 LLM 대화 (Chat with RAG)")

    # Sidebar for session management
    with st.sidebar:
        st.header("대화 세션")
        if st.button("➕ 새 대화 시작 (New Chat)"):
            st.session_state.current_session_id = None
            st.session_state.messages = []
            st.rerun()

        sessions = db.get_sessions()
        for s in sessions:
            if st.button(f"🗨️ {s['title']} ({s['created_at'][:10]})", key=s['session_id']):
                st.session_state.current_session_id = s['session_id']
                # Load messages from DB
                db_msgs = db.get_messages(s['session_id'])
                st.session_state.messages = [{"role": m["role"], "content": m["content"]} for m in db_msgs]
                st.rerun()

        st.markdown("---")
        st.subheader("RAG 옵션")
        use_rag_docs = st.checkbox("문서 검색 사용 (Data Sheets)", value=True, help="업로드한 문서(PDF/TXT/CSV)에서 답변의 근거를 찾습니다.")
        use_rag_history = st.checkbox("과거 대화 검색 사용 (History)", value=True, help="이전 대화 기록을 검색해 답변에 참고합니다.")

    # Check if we need to create a new session
    if st.session_state.current_session_id is None:
        # Create a new session in DB on first message
        pass

    # Display chat messages from history on app rerun
    for message in st.session_state.messages:
        with st.chat_message("user" if message["role"] == "user" else "assistant"):
            st.markdown(message["content"])

    # React to user input
    if prompt := st.chat_input("메시지를 입력하세요..."):
        # Display user message in chat message container
        st.chat_message("user").markdown(prompt)
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})

        # Initialize session if first message
        if st.session_state.current_session_id is None:
            model_name = st.session_state.get("llm_model_name", "Unknown")
            # Generate a title from the prompt
            title = prompt[:20] + "..." if len(prompt) > 20 else prompt
            st.session_state.current_session_id = db.create_session(model_name=model_name, title=title)

        # Save user message to DB
        db.save_message(st.session_state.current_session_id, "user", prompt)

        # Retrieve RAG context if enabled
        rag_context = ""
        if use_rag_docs or use_rag_history:
            with st.spinner("유사한 문서 및 대화 검색 중..."):
                rag_context = st.session_state.rag_manager.retrieve_context(
                    query=prompt,
                    use_docs=use_rag_docs,
                    use_history=use_rag_history
                )
                if rag_context:
                    st.toast("참고할 RAG 컨텍스트를 찾았습니다!")

        # Get response from local LLM
        with st.chat_message("assistant"):
            message_placeholder = st.empty()

            # Check VRAM before generation
            client = LLMClient(
                base_url=st.session_state.get("llm_base_url", "http://localhost:8000/v1"),
                api_key=st.session_state.get("llm_api_key", "EMPTY"),
                model=st.session_state.get("llm_model_name", "Exaone-4.0-32b")
            )
            vram_info = client.get_vram_usage()
            if vram_info.get("warning"):
                st.warning("⚠️ VRAM 사용량이 90%를 초과했습니다. 응답이 느리거나 OOM 에러가 발생할 수 있습니다.")

            with st.spinner("답변 생성 중..."):
                # We only send the last few messages for generation context to save context window
                history_for_llm = st.session_state.messages[:-1]

                response = client.generate_response(
                    prompt=prompt,
                    history=history_for_llm[-5:], # send last 5 messages
                    rag_context=rag_context
                )

                message_placeholder.markdown(response)

        # Add assistant response to chat history
        st.session_state.messages.append({"role": "assistant", "content": response})
        # Save to DB
        db.save_message(st.session_state.current_session_id, "assistant", response)

        # Ingest assistant message to RAG history
        st.session_state.rag_manager.ingest_chat_message(
            session_id=st.session_state.current_session_id,
            role="user",
            content=prompt
        )
        st.session_state.rag_manager.ingest_chat_message(
            session_id=st.session_state.current_session_id,
            role="assistant",
            content=response
        )

def show_document_management():
    st.title("📂 문서 및 데이터 시트 관리 (Documents)")
    st.markdown("RAG 파이프라인에서 참조할 외부 문서(PDF, TXT, CSV)를 업로드하고 벡터 DB에 저장합니다.")

    uploaded_files = st.file_uploader(
        "Upload Data Sheets (데이터 시트 업로드)",
        type=["pdf", "txt", "csv"],
        accept_multiple_files=True,
        help="여기에 PDF, TXT, CSV 파일을 끌어다 놓으세요."
    )

    tags = st.text_input("Tags (태그)", help="문서를 분류할 태그를 입력하세요. (예: 매뉴얼, 정책, 코드리뷰)")

    if st.button("문서 저장 및 분석 (Ingest to Vector DB)"):
        if not uploaded_files:
            st.error("업로드된 파일이 없습니다.")
        else:
            total_chunks = 0
            # Ensure upload dir exists
            os.makedirs("uploads", exist_ok=True)

            progress_bar = st.progress(0)
            for i, file in enumerate(uploaded_files):
                file_path = os.path.join("uploads", file.name)
                # Save file locally first
                with open(file_path, "wb") as f:
                    f.write(file.getbuffer())

                with st.spinner(f"'{file.name}' 분석 및 벡터 변환 중..."):
                    try:
                        chunks = st.session_state.rag_manager.ingest_document(file_path, tags)
                        total_chunks += chunks
                        st.success(f"'{file.name}' 저장 완료 (청크: {chunks}개)")
                    except Exception as e:
                        st.error(f"'{file.name}' 처리 중 오류: {e}")

                progress_bar.progress((i + 1) / len(uploaded_files))

            st.balloons()
            st.success(f"총 {total_chunks}개의 텍스트 조각이 벡터 데이터베이스에 성공적으로 저장되었습니다!")

def show_data_export():
    st.title("⬇️ 데이터 추출 및 학습 (Data Export)")
    st.markdown("저장된 대화 기록을 로컬 LLM 파인튜닝(Fine-tuning)을 위한 형식(JSONL)으로 추출합니다.")

    stats = db.get_stats()
    st.info(f"현재 총 **{stats['session_count']}**개의 대화 세션과 **{stats['message_count']}**개의 메시지가 저장되어 있습니다.")

    export_path = "dataset_export.jsonl"

    if st.button("파인튜닝 데이터셋 (JSONL) 생성"):
        with st.spinner("JSONL 파일 생성 중..."):
            db.export_to_jsonl(export_path)
            time.sleep(1) # Fake delay for UX
            st.session_state.export_ready = True

    if st.session_state.get("export_ready", False) and os.path.exists(export_path):
        st.success("데이터셋이 성공적으로 생성되었습니다. 아래 버튼을 눌러 다운로드하세요.")
        with open(export_path, "r", encoding="utf-8") as f:
            st.download_button(
                label="📥 데이터셋 다운로드 (dataset_export.jsonl)",
                data=f,
                file_name="dataset_export.jsonl",
                mime="application/jsonl"
            )

        st.subheader("미리보기 (Preview)")
        try:
            with open(export_path, "r", encoding="utf-8") as f:
                head = [next(f) for _ in range(3)]
            st.code("".join(head), language="json")
        except StopIteration:
            st.info("데이터가 부족하여 미리보기를 표시할 수 없습니다.")

# Main app logic for Sidebar navigation
st.sidebar.title("로컬 LLM RAG & 학습 허브")
page = st.sidebar.radio(
    "메뉴 선택 (Navigation)",
    ["대시보드 및 설정 (Dashboard)", "대화하기 (Chat)", "문서 관리 (Documents)", "데이터 추출 (Export)"]
)

if page == "대시보드 및 설정 (Dashboard)":
    show_dashboard()
elif page == "대화하기 (Chat)":
    show_chat()
elif page == "문서 관리 (Documents)":
    show_document_management()
elif page == "데이터 추출 (Export)":
    show_data_export()
