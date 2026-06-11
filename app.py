import streamlit as st
import pandas as pd
import os
from datetime import datetime

# 1. 페이지 기본 설정
st.set_page_config(page_title="요청사항 이력 관리 시스템", layout="wide", page_icon="📋")

st.title("📋 요청사항 이력 관리 시스템")
st.markdown("작성하신 모든 데이터는 안전하게 실시간 저장되며, 언제든 엑셀 파일로 추출할 수 있습니다.")

# 📂 파일 이름 설정 및 불러오기 함수
DB_FILE = "requests_data.csv"

def load_data():
    if os.path.exists(DB_FILE):
        return pd.read_csv(DB_FILE, encoding='utf-8-sig')
    else:
        return pd.DataFrame(columns=["번호", "요청일자", "요청자", "요청내용", "진행상태", "완료예정일", "처리담당자"])

def save_data(df):
    df.to_csv(DB_FILE, index=False, encoding='utf-8-sig')

# 2. 데이터 로드
if 'request_db' not in st.session_state:
    st.session_state.request_db = load_data()

df = st.session_state.request_db

# 상태 옵션 정의 (진행중, 완료, 보류 3가지로 고정)
STATUS_OPTIONS = ["진행중", "완료", "보류"]

# 3. 탭 구성
tab1, tab2 = st.tabs(["➕ 요청사항 등록 및 현황", "🔧 상태 변경 및 수정/삭제"])

# --- [탭 1] 요청사항 등록 및 현황 ---
with tab1:
    st.subheader("📊 접수된 요청사항 이력 목록")
    if df.empty:
        st.info("현재 등록된 요청사항 이력이 없습니다. 새로운 요청을 등록해 주세요.")
    else:
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        # 엑셀 다운로드 데이터 가공 (BOM 도장 쾅)
        excel_data = df.to_csv(index=False).encode('utf-8-sig')
        today_str = datetime.today().strftime("%Y%m%d")
        
        st.download_button(
            label="📥 현재 이력 엑셀(CSV) 파일로 다운로드",
            data=excel_data,
            file_name=f"요청사항_이력_{today_str}.csv",
            mime="text/csv",
            use_container_width=False
        )

    st.markdown("---")
    st.subheader("📝 신규 요청사항 등록")
    
    with st.form("request_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            requester = st.text_input("요청자 (부서 또는 이름)", placeholder="예: 영업팀 홍길동")
            req_content = st.text_area("요청 내용 (상세히)", placeholder="예: 인트라넷 로그인 오류 해결 요청")
        with col2:
            req_date = st.date_input("요청 일자", datetime.today())
            due_date = st.date_input("완료 예정일", datetime.today())
            handler = st.text_input("처리 담당자", placeholder="예: 김현정")
            # 🌟 진행 상태 선택지를 3개로 변경
            status = st.selectbox("진행 상태", STATUS_OPTIONS)

        submit_btn = st.form_submit_button("요청사항 등록하기")

        if submit_btn:
            if requester and req_content:
                new_idx = len(df) + 1
                new_data = pd.DataFrame([{
                    "번호": new_idx,
                    "요청일자": req_date.strftime("%Y-%m-%d"),
                    "요청자": requester,
                    "요청내용": req_content,
                    "진행상태": status,
                    "완료예정일": due_date.strftime("%Y-%m-%d"),
                    "처리담당자": handler
                }])
                
                updated_df = pd.concat([df, new_data], ignore_index=True)
                updated_df["번호"] = range(1, len(updated_df) + 1)
                
                st.session_state.request_db = updated_df
                save_data(updated_df)
                
                st.success(f"✅ [{requester}]님의 요청사항이 파일에 안전하게 저장되었습니다!")
                st.rerun()
            else:
                st.warning("⚠️ 요청자와 요청 내용은 필수 입력 사항입니다.")

# --- [탭 2] 상태 변경 및 수정/삭제 ---
with tab2:
    st.subheader("⚙️ 요청사항 처리 및 이력 수정/삭제")
    if df.empty:
        st.info("관리할 요청사항 이력이 없습니다.")
    else:
        options = [f"[{row['번호']}] {row['요청자']} - {row['요청내용'][:20]}..." for _, row in df.iterrows()]
        selected_option = st.selectbox("처리 및 수정할 요청사항을 선택하세요 👇", options)

        selected_idx = options.index(selected_option)
        selected_row = df.iloc[selected_idx]

        st.markdown("#### ✏️ 선택한 요청사항 내용 수정")
        col1, col2 = st.columns(2)
        with col1:
            edit_requester = st.text_input("요청자 변경", value=selected_row["요청자"])
            edit_content = st.text_area("요청내용 변경", value=selected_row["요청내용"])
            
            # 안전장치: 혹시 기존 데이터에 '접수'가 남아있다면 기본값으로 '진행중'을 선택하게 합니다.
            curr_status = selected_row["진행상태"]
            default_index = STATUS_OPTIONS.index(curr_status) if curr_status in STATUS_OPTIONS else 0
            
            # 🌟 진행상태 변경 선택지도 3개로 변경
            edit_status = st.selectbox("진행상태 변경", STATUS_OPTIONS, index=default_index)
        with col2:
            try:
                curr_req_date = datetime.strptime(selected_row["요청일자"], "%Y-%m-%d")
                curr_due_date = datetime.strptime(selected_row["완료예정일"], "%Y-%m-%d")
            except:
                curr_req_date = datetime.today()
                curr_due_date = datetime.today()
                
            edit_req_date = st.date_input("요청일자 변경", curr_req_date)
            edit_due_date = st.date_input("완료예정일 변경", curr_due_date)
            edit_handler = st.text_input("담당자 변경", value=selected_row["처리담당자"])

        btn_col1, btn_col2, _ = st.columns([1, 1, 3])

        with btn_col1:
            if st.button("💾 저장 완료", type="primary", use_container_width=True):
                df.at[selected_idx, "요청자"] = edit_requester
                df.at[selected_idx, "요청내용"] = edit_content
                df.at[selected_idx, "진행상태"] = edit_status
                df.at[selected_idx, "요청일자"] = edit_req_date.strftime("%Y-%m-%d")
                df.at[selected_idx, "완료예정일"] = edit_due_date.strftime("%Y-%m-%d")
                df.at[selected_idx, "처리담당자"] = edit_handler
                
                st.session_state.request_db = df
                save_data(df)
                
                st.success("요청사항 이력이 업데이트되어 파일에 저장되었습니다!")
                st.rerun()

        with btn_col2:
            if st.button("🗑️ 이력 삭제", type="secondary", use_container_width=True):
                updated_df = df.drop(selected_idx).reset_index(drop=True)
                if not updated_df.empty:
                    updated_df["번호"] = range(1, len(updated_df) + 1)
                
                st.session_state.request_db = updated_df
                save_data(updated_df)
                
                st.error("해당 요청사항 이력이 삭제되었습니다.")
                st.rerun()