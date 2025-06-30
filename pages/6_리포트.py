import streamlit as st
import sys
import os
import pdfplumber
from openai import OpenAI
from datetime import datetime
from dotenv import load_dotenv

# 상위 디렉토리의 utils 모듈 import를 위한 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 페이지 설정
st.set_page_config(
    page_title="AI_리포트 생성기",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 커스텀 CSS
st.markdown("""
<style>
    .info-container {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 25px;
        border-radius: 15px;
        color: white;
        margin: 20px 0;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    .data-source-card {
        background: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        margin: 15px 0;
        border-left: 5px solid #1f77b4;
    }
    .update-card {
        background: linear-gradient(135deg, #74b9ff 0%, #0984e3 100%);
        padding: 15px;
        border-radius: 10px;
        color: white;
        margin: 10px 0;
    }
    .system-info {
        background: linear-gradient(135deg, #00b894 0%, #00a085 100%);
        padding: 20px;
        border-radius: 15px;
        color: white;
        margin: 15px 0;
    }
    .guide-section {
        background: #f8f9fa;
        padding: 20px;
        border-radius: 10px;
        margin: 15px 0;
        border: 1px solid #e9ecef;
    }
</style>
""", unsafe_allow_html=True)

# 타이틀
st.markdown('<h1 class="main-header">📄 AI 기반 보고서 생성기</h1>', unsafe_allow_html=True)

# OpenAI API Key 로딩
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")



# PDF 텍스트 추출
@st.cache_data
def extract_text_from_pdf(uploaded_file):
    with pdfplumber.open(uploaded_file) as pdf:
        text = ""
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text

# 목차 추출 함수
def extract_table_of_contents(text):
    prompt = f"""
다음 문서에서 **목차(차례)**에 해당하는 부분만 정확히 추출해 주세요.
- 숫자나 로마자, 제목 패턴을 이용해 목차 항목만 뽑아주세요.
- 본문 내용은 포함하지 말고, 목차 구조만 출력하세요.

문서 내용:
{text[:4000]}
"""
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "당신은 문서 구조에서 목차만 정확히 추출하는 AI입니다."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3
    )
    return response.choices[0].message.content.strip()

# 문서 전체 구조 요약
def summarize_template_structure(text):
    prompt = f"""
다음 문서의 형식(보고서 구조, 제목 스타일, 구성 흐름 등)을 간단히 요약해 주세요.
- 문서가 어떤 형식으로 작성되어 있는지 설명해주세요.
- 목차, 본문 구성, 언어 톤 등을 포함해 형식을 분석해주세요.

문서 내용:
{text[:4000]}
"""
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "당신은 문서 형식을 분석하고 요약하는 AI입니다."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.5
    )
    return response.choices[0].message.content.strip()

# 주제 기반 보고서 생성
def generate_report_based_on_template(topic, template_text):
    prompt = f"""
아래 문서 형식을 참고하여, 새로운 주제 '{topic}'에 대해 동일한 형식의 보고서를 작성해 주세요.

- 문서 형식(목차, 구성, 말투 등)은 그대로 유지하되,
- 내용은 '{topic}'을 기반으로 완전히 새롭게 작성해 주세요.

📄 참고 문서:
{template_text[:4000]}
"""
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "당신은 보고서 형식을 학습해 새로운 주제에 맞춰 작성하는 AI입니다."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7
    )
    return response.choices[0].message.content.strip()

# 사용자 입력 UI
uploaded_file = st.file_uploader("📎 PDF 문서를 업로드하세요", type=["pdf"])

# Step 1: 문서 업로드 시 내용 요약 및 목차 추출
if uploaded_file:
    with st.spinner("문서 분석 중..."):
        extracted_text = extract_text_from_pdf(uploaded_file)

        toc = extract_table_of_contents(extracted_text)
        structure_summary = summarize_template_structure(extracted_text)

    st.subheader("🧾 문서 목차 자동 추출")
    st.code(toc, language="markdown")

    st.subheader("📚 문서 형식 요약")
    st.markdown(structure_summary)

topic = st.text_input("📝 새로 작성할 보고서 주제를 입력하세요", placeholder="예: 탄소중립 추진 전략")

# Step 2: 주제 입력 후 보고서 생성
if uploaded_file and topic:
    with st.spinner("📄 새로운 보고서를 작성하는 중입니다..."):
        generated_report = generate_report_based_on_template(topic, extracted_text)
    st.success("✅ 보고서 생성 완료!")

    st.download_button(
        "📥 보고서 다운로드",
        generated_report,
        file_name=f"{topic}_보고서.txt",
        mime="text/plain"
    )

    st.text_area("📄 생성된 보고서 미리보기", generated_report, height=500)