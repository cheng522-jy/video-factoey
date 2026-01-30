"""
交互式字幕编辑器页面
可视化编辑字幕文本和时间轴
"""

import streamlit as st
import pandas as pd
import os

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.subtitle import (
    SubtitleParser, SubtitleGenerator,
    format_timestamp_srt, parse_timestamp_srt,
    merge_segments, split_segment, adjust_timing
)

# 页面配置
st.set_page_config(
    page_title="字幕编辑器 - Video Factory",
    page_icon="✏️",
    layout="wide"
)

# 项目目录
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOWNLOAD_DIR = os.path.join(PROJECT_DIR, "downloads")


def format_time_display(seconds):
    """格式化时间显示 (MM:SS.mmm)"""
    minutes = int(seconds // 60)
    secs = seconds % 60
    return f"{minutes:02d}:{secs:05.2f}"


def parse_time_display(time_str):
    """解析时间显示格式"""
    try:
        # 尝试 SRT 格式
        if ',' in time_str or len(time_str) > 8:
            return parse_timestamp_srt(time_str)
        # 简单格式 MM:SS.mm
        parts = time_str.split(':')
        if len(parts) == 2:
            minutes = int(parts[0])
            secs = float(parts[1])
            return minutes * 60 + secs
        elif len(parts) == 3:
            hours = int(parts[0])
            minutes = int(parts[1])
            secs = float(parts[2].replace(',', '.'))
            return hours * 3600 + minutes * 60 + secs
    except:
        pass
    return 0.0


def segments_to_dataframe(segments):
    """将字幕段落转换为 DataFrame"""
    data = []
    for i, seg in enumerate(segments):
        data.append({
            '序号': i + 1,
            '开始': format_time_display(seg['start']),
            '结束': format_time_display(seg['end']),
            '文本': seg['text'],
            '原文': seg.get('original', '')
        })
    return pd.DataFrame(data)


def dataframe_to_segments(df):
    """将 DataFrame 转换回字幕段落"""
    segments = []
    for _, row in df.iterrows():
        segments.append({
            'start': parse_time_display(row['开始']),
            'end': parse_time_display(row['结束']),
            'text': row['文本'],
            'original': row.get('原文', '')
        })
    return segments


# 页面标题
st.title("✏️ 交互式字幕编辑器")
st.markdown("编辑字幕文本、调整时间轴、合并拆分字幕")

st.divider()

# 初始化编辑状态
if 'editor_segments' not in st.session_state:
    st.session_state.editor_segments = None
if 'editor_source' not in st.session_state:
    st.session_state.editor_source = None

# 侧边栏 - 视频预览和文件操作
with st.sidebar:
    st.subheader("📺 视频预览")

    if st.session_state.get('downloaded_file') and os.path.exists(st.session_state.downloaded_file):
        if st.session_state.downloaded_file.endswith('.mp4'):
            st.video(st.session_state.downloaded_file)
        elif st.session_state.downloaded_file.endswith('.mp3'):
            st.audio(st.session_state.downloaded_file)
    else:
        st.info("暂无视频/音频文件")

    st.divider()

    st.subheader("📂 加载字幕")

    # 从 session state 加载
    load_source = st.selectbox(
        "选择字幕来源",
        ["从识别结果加载", "从翻译结果加载", "上传字幕文件"]
    )

    if load_source == "从识别结果加载":
        if st.button("📥 加载原语言字幕"):
            if st.session_state.get('segments'):
                st.session_state.editor_segments = [
                    dict(seg) for seg in st.session_state.segments
                ]
                st.session_state.editor_source = "原语言字幕"
                st.success("✅ 已加载")
                st.rerun()
            else:
                st.warning("请先在「视频处理」页面进行语音识别")

    elif load_source == "从翻译结果加载":
        if st.button("📥 加载翻译字幕"):
            if st.session_state.get('translated_segments'):
                st.session_state.editor_segments = [
                    dict(seg) for seg in st.session_state.translated_segments
                ]
                st.session_state.editor_source = "翻译字幕"
                st.success("✅ 已加载")
                st.rerun()
            else:
                st.warning("请先在「视频处理」页面进行翻译")

    else:  # 上传文件
        uploaded_file = st.file_uploader(
            "上传 SRT/VTT 文件",
            type=['srt', 'vtt']
        )
        if uploaded_file:
            content = uploaded_file.read().decode('utf-8')
            if uploaded_file.name.endswith('.vtt'):
                segments = SubtitleParser.parse_vtt(content)
            else:
                segments = SubtitleParser.parse_srt(content)
            st.session_state.editor_segments = segments
            st.session_state.editor_source = uploaded_file.name
            st.success(f"✅ 已加载 {len(segments)} 条字幕")
            st.rerun()

# 主编辑区域
if st.session_state.editor_segments:
    segments = st.session_state.editor_segments

    st.info(f"📄 当前编辑: {st.session_state.editor_source} | 共 {len(segments)} 条字幕")

    # 工具栏
    col_tools = st.columns([1, 1, 1, 1, 2])

    with col_tools[0]:
        if st.button("🔄 刷新"):
            st.rerun()

    with col_tools[1]:
        if st.button("↩️ 撤销"):
            st.warning("撤销功能开发中")

    with col_tools[2]:
        time_adjust = st.number_input(
            "时间偏移(秒)",
            value=0.0,
            step=0.1,
            format="%.1f",
            label_visibility="collapsed"
        )

    with col_tools[3]:
        if st.button("⏱️ 整体偏移"):
            if time_adjust != 0:
                for seg in segments:
                    seg['start'] = max(0, seg['start'] + time_adjust)
                    seg['end'] = max(0.1, seg['end'] + time_adjust)
                st.session_state.editor_segments = segments
                st.success(f"已偏移 {time_adjust} 秒")
                st.rerun()

    st.divider()

    # 可编辑表格
    df = segments_to_dataframe(segments)

    edited_df = st.data_editor(
        df,
        use_container_width=True,
        num_rows="dynamic",
        column_config={
            '序号': st.column_config.NumberColumn(
                "序号",
                disabled=True,
                width="small"
            ),
            '开始': st.column_config.TextColumn(
                "开始时间",
                width="small",
                help="格式: MM:SS.mm"
            ),
            '结束': st.column_config.TextColumn(
                "结束时间",
                width="small",
                help="格式: MM:SS.mm"
            ),
            '文本': st.column_config.TextColumn(
                "字幕文本",
                width="large"
            ),
            '原文': st.column_config.TextColumn(
                "原文",
                width="medium",
                disabled=True
            ),
        },
        hide_index=True,
        key="subtitle_editor"
    )

    # 检测编辑并更新
    if not df.equals(edited_df):
        st.session_state.editor_segments = dataframe_to_segments(edited_df)

    st.divider()

    # 高级操作
    st.subheader("🛠️ 高级操作")

    col_adv1, col_adv2 = st.columns(2)

    with col_adv1:
        st.markdown("**合并字幕**")
        merge_start = st.number_input("起始序号", min_value=1, max_value=len(segments), value=1, key="merge_start")
        merge_end = st.number_input("结束序号", min_value=1, max_value=len(segments), value=min(2, len(segments)), key="merge_end")

        if st.button("🔗 合并选中字幕"):
            if merge_start < merge_end:
                indices = list(range(merge_start - 1, merge_end))
                st.session_state.editor_segments = merge_segments(segments, indices)
                st.success(f"已合并第 {merge_start}-{merge_end} 条字幕")
                st.rerun()
            else:
                st.warning("请选择至少两条连续的字幕")

    with col_adv2:
        st.markdown("**拆分字幕**")
        split_index = st.number_input("要拆分的序号", min_value=1, max_value=len(segments), value=1, key="split_index")
        split_ratio = st.slider("拆分位置", 0.1, 0.9, 0.5, 0.1, key="split_ratio")

        if st.button("✂️ 拆分字幕"):
            seg = segments[split_index - 1]
            split_time = seg['start'] + (seg['end'] - seg['start']) * split_ratio
            st.session_state.editor_segments = split_segment(segments, split_index - 1, split_time)
            st.success(f"已拆分第 {split_index} 条字幕")
            st.rerun()

    st.divider()

    # 导出选项
    st.subheader("💾 保存与导出")

    col_export1, col_export2, col_export3 = st.columns(3)

    with col_export1:
        # 生成 SRT 内容
        srt_content = ""
        for i, seg in enumerate(st.session_state.editor_segments, 1):
            start = format_timestamp_srt(seg['start'])
            end = format_timestamp_srt(seg['end'])
            srt_content += f"{i}\n{start} --> {end}\n{seg['text']}\n\n"

        st.download_button(
            label="📥 导出 SRT 格式",
            data=srt_content,
            file_name="edited_subtitle.srt",
            mime="text/plain"
        )

    with col_export2:
        # 生成 VTT 内容
        vtt_content = "WEBVTT\n\n"
        for i, seg in enumerate(st.session_state.editor_segments, 1):
            start = format_timestamp_srt(seg['start']).replace(',', '.')
            end = format_timestamp_srt(seg['end']).replace(',', '.')
            vtt_content += f"{i}\n{start} --> {end}\n{seg['text']}\n\n"

        st.download_button(
            label="📥 导出 VTT 格式",
            data=vtt_content,
            file_name="edited_subtitle.vtt",
            mime="text/plain"
        )

    with col_export3:
        if st.button("💾 保存到工作区"):
            # 更新 session state 中的字幕
            if st.session_state.editor_source == "翻译字幕":
                st.session_state.translated_segments = st.session_state.editor_segments
            else:
                st.session_state.segments = st.session_state.editor_segments
            st.success("✅ 已保存到工作区，可在「AI 配音」中使用")

else:
    # 无字幕时显示提示
    st.info("""
    ### 📝 开始编辑字幕

    请从左侧边栏选择字幕来源：

    1. **从识别结果加载** - 使用「视频处理」页面生成的原语言字幕
    2. **从翻译结果加载** - 使用翻译后的字幕
    3. **上传字幕文件** - 上传已有的 SRT/VTT 文件

    ---

    **编辑功能：**
    - 直接点击表格单元格编辑文本
    - 修改开始/结束时间调整时间轴
    - 使用「合并」功能合并多条字幕
    - 使用「拆分」功能将长字幕分开
    - 支持导出 SRT/VTT 格式
    """)
