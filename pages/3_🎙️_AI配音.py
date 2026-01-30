"""
AI 配音页面
使用 Edge TTS 生成多语言配音
"""

import streamlit as st
import os
import asyncio

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.tts import (
    EdgeTTSEngine, run_tts_segments,
    VOICE_OPTIONS, get_voices_for_language, get_default_voice
)
from utils.translator import (
    SUPPORTED_LANGUAGES, get_language_options, get_tts_code
)
from utils.audio_mixer import AudioMixer, mix_audio, create_dubbing_audio

# 页面配置
st.set_page_config(
    page_title="AI 配音 - Video Factory",
    page_icon="🎙️",
    layout="wide"
)

# 项目目录
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOWNLOAD_DIR = os.path.join(PROJECT_DIR, "downloads")
TTS_DIR = os.path.join(PROJECT_DIR, "tts_output")
os.makedirs(TTS_DIR, exist_ok=True)


# 页面标题
st.title("🎙️ AI 配音工作台")
st.markdown("使用 Edge TTS 生成高质量多语言配音")

st.divider()

# 检查是否有可用的字幕
has_segments = st.session_state.get('segments') is not None
has_translated = st.session_state.get('translated_segments') is not None
has_editor = st.session_state.get('editor_segments') is not None

if not (has_segments or has_translated or has_editor):
    st.warning("""
    ### ⚠️ 暂无可用字幕

    请先完成以下步骤：
    1. 在「🎬 视频处理」页面下载视频并进行语音识别
    2. 或在「✏️ 字幕编辑器」中上传/编辑字幕

    完成后返回此页面生成配音。
    """)
    st.stop()

# 侧边栏 - 配音设置
with st.sidebar:
    st.subheader("⚙️ 配音设置")

    # 选择字幕来源
    subtitle_sources = []
    if has_segments:
        subtitle_sources.append("原语言字幕")
    if has_translated:
        subtitle_sources.append("翻译字幕")
    if has_editor:
        subtitle_sources.append("编辑器字幕")

    subtitle_source = st.selectbox(
        "📄 选择字幕来源",
        subtitle_sources,
        index=len(subtitle_sources) - 1  # 默认选最后一个（最新的）
    )

    # 获取对应的字幕
    if subtitle_source == "原语言字幕":
        working_segments = st.session_state.segments
    elif subtitle_source == "翻译字幕":
        working_segments = st.session_state.translated_segments
    else:
        working_segments = st.session_state.editor_segments

    st.info(f"已选择 {len(working_segments)} 条字幕")

    st.divider()

    # 语言和音色选择
    st.subheader("🎤 音色设置")

    # 目标语言
    lang_options = get_language_options()
    target_lang = st.selectbox(
        "🌐 配音语言",
        options=[code for code, name in lang_options],
        format_func=lambda x: dict(lang_options)[x],
        index=1,  # 默认中文
        help="选择配音的语言"
    )

    # 获取该语言的 TTS 代码
    tts_lang_code = get_tts_code(target_lang)

    # 获取可用音色
    available_voices = get_voices_for_language(tts_lang_code)

    voice = st.selectbox(
        "🎭 选择音色",
        options=[v[0] for v in available_voices],
        format_func=lambda x: dict(available_voices)[x],
        help="选择配音的音色"
    )

    st.divider()

    # 语速和音调
    st.subheader("🎚️ 音频调整")

    rate_value = st.slider(
        "⚡ 语速",
        min_value=-50,
        max_value=100,
        value=0,
        step=10,
        help="调整语速，负值减慢，正值加快"
    )
    rate = f"+{rate_value}%" if rate_value >= 0 else f"{rate_value}%"

    pitch_value = st.slider(
        "🎵 音调",
        min_value=-50,
        max_value=50,
        value=0,
        step=5,
        help="调整音调，负值降低，正值升高"
    )
    pitch = f"+{pitch_value}Hz" if pitch_value >= 0 else f"{pitch_value}Hz"

    st.divider()

    # 混音模式
    st.subheader("🔊 混音设置")

    mix_mode = st.radio(
        "混音模式",
        ["replace", "duck", "overlay"],
        format_func=lambda x: {
            "replace": "🔇 完全替换原音",
            "duck": "🔉 降低原音量",
            "overlay": "🔊 叠加保留原音"
        }[x],
        help="选择如何处理原始音频"
    )

    if mix_mode == "duck":
        original_volume = st.slider(
            "原音量比例",
            min_value=0.1,
            max_value=0.5,
            value=0.3,
            step=0.1
        )
    else:
        original_volume = 0.3

# 主区域 - 预览和生成
col_preview, col_generate = st.columns([1, 1])

with col_preview:
    st.subheader("📝 字幕预览")

    # 显示前几条字幕
    preview_count = min(10, len(working_segments))
    for i, seg in enumerate(working_segments[:preview_count]):
        with st.container():
            col_time, col_text = st.columns([1, 3])
            with col_time:
                start_min = int(seg['start'] // 60)
                start_sec = seg['start'] % 60
                st.caption(f"{start_min:02d}:{start_sec:05.2f}")
            with col_text:
                st.write(seg['text'][:100] + ("..." if len(seg['text']) > 100 else ""))

    if len(working_segments) > preview_count:
        st.caption(f"... 还有 {len(working_segments) - preview_count} 条字幕")

with col_generate:
    st.subheader("🚀 生成配音")

    # 试听功能
    st.markdown("**🎧 试听音色**")
    test_text = st.text_input(
        "输入试听文本",
        value="你好，这是一段测试语音。" if 'zh' in tts_lang_code else "Hello, this is a test voice.",
        label_visibility="collapsed"
    )

    if st.button("▶️ 试听"):
        with st.spinner("生成试听音频..."):
            try:
                test_output = os.path.join(TTS_DIR, "test_voice.mp3")
                engine = EdgeTTSEngine(voice=voice, rate=rate, pitch=pitch)
                asyncio.run(engine.synthesize(test_text, test_output))

                if os.path.exists(test_output):
                    st.audio(test_output)
                    st.success("✅ 试听生成成功")
            except Exception as e:
                st.error(f"试听失败: {str(e)}")

    st.divider()

    # 生成完整配音
    st.markdown("**🎬 生成完整配音**")

    # 计算预估时长
    if working_segments:
        total_duration = working_segments[-1]['end']
        est_minutes = int(total_duration // 60)
        est_seconds = int(total_duration % 60)
        st.info(f"预计配音时长: {est_minutes}分{est_seconds}秒 | 共 {len(working_segments)} 段")

    if st.button("🎙️ 开始生成配音", type="primary"):
        progress_bar = st.progress(0)
        status_text = st.empty()

        try:
            # 步骤1: 生成 TTS 音频段落
            status_text.text("🎤 正在生成语音...")

            # 创建输出目录
            output_dir = os.path.join(TTS_DIR, "segments")
            os.makedirs(output_dir, exist_ok=True)

            # 进度回调
            def update_progress(current, total):
                progress = current / total * 0.7  # TTS 占 70%
                progress_bar.progress(progress)
                status_text.text(f"🎤 正在生成语音... {current}/{total}")

            # 生成 TTS
            tts_segments = run_tts_segments(
                working_segments,
                output_dir,
                voice=voice,
                rate=rate,
                progress_callback=update_progress
            )

            progress_bar.progress(0.7)
            status_text.text("🔊 正在混音...")

            # 步骤2: 混音
            output_audio_path = os.path.join(TTS_DIR, "dubbed_audio.mp3")

            if st.session_state.get('audio_file') and os.path.exists(st.session_state.audio_file):
                # 有原音频，进行混音
                mixed_audio_path = mix_audio(
                    st.session_state.audio_file,
                    tts_segments,
                    output_audio_path,
                    mode=mix_mode,
                    original_volume=original_volume
                )
            else:
                # 无原音频，仅生成配音
                total_duration = working_segments[-1]['end'] if working_segments else 0
                mixed_audio_path = create_dubbing_audio(
                    tts_segments,
                    output_audio_path,
                    total_duration=total_duration
                )

            progress_bar.progress(1.0)
            status_text.text("✅ 配音生成完成！")

            # 保存到 session state
            st.session_state.tts_audio_file = mixed_audio_path

            st.success("🎉 配音生成成功！")

        except Exception as e:
            st.error(f"❌ 生成失败: {str(e)}")
            import traceback
            st.code(traceback.format_exc())

# 结果展示
st.divider()

if st.session_state.get('tts_audio_file') and os.path.exists(st.session_state.tts_audio_file):
    st.subheader("🎧 配音结果")

    col_audio, col_download = st.columns([2, 1])

    with col_audio:
        st.audio(st.session_state.tts_audio_file)

    with col_download:
        with open(st.session_state.tts_audio_file, 'rb') as f:
            st.download_button(
                label="📥 下载配音音频",
                data=f,
                file_name="dubbed_audio.mp3",
                mime="audio/mpeg"
            )

    # 视频合成提示
    st.info("""
    💡 **下一步：视频合成**

    配音音频已生成。如需将配音合成到视频中，可以使用以下工具：
    - **FFmpeg**: `ffmpeg -i video.mp4 -i dubbed_audio.mp3 -c:v copy -map 0:v:0 -map 1:a:0 output.mp4`
    - **剪映/CapCut**: 导入视频和音频，替换音轨
    - **Adobe Premiere**: 导入并替换音频轨道

    视频合成功能将在后续版本中集成。
    """)
