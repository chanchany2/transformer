with col4:
    # 무한 루프 실행 처리
    if st.session_state.get("force_loop", False):
        st.write("⏳ 무한 루프 감지됨 → 5회까지만 출력합니다.")
        output_area = st.empty()
        for i in range(5):
            output_area.code(f"이서인 바보 ({i+1})", language="text")
            time.sleep(1)
        st.session_state.force_loop = False
    elif st.session_state.input_needed and st.session_state.input_calls:
        st.write("👇 실행을 위해 입력값을 넣어주세요:")
        st.session_state.input_values = []
        for i, match in enumerate(st.session_state.input_calls):
            value = st.text_input(f"입력값 #{i+1}", key=f"input_{i}")
            st.session_state.input_values.append(value)
        if st.button("입력값 적용 후 실행"):
            exec_code = code
            for i, match in enumerate(st.session_state.input_calls):
                exec_code = exec_code.replace(match.group(0), f'"{st.session_state.input_values[i]}"', 1)

            output = io.StringIO()
            try:
                with contextlib.redirect_stdout(output), contextlib.redirect_stderr(output):
                    exec(exec_code, {})
                st.success("✅ 실행 결과")
                st.code(output.getvalue() or "(출력 없음)", language="text", height=400)
                st.session_state.input_needed = False
            except Exception as e:
                st.error(f"오류 발생: {e}")
    elif "result" in st.session_state and not st.session_state.input_needed:
        st.success("✅ 실행 결과")
        st.code(st.session_state.result or "(출력 없음)", language="text", height=400)
