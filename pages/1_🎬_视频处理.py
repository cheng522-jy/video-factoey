"""
视频处理页面
YouTube 视频下载、音频提取、语音识别
"""

import streamlit as st
import yt_dlp
import whisper
import os
import re
from openai import OpenAI

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.translator import (
    SUPPORTED_LANGUAGES, get_language_options,
    get_translate_code, translate_segments
)
from utils.subtitle import SubtitleGenerator, format_timestamp_srt

# 项目目录
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOWNLOAD_DIR = os.path.join(PROJECT_DIR, "downloads")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# 页面配置
st.set_page_config(
    page_title="视频处理 - Video Factory",
    page_icon="🎬",
    layout="wide"
)

# 缓存 Whisper 模型
@st.cache_resource
def load_whisper_model():
    """加载 Whisper 模型（缓存以避免重复加载）"""
    return whisper.load_model("base")


def get_video_info(url):
    """获取 YouTube 视频基本信息"""
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'extract_flat': False,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        return info


def download_video(url, quality, progress_bar, status_text):
    """下载视频"""
    filename = None

    def progress_hook(d):
        nonlocal filename
        if d['status'] == 'downloading':
            if d.get('total_bytes'):
                progress = d['downloaded_bytes'] / d['total_bytes']
            elif d.get('total_bytes_estimate'):
                progress = d['downloaded_bytes'] / d['total_bytes_estimate']
            else:
                progress = 0
            progress_bar.progress(min(progress, 1.0))
            status_text.text(f"下载中... {d.get('_percent_str', '0%')} | 速度: {d.get('_speed_str', 'N/A')}")
        elif d['status'] == 'finished':
            filename = d.get('filename')
            status_text.text("下载完成，正在处理...")

    # 根据质量选择格式
    format_map = {
        "最高质量": 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        "1080p": 'bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080][ext=mp4]/best',
        "720p": 'bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]/best',
        "480p": 'bestvideo[height<=480][ext=mp4]+bestaudio[ext=m4a]/best[height<=480][ext=mp4]/best',
    }
    format_str = format_map.get(quality, format_map["720p"])

    ydl_opts = {
        'format': format_str,
        'outtmpl': os.path.join(DOWNLOAD_DIR, '%(title).50s.%(ext)s'),
        'progress_hooks': [progress_hook],
        'merge_output_format': 'mp4',
        'quiet': True,
        'no_warnings': True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        if not filename:
            filename = ydl.prepare_filename(info)
            if not filename.endswith('.mp4'):
                base = os.path.splitext(filename)[0]
                filename = base + '.mp4'

    return filename


def extract_audio(url, progress_bar, status_text):
    """提取音频为 MP3"""
    filename = None

    def progress_hook(d):
        nonlocal filename
        if d['status'] == 'downloading':
            if d.get('total_bytes'):
                progress = d['downloaded_bytes'] / d['total_bytes']
            elif d.get('total_bytes_estimate'):
                progress = d['downloaded_bytes'] / d['total_bytes_estimate']
            else:
                progress = 0
            progress_bar.progress(min(progress * 0.8, 0.8))
            status_text.text(f"下载音频中... {d.get('_percent_str', '0%')}")
        elif d['status'] == 'finished':
            filename = d.get('filename')
            progress_bar.progress(0.9)
            status_text.text("正在转换为 MP3...")

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': os.path.join(DOWNLOAD_DIR, '%(title).50s.%(ext)s'),
        'progress_hooks': [progress_hook],
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'quiet': True,
        'no_warnings': True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        base_filename = ydl.prepare_filename(info)
        filename = os.path.splitext(base_filename)[0] + '.mp3'

    return filename


def transcribe_audio(audio_path, language='en'):
    """使用 Whisper 转录音频"""
    model = load_whisper_model()
    result = model.transcribe(audio_path, language=language, verbose=False)
    return result


def analyze_with_ai(transcript_text, segments):
    """使用 AI API 进行智能分析"""
    api_key = os.environ.get('GROQ_API_KEY', '')
    if not api_key:
        return None

    base_url = "https://api.groq.com/openai/v1"
    model = "llama-3.3-70b-versatile"

    client = OpenAI(api_key=api_key, base_url=base_url)

    timed_text = ""
    for seg in segments[:50]:  # 限制段落数
        start = format_timestamp_srt(seg['start'])[:8]
        timed_text += f"[{start}] {seg['text']}\n"

    prompt = f"""请分析以下视频转录文本，并提供：

1. **视频整体介绍**（2-3句话，简短有力地概括视频主题和价值）

2. **按主题分段大纲**（根据内容自然分段，格式如下）：
   - 00:00-02:15 章节标题：简要描述
   - 02:15-05:00 章节标题：简要描述
   ...

转录文本：
{timed_text[:6000]}

请用中文回复，格式清晰。"""

    try:
        response = client.chat.completions.create(
            model=model,
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"AI 分析失败: {str(e)}"


# 页面标题
st.title("🎬 视频处理")
st.markdown("下载 YouTube 视频、提取音频、AI 语音识别")

st.divider()

# 语言选择
col_lang1, col_lang2 = st.columns(2)
with col_lang1:
    lang_options = get_language_options()
    source_lang = st.selectbox(
        "🌐 视频源语言",
        options=[code for code, name in lang_options],
        format_func=lambda x: dict(lang_options)[x],
        index=0,  # 默认英语
        help="选择视频的原始语言，影响语音识别准确度"
    )
    st.session_state.source_language = source_lang

with col_lang2:
    target_lang = st.selectbox(
        "🎯 目标翻译语言",
        options=[code for code, name in lang_options],
        format_func=lambda x: dict(lang_options)[x],
        index=1,  # 默认中文
        help="选择要翻译成的目标语言"
    )
    st.session_state.target_language = target_lang

st.divider()

# 输入区域
url = st.text_input(
    "🔗 输入 YouTube 视频链接",
    placeholder="https://www.youtube.com/watch?v=..."
)

# 获取视频信息按钮
if url:
    if st.button("🔍 获取视频信息", type="primary"):
        try:
            with st.spinner("正在获取视频信息..."):
                st.session_state.video_info = get_video_info(url)
                st.session_state.downloaded_file = None
                st.session_state.audio_file = None
                st.session_state.transcript = None
        except Exception as e:
            st.error(f"❌ 获取失败: {str(e)}")

# 显示视频信息和下载选项
if st.session_state.video_info:
    info = st.session_state.video_info

    st.success("✅ 获取成功！")
    st.subheader(f"📺 {info.get('title', '未知标题')}")

    # 视频信息展示
    col1, col2 = st.columns([1, 2])

    with col1:
        thumbnail = info.get('thumbnail')
        if thumbnail:
            st.image(thumbnail, width=300)

    with col2:
        st.write(f"**频道:** {info.get('channel', '未知')}")
        duration = info.get('duration', 0)
        minutes = duration // 60
        seconds = duration % 60
        st.write(f"**时长:** {minutes}分{seconds}秒")
        st.write(f"**观看数:** {info.get('view_count', 0):,}")

    st.divider()

    # 下载选项区域
    st.subheader("⬇️ 下载选项")

    col_video, col_audio = st.columns(2)

    with col_video:
        st.markdown("### 🎬 视频下载")
        quality = st.selectbox(
            "选择视频质量",
            ["最高质量", "1080p", "720p", "480p"]
        )

        if st.button("📥 下载视频", key="download_video"):
            progress_bar = st.progress(0)
            status_text = st.empty()

            try:
                status_text.text("准备下载...")
                filepath = download_video(url, quality, progress_bar, status_text)
                progress_bar.progress(1.0)
                status_text.text("✅ 下载完成！")

                if filepath and os.path.exists(filepath):
                    st.session_state.downloaded_file = filepath
                    with open(filepath, 'rb') as f:
                        st.download_button(
                            label="📁 点击下载视频文件",
                            data=f,
                            file_name=os.path.basename(filepath),
                            mime="video/mp4"
                        )
                    st.info(f"文件已保存: `{filepath}`")
            except Exception as e:
                st.error(f"❌ 下载失败: {str(e)}")

    with col_audio:
        st.markdown("### 🎵 音频提取")
        st.write("提取音频并转换为 MP3 格式")

        if st.button("🎧 仅提取音频 (MP3)", key="extract_audio"):
            progress_bar = st.progress(0)
            status_text = st.empty()

            try:
                status_text.text("准备提取音频...")
                filepath = extract_audio(url, progress_bar, status_text)
                progress_bar.progress(1.0)
                status_text.text("✅ 音频提取完成！")

                if filepath and os.path.exists(filepath):
                    st.session_state.downloaded_file = filepath
                    st.session_state.audio_file = filepath
                    with open(filepath, 'rb') as f:
                        st.download_button(
                            label="📁 点击下载音频文件",
                            data=f,
                            file_name=os.path.basename(filepath),
                            mime="audio/mpeg"
                        )
                    st.info(f"文件已保存: `{filepath}`")
            except Exception as e:
                st.error(f"❌ 音频提取失败: {str(e)}")

    # AI 分析区域
    st.divider()
    st.subheader("🤖 AI 智能分析")
    st.markdown("自动识别语音、生成字幕、智能总结视频内容")

    # 检查是否有音频文件
    if st.session_state.audio_file and os.path.exists(st.session_state.audio_file):
        st.info(f"📁 已检测到音频文件: `{os.path.basename(st.session_state.audio_file)}`")

        if st.button("🚀 开始 AI 分析", type="primary", key="start_analysis"):
            try:
                # 步骤1: 语音识别
                with st.spinner("🎤 正在识别语音（这可能需要几分钟）..."):
                    whisper_lang = SUPPORTED_LANGUAGES.get(source_lang, {}).get('whisper', 'en')
                    transcript = transcribe_audio(st.session_state.audio_file, whisper_lang)
                    st.session_state.transcript = transcript
                    st.session_state.segments = transcript['segments']
                st.success("✅ 语音识别完成！")

                # 步骤2: 生成原语言字幕
                with st.spinner("📝 正在生成原语言字幕..."):
                    base_name = os.path.splitext(st.session_state.audio_file)[0]
                    srt_source_path = base_name + f"_{source_lang}.srt"
                    SubtitleGenerator.generate_srt(transcript['segments'], srt_source_path)
                    st.session_state.srt_en_file = srt_source_path
                st.success("✅ 原语言字幕生成完成！")

                # 步骤3: 翻译字幕
                with st.spinner(f"🌐 正在翻译为{dict(lang_options).get(target_lang, target_lang)}..."):
                    source_translate = get_translate_code(source_lang)
                    target_translate = get_translate_code(target_lang)

                    def update_progress(current, total):
                        pass  # Streamlit spinner 不支持进度更新

                    translated = translate_segments(
                        transcript['segments'],
                        source=source_translate,
                        target=target_translate,
                        progress_callback=update_progress
                    )
                    st.session_state.translated_segments = translated

                    srt_translated_path = base_name + f"_{target_lang}.srt"
                    SubtitleGenerator.generate_srt(translated, srt_translated_path)
                    st.session_state.srt_translated_file = srt_translated_path
                st.success("✅ 翻译字幕生成完成！")

                # 步骤4: AI 智能分析（可选）
                with st.spinner("🧠 正在进行 AI 智能分析..."):
                    analysis = analyze_with_ai(transcript['text'], transcript['segments'])
                    if analysis:
                        st.session_state.analysis_result = analysis
                        st.success("✅ AI 分析完成！")
                    else:
                        st.warning("⚠️ AI 分析跳过（API 不可用）")

            except Exception as e:
                st.error(f"❌ 分析过程出错: {str(e)}")

    else:
        st.warning("⚠️ 请先提取音频文件，然后再进行 AI 分析")

    # 显示分析结果
    if st.session_state.analysis_result:
        st.divider()
        st.subheader("📊 分析结果")
        st.markdown(st.session_state.analysis_result)

    # 显示字幕下载按钮
    if st.session_state.srt_en_file or st.session_state.srt_translated_file:
        st.divider()
        st.subheader("📄 字幕文件下载")

        col_source, col_target = st.columns(2)

        with col_source:
            if st.session_state.srt_en_file and os.path.exists(st.session_state.srt_en_file):
                with open(st.session_state.srt_en_file, 'r', encoding='utf-8') as f:
                    st.download_button(
                        label=f"📥 下载{dict(lang_options).get(source_lang, '原')}语字幕 (.srt)",
                        data=f.read(),
                        file_name=os.path.basename(st.session_state.srt_en_file),
                        mime="text/plain"
                    )

        with col_target:
            if st.session_state.srt_translated_file and os.path.exists(st.session_state.srt_translated_file):
                with open(st.session_state.srt_translated_file, 'r', encoding='utf-8') as f:
                    st.download_button(
                        label=f"📥 下载{dict(lang_options).get(target_lang, '译')}文字幕 (.srt)",
                        data=f.read(),
                        file_name=os.path.basename(st.session_state.srt_translated_file),
                        mime="text/plain"
                    )

        # 提示下一步
        st.info("💡 提示：字幕已生成，可前往「✏️ 字幕编辑器」进行精细调整，或前往「🎙️ AI 配音」生成配音")
