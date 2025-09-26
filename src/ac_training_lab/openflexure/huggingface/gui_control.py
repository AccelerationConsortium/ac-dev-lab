def show():
    # note to self you can check for empty with if statement st.image(image,
    # caption='PIL Image', use_column_width=True)
    import streamlit as st
    from microscope_demo_client import MicroscopeDemo
    from my_secrets import HIVEMQ_BROKER

    port = 8883
    microscopes = [
        "microscope",
        "microscope2",
        "deltastagetransmission",
        "deltastagereflection",
    ]

    def get_pos_button():
        microscope = MicroscopeDemo(
            HIVEMQ_BROKER,
            port,
            microscopeselection + "clientuser",
            access_key,
            microscopeselection,
        )
        # "acmicroscopedemo" is a placeholder until access keys are implemented
        pos = microscope.get_pos()
        st.write("x: " + str(pos["x"]))
        st.write("y: " + str(pos["y"]))
        st.write("z: " + str(pos["z"]))
        microscope.end_connection()

    def take_image_button():
        microscope = MicroscopeDemo(
            HIVEMQ_BROKER,
            port,
            microscopeselection + "clientuser",
            access_key,
            microscopeselection,
        )
        # "acmicroscopedemo" is a placeholder until access keys are implemented
        st.image(
            microscope.take_image(),
            caption="Taken from the microscope camera",
            use_column_width=True,
        )
        microscope.end_connection()

    def focus_button():
        microscope = MicroscopeDemo(
            HIVEMQ_BROKER,
            port,
            microscopeselection + "clientuser",
            access_key,
            microscopeselection,
        )
        # "acmicroscopedemo" is a placeholder until access keys are implemented
        microscope.focus(focusamount)
        st.write("Autofocus complete")
        microscope.end_connection()

    def move_button():
        microscope = MicroscopeDemo(
            HIVEMQ_BROKER,
            port,
            microscopeselection + "clientuser",
            access_key,
            microscopeselection,
        )
        # "acmicroscopedemo" is a placeholder until access keys are implemented
        microscope.move(xmove, ymove)
        st.write("Move complete")
        microscope.end_connection()

    def start_recording_button():
        microscope = MicroscopeDemo(
            HIVEMQ_BROKER,
            port,
            microscopeselection + "clientuser",
            access_key,
            microscopeselection,
        )
        # Store microscope instance in session state for stopping later
        st.session_state.recording_microscope = microscope
        microscope.start_video_recording(fps=recording_fps)
        st.success(f"Video recording started at {recording_fps} fps")
        st.info("Use 'Stop Recording' button to end recording and save video")

    def stop_recording_button():
        if hasattr(st.session_state, 'recording_microscope'):
            microscope = st.session_state.recording_microscope
            video_path = microscope.stop_video_recording()
            if video_path:
                st.success(f"Recording stopped and saved: {video_path}")
            else:
                st.error("Failed to save recording")
            microscope.end_connection()
            del st.session_state.recording_microscope
        else:
            st.warning("No active recording found")

    def record_duration_button():
        microscope = MicroscopeDemo(
            HIVEMQ_BROKER,
            port,
            microscopeselection + "clientuser",
            access_key,
            microscopeselection,
        )
        st.info(f"Recording for {recording_duration} seconds...")
        video_path = microscope.record_video_for_duration(
            duration_seconds=recording_duration, 
            fps=recording_fps
        )
        if video_path:
            st.success(f"Recording completed and saved: {video_path}")
        else:
            st.error("Recording failed")
        microscope.end_connection()

    st.title("GUI control")

    microscopeselection = st.selectbox(
        "Choose a microscope:", microscopes, index=microscopes.index("microscope2")
    )

    access_key = st.text_input(label="Enter your access key here:", max_chars=1000)

    st.button("Get position", on_click=get_pos_button)
    st.write("")
    st.button("Take image", on_click=take_image_button)
    st.write("")
    focusamount = st.number_input(
        "Autofocus amount 1-5000", min_value=1, max_value=5000, step=100, value=1000
    )
    st.button("Focus", on_click=focus_button)
    st.write("")
    xmove = st.number_input("X", min_value=-20000, max_value=20000, step=250, value=0)
    ymove = st.number_input("Y", min_value=-20000, max_value=20000, step=250, value=0)
    st.button("Move", on_click=move_button)
    
    st.write("")
    st.markdown("### Video Recording")
    
    col1, col2 = st.columns(2)
    with col1:
        recording_fps = st.number_input("Recording FPS", min_value=1, max_value=10, value=2)
        recording_duration = st.number_input("Duration (seconds)", min_value=5, max_value=300, value=30)
    
    with col2:
        st.button("Start Recording", on_click=start_recording_button)
        st.button("Stop Recording", on_click=stop_recording_button)
        
    st.button("Record for Duration", on_click=record_duration_button, help=f"Record for {recording_duration} seconds automatically")
