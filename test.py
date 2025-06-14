import streamlit as st
import io
import contextlib
import re
import time
from openai import OpenAI

st.set_page_config(layout="wide")

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

def translate_korean_code(code):
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": (
                    "Translate Korean-style Python code into actual Python code "
                    "using English keywords. Respond only with raw code. "
                    "Do not include explanations, prompts, or markdown formatting like ```python."
                ),
            },
            {"role": "user", "content": code},
        ],
        temperature=0.2,
    )
    return response.choices[0].message.content

# 세션 상태 초기화
if "code_input" not in st.session_state:
    st.session_state.code_input = ""
if "input_needed" not in st.session_state:
    st.session_state.input_needed = False
if "input_calls" not in st.session_state:
    st.session_state.input_calls = []
if "input_values" not in st.session_state:
    st.session_state.input_values = []
if "looping" not in st.session_state:
    st.session_state.looping = False

# 컬럼 구성
col1, col2, col3, col4 = st.columns([1, 6, 1, 6])

# col1: 영어 변환
with col1:
    if st.button("영어 변환"):
        if st.session_state.code_input.strip() == "":
            st.warning("한글 파이썬 코드를 먼저 입력해주세요.")
        else:
            translated = translate_korean_code(st.session_state.code_input)
            st.session_state.code_input = translated
            st.session_state.input_calls = []
            st.session_state.input_values = []

# col2: 코드 입력
with col2:
    st.session_state.code_input = st.text_area(
        "파이썬 코드 입력 (한글 또는 영어)",
        value=st.session_state.code_input,
        height=400
    )

# input() 감지
code = st.session_state.code_input
input_calls = list(re.finditer(r'input\s*\(\s*["\']?.*?["\']?\s*\)', code))
st.session_state.input_calls = input_calls

# col3: 실행 버튼
with col3:
    if st.button("코드 실행"):
        if not input_calls:
            if "while True" in code:
                st.session_state.result = "__INFINITE_LOOP__"
            else:
                output = io.StringIO()
                try:
                    with contextlib.redirect_stdout(output), contextlib.redirect_stderr(output):
                        exec(code, {})
                    st.session_state.result = output.getvalue()
                    st.session_state.input_needed = False
                except Exception as e:
                    st.session_state.result = f"오류 발생: {e}"
        else:
            st.session_state.input_needed = True

# col4: 실행 결과 / 입력
with col4:
    if st.session_state.input_needed and st.session_state.input_calls:
        st.write("👇 실행을 위해 입력값을 넣어주세요:")
        st.session_state.input_values = []
        for i, match in enumerate(st.session_state.input_calls):
            value = st.text_input(f"입력값 #{i+1}", key=f"input_{i}")
            st.session_state.input_values.append(value)

        if st.button("입력값 적용 후 실행"):
            exec_code = code
            for i, match in enumerate(st.session_state.input_calls):
                exec_code = exec_code.replace(match.group(0), f'"{st.session_state.input_values[i]}"', 1)

            # 무한 루프 감지
            if "while True" in exec_code:
                # print된 문자열 추출 (맨 마지막 print 문장)
                prints = list(re.finditer(r'print\s*\(\s*["\'](.*?)["\']\s*\)', exec_code))
                print_str = prints[-1].group(1) if prints else "(출력 없음)"
                st.session_state.looping = True
                st.session_state.loop_output = print_str
                st.rerun()
            else:
                output = io.StringIO()
                try:
                    with contextlib.redirect_stdout(output), contextlib.redirect_stderr(output):
                        exec(exec_code, {})
                    st.success("✅ 실행 결과")
                    st.code(output.getvalue() or "(출력 없음)", language="text", height=400)
                    st.session_state.input_needed = False
                except Exception as e:
                    st.error(f"오류 발생: {e}")

    elif st.session_state.result == "__INFINITE_LOOP__":
        st.warning("⚠️ 무한 루프가 감지되어 Streamlit 방식으로 실행됩니다.")
        st.session_state.looping = True
        st.session_state.loop_output = "출력 없음"
        st.rerun()

    elif "result" in st.session_state and not st.session_state.input_needed:
        st.success("✅ 실행 결과")
        st.code(st.session_state.result or "(출력 없음)", language="text", height=400)

# ✅ 무한 루프 Streamlit 방식 출력
if st.session_state.get("looping", False):
    stop = st.button("멈추기")
    output_area = st.empty()
    i = st.session_state.get("loop_index", 1)

    if stop:
        st.session_state.looping = False
        st.session_state.loop_index = 1
        st.success("✅ 루프가 중지되었습니다.")
    else:
        output_area.code(f"{st.session_state.loop_output} ({i})", language="text")
        time.sleep(1 / 3)
        st.session_state.loop_index = i + 1
        st.rerun()
