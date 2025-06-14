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
for key, default in {
    "code_input": "",
    "input_needed": False,
    "input_calls": [],
    "input_values": [],
    "looping": False,
    "loop_output": "",
    "loop_index": 1,
    "rerun_flag": False,
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

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

code = st.session_state.code_input
input_calls = list(re.finditer(r'input\s*\(\s*["\']?.*?["\']?\s*\)', code))
st.session_state.input_calls = input_calls

# col3: 실행 버튼
with col3:
    if st.button("코드 실행"):
        if not input_calls:
            if "while True" in code:
                # 무한 루프 감지 시 세션에 신호만 저장 (즉시 rerun하지 않음)
                st.session_state.result = "__INFINITE_LOOP__"
                st.session_state.looping = True
                # 무한 루프에서 출력할 문자열 찾기 (print 구문 중 마지막 인자)
                prints = list(re.finditer(r'print\s*\(\s*["\'](.*?)["\']\s*\)', code))
                st.session_state.loop_output = prints[-1].group(1) if prints else "(출력 없음)"
                st.session_state.loop_index = 1
                st.session_state.input_needed = False
                st.session_state.rerun_flag = True
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

            if "while True" in exec_code:
                prints = list(re.finditer(r'print\s*\(\s*["\'](.*?)["\']\s*\)', exec_code))
                st.session_state.looping = True
                st.session_state.loop_output = prints[-1].group(1) if prints else "(출력 없음)"
                st.session_state.loop_index = 1
                st.session_state.input_needed = False
                st.session_state.rerun_flag = True
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

    elif st.session_state.get("result", "") == "__INFINITE_LOOP__" and not st.session_state.looping:
        st.warning("⚠️ 무한 루프가 감지되어 Streamlit 방식으로 실행됩니다.")
        st.session_state.looping = True
        st.session_state.loop_output = "출력 없음"
        st.session_state.loop_index = 1
        st.session_state.rerun_flag = True

    elif st.session_state.get("result") and not st.session_state.input_needed and not st.session_state.looping:
        st.success("✅ 실행 결과")
        st.code(st.session_state.result or "(출력 없음)", language="text", height=400)

# 무한 루프 출력 & 반복 처리
if st.session_state.looping:
    stop = st.button("멈추기")
    output_area = st.empty()
    i = st.session_state.loop_index

    if stop:
        st.session_state.looping = False
        st.session_state.loop_index = 1
        st.session_state.rerun_flag = False
        st.success("✅ 루프가 중지되었습니다.")
    else:
        output_area.code(f"{st.session_state.loop_output} ({i})", language="text")
        time.sleep(1 / 3)
        st.session_state.loop_index = i + 1
        st.session_state.rerun_flag = True

# 안전하게 rerun 호출: 버튼 클릭 같은 사용자 액션 이후에만
if st.session_state.rerun_flag:
    st.session_state.rerun_flag = False
    st.experimental_rerun()
