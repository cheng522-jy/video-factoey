"""
Video Factory - 视频工厂
自动化 YouTube 视频处理工具

主入口文件 - 多页面应用
"""

import streamlit as st
import os
import ssl
import certifi

# 修复 SSL 证书问题
os.environ['SSL_CERT_FILE'] = certifi.where()
os.environ['REQUESTS_CA_BUNDLE'] = certifi.where()

# 项目目录
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
DOWNLOAD_DIR = os.path.join(PROJECT_DIR, "downloads")
TTS_DIR = os.path.join(PROJECT_DIR, "tts_output")

# 确保目录存在
os.makedirs(DOWNLOAD_DIR, exist_ok=True)
os.makedirs(TTS_DIR, exist_ok=True)

# 页面配置
st.set_page_config(
    page_title="Video Factory 视频工厂",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 初始化全局 session state
if 'video_info' not in st.session_state:
    st.session_state.video_info = None
if 'downloaded_file' not in st.session_state:
    st.session_state.downloaded_file = None
if 'audio_file' not in st.session_state:
    st.session_state.audio_file = None
if 'transcript' not in st.session_state:
    st.session_state.transcript = None
if 'segments' not in st.session_state:
    st.session_state.segments = None
if 'translated_segments' not in st.session_state:
    st.session_state.translated_segments = None
if 'analysis_result' not in st.session_state:
    st.session_state.analysis_result = None
if 'srt_en_file' not in st.session_state:
    st.session_state.srt_en_file = None
if 'srt_translated_file' not in st.session_state:
    st.session_state.srt_translated_file = None
if 'tts_audio_file' not in st.session_state:
    st.session_state.tts_audio_file = None
if 'final_video_file' not in st.session_state:
    st.session_state.final_video_file = None
if 'source_language' not in st.session_state:
    st.session_state.source_language = 'en'
if 'target_language' not in st.session_state:
    st.session_state.target_language = 'zh'

# 主页内容
st.title("🎬 Video Factory 视频工厂")
st.markdown("### 从 YouTube 链接到完整多媒体素材包")

st.divider()

# 功能介绍
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    ### 📥 视频处理
    - YouTube 视频下载
    - 多种质量选择
    - 音频提取 (MP3)
    - AI 语音识别
    - 智能内容分析
    """)

with col2:
    st.markdown("""
    ### ✏️ 字幕编辑
    - 可视化字幕编辑
    - 时间轴调整
    - 字幕合并/拆分
    - 多格式导出 (SRT/VTT)
    - 实时预览
    """)

with col3:
    st.markdown("""
    ### 🎙️ AI 配音
    - 多语言翻译
    - Edge TTS 语音合成
    - 多种音色选择
    - 语速/音调调整
    - 音频混音导出
    """)

st.divider()

# 快速开始
st.markdown("### 🚀 快速开始")
st.markdown("""
1. **视频处理**: 在左侧导航栏选择「🎬 视频处理」，输入 YouTube 链接开始
2. **字幕编辑**: 完成语音识别后，可在「✏️ 字幕编辑器」中精细调整字幕
3. **AI 配音**: 在「🎙️ AI 配音」中选择目标语言和音色，生成配音视频
""")

# 当前状态
st.divider()
st.markdown("### 📊 当前工作状态")

status_col1, status_col2, status_col3 = st.columns(3)

with status_col1:
    if st.session_state.video_info:
        st.success(f"✅ 已加载视频: {st.session_state.video_info.get('title', '未知')[:30]}...")
    else:
        st.info("⏳ 等待加载视频")

with status_col2:
    if st.session_state.transcript:
        seg_count = len(st.session_state.transcript.get('segments', []))
        st.success(f"✅ 已识别字幕: {seg_count} 段")
    else:
        st.info("⏳ 等待语音识别")

with status_col3:
    if st.session_state.tts_audio_file:
        st.success("✅ 已生成配音")
    else:
        st.info("⏳ 等待生成配音")

# 页脚
st.divider()
st.caption("Video Factory v2.0 | 使用 `./venv/bin/python -m streamlit run app.py` 启动")
