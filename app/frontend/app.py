import streamlit as st
import requests
import os

API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000/api/memory")

st.set_page_config(page_title="AI Memory Dashboard", layout="wide")

st.title("🧠 AI 대화 기억 시스템 (AI Memory System)")

tab1, tab2 = st.tabs(["💬 새 대화 저장", "🔍 의미 기반 검색"])

with tab1:
    st.header("새로운 대화 또는 정보 저장")

    with st.form("save_memory_form"):
        title = st.text_input("제목 (선택, 비워두면 자동 생성)")
        project = st.text_input("프로젝트 이름 (선택)")
        ai_name = st.selectbox("AI 모델", ["ChatGPT", "Claude", "Local LLM", "System"])
        raw_text = st.text_area("대화 원본 또는 저장할 내용 (필수)", height=300)

        submitted = st.form_submit_button("저장하기")

        if submitted:
            if not raw_text.strip():
                st.error("저장할 내용을 입력해주세요.")
            else:
                with st.spinner("AI가 요약, 태깅 및 임베딩을 생성 중입니다..."):
                    payload = {
                        "title": title if title else "자동 생성됨",
                        "raw_text": raw_text,
                        "ai_name": ai_name,
                        "project": project if project else None
                    }
                    try:
                        response = requests.post(f"{API_BASE_URL}/", json=payload)
                        if response.status_code == 200:
                            data = response.json()
                            st.success(f"저장 성공! (ID: {data['id']})")
                            with st.expander("생성된 메타데이터 보기"):
                                st.json(data)
                        else:
                            st.error(f"오류 발생: {response.text}")
                    except Exception as e:
                        st.error(f"서버에 연결할 수 없습니다: {e}")

with tab2:
    st.header("하이브리드 검색 (키워드 + 의미 검색)")

    query = st.text_input("검색어를 입력하세요 (예: '그때 ESP32 스마트저울 보정 코드')")
    col1, col2 = st.columns(2)
    with col1:
        limit = st.number_input("검색 결과 수", min_value=1, max_value=20, value=5)
    with col2:
        min_score = st.slider("최소 유사도 점수", min_value=0.0, max_value=1.0, value=0.5, step=0.05)

    if st.button("검색"):
        if not query.strip():
            st.warning("검색어를 입력해주세요.")
        else:
            with st.spinner("의미 기반으로 검색 중입니다..."):
                try:
                    params = {"query": query, "limit": limit, "min_score": min_score}
                    response = requests.get(f"{API_BASE_URL}/search", params=params)

                    if response.status_code == 200:
                        results = response.json()
                        st.subheader(f"총 {len(results)}개의 결과를 찾았습니다.")

                        for idx, res in enumerate(results):
                            with st.container():
                                st.markdown(f"### {idx+1}. {res['title']}")

                                meta_col1, meta_col2, meta_col3, meta_col4 = st.columns(4)
                                meta_col1.markdown(f"**Score**: `{res['score']:.4f}`")
                                meta_col2.markdown(f"**Project**: `{res.get('project') or 'N/A'}`")
                                meta_col3.markdown(f"**Importance**: `{res.get('importance') or 'N/A'}`")
                                meta_col4.markdown(f"**Date**: `{res['created_at'][:10]}`")

                                st.markdown(f"**태그**: " + " ".join([f"`#{tag}`" for tag in res['tags']]))
                                st.markdown(f"**요약**: {res['summary']}")

                                with st.expander("상세 수정 / 관리"):
                                    st.write("나중에 이 부분에 태그 수정 및 중요도 변경 UI 추가 가능")
                                st.divider()
                    else:
                        st.error(f"검색 오류: {response.text}")
                except Exception as e:
                    st.error(f"서버에 연결할 수 없습니다: {e}")
