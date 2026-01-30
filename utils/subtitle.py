"""
字幕处理模块
支持 SRT/VTT 格式的解析和生成
"""

import re
import os
from typing import List, Dict, Optional
from dataclasses import dataclass


@dataclass
class SubtitleSegment:
    """字幕段落数据类"""
    index: int
    start: float  # 秒
    end: float    # 秒
    text: str
    original: str = ""  # 原文（翻译时保留）


def format_timestamp_srt(seconds: float) -> str:
    """
    将秒数转换为 SRT 时间戳格式
    格式: HH:MM:SS,mmm
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds - int(seconds)) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def format_timestamp_vtt(seconds: float) -> str:
    """
    将秒数转换为 VTT 时间戳格式
    格式: HH:MM:SS.mmm
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds - int(seconds)) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}.{millis:03d}"


def parse_timestamp_srt(timestamp: str) -> float:
    """
    解析 SRT 时间戳为秒数
    格式: HH:MM:SS,mmm
    """
    pattern = r'(\d{2}):(\d{2}):(\d{2})[,.](\d{3})'
    match = re.match(pattern, timestamp.strip())
    if not match:
        return 0.0
    hours, minutes, seconds, millis = map(int, match.groups())
    return hours * 3600 + minutes * 60 + seconds + millis / 1000


def parse_timestamp_vtt(timestamp: str) -> float:
    """
    解析 VTT 时间戳为秒数
    格式: HH:MM:SS.mmm 或 MM:SS.mmm
    """
    # 尝试完整格式
    pattern_full = r'(\d{2}):(\d{2}):(\d{2})[.,](\d{3})'
    match = re.match(pattern_full, timestamp.strip())
    if match:
        hours, minutes, seconds, millis = map(int, match.groups())
        return hours * 3600 + minutes * 60 + seconds + millis / 1000

    # 尝试短格式
    pattern_short = r'(\d{2}):(\d{2})[.,](\d{3})'
    match = re.match(pattern_short, timestamp.strip())
    if match:
        minutes, seconds, millis = map(int, match.groups())
        return minutes * 60 + seconds + millis / 1000

    return 0.0


class SubtitleParser:
    """字幕解析器"""

    @staticmethod
    def parse_srt(content: str) -> List[Dict]:
        """
        解析 SRT 格式字幕

        Args:
            content: SRT 文件内容

        Returns:
            字幕段落列表
        """
        segments = []
        blocks = re.split(r'\n\n+', content.strip())

        for block in blocks:
            lines = block.strip().split('\n')
            if len(lines) < 3:
                continue

            # 解析序号
            try:
                index = int(lines[0].strip())
            except ValueError:
                continue

            # 解析时间戳
            time_match = re.match(
                r'(\d{2}:\d{2}:\d{2}[,\.]\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2}[,\.]\d{3})',
                lines[1].strip()
            )
            if not time_match:
                continue

            start = parse_timestamp_srt(time_match.group(1))
            end = parse_timestamp_srt(time_match.group(2))

            # 解析文本（可能多行）
            text = '\n'.join(lines[2:]).strip()

            segments.append({
                'index': index,
                'start': start,
                'end': end,
                'text': text
            })

        return segments

    @staticmethod
    def parse_vtt(content: str) -> List[Dict]:
        """
        解析 VTT 格式字幕

        Args:
            content: VTT 文件内容

        Returns:
            字幕段落列表
        """
        segments = []

        # 移除 WEBVTT 头部
        content = re.sub(r'^WEBVTT.*?\n\n', '', content, flags=re.DOTALL)
        blocks = re.split(r'\n\n+', content.strip())

        index = 0
        for block in blocks:
            lines = block.strip().split('\n')
            if not lines:
                continue

            # 查找时间戳行
            time_line_idx = 0
            for i, line in enumerate(lines):
                if '-->' in line:
                    time_line_idx = i
                    break
            else:
                continue

            # 解析时间戳
            time_match = re.match(
                r'(\d{2}:\d{2}:\d{2}[.,]\d{3}|\d{2}:\d{2}[.,]\d{3})\s*-->\s*'
                r'(\d{2}:\d{2}:\d{2}[.,]\d{3}|\d{2}:\d{2}[.,]\d{3})',
                lines[time_line_idx].strip()
            )
            if not time_match:
                continue

            start = parse_timestamp_vtt(time_match.group(1))
            end = parse_timestamp_vtt(time_match.group(2))

            # 解析文本
            text = '\n'.join(lines[time_line_idx + 1:]).strip()

            index += 1
            segments.append({
                'index': index,
                'start': start,
                'end': end,
                'text': text
            })

        return segments

    @staticmethod
    def parse_file(file_path: str) -> List[Dict]:
        """
        根据文件扩展名自动解析字幕文件

        Args:
            file_path: 字幕文件路径

        Returns:
            字幕段落列表
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        ext = os.path.splitext(file_path)[1].lower()
        if ext == '.vtt':
            return SubtitleParser.parse_vtt(content)
        else:  # 默认 SRT
            return SubtitleParser.parse_srt(content)


class SubtitleGenerator:
    """字幕生成器"""

    @staticmethod
    def generate_srt(segments: List[Dict], output_path: str) -> str:
        """
        生成 SRT 格式字幕文件

        Args:
            segments: 字幕段落列表
            output_path: 输出文件路径

        Returns:
            输出文件路径
        """
        with open(output_path, 'w', encoding='utf-8') as f:
            for i, seg in enumerate(segments, 1):
                start = format_timestamp_srt(seg['start'])
                end = format_timestamp_srt(seg['end'])
                text = seg['text'].strip()
                f.write(f"{i}\n{start} --> {end}\n{text}\n\n")
        return output_path

    @staticmethod
    def generate_vtt(segments: List[Dict], output_path: str) -> str:
        """
        生成 VTT 格式字幕文件

        Args:
            segments: 字幕段落列表
            output_path: 输出文件路径

        Returns:
            输出文件路径
        """
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("WEBVTT\n\n")
            for i, seg in enumerate(segments, 1):
                start = format_timestamp_vtt(seg['start'])
                end = format_timestamp_vtt(seg['end'])
                text = seg['text'].strip()
                f.write(f"{i}\n{start} --> {end}\n{text}\n\n")
        return output_path

    @staticmethod
    def generate(segments: List[Dict], output_path: str,
                 format: str = 'srt') -> str:
        """
        生成字幕文件

        Args:
            segments: 字幕段落列表
            output_path: 输出文件路径
            format: 格式 ('srt' 或 'vtt')

        Returns:
            输出文件路径
        """
        if format.lower() == 'vtt':
            return SubtitleGenerator.generate_vtt(segments, output_path)
        else:
            return SubtitleGenerator.generate_srt(segments, output_path)


def merge_segments(segments: List[Dict], indices: List[int]) -> List[Dict]:
    """
    合并指定的字幕段落

    Args:
        segments: 字幕段落列表
        indices: 要合并的段落索引列表（必须连续）

    Returns:
        合并后的字幕段落列表
    """
    if not indices or len(indices) < 2:
        return segments

    indices = sorted(indices)
    result = []

    # 合并选中的段落
    merged_start = segments[indices[0]]['start']
    merged_end = segments[indices[-1]]['end']
    merged_text = ' '.join(segments[i]['text'] for i in indices)

    # 构建新列表
    for i, seg in enumerate(segments):
        if i == indices[0]:
            result.append({
                'start': merged_start,
                'end': merged_end,
                'text': merged_text
            })
        elif i not in indices:
            result.append(seg)

    # 重新编号
    for i, seg in enumerate(result):
        seg['index'] = i + 1

    return result


def split_segment(segments: List[Dict], index: int,
                  split_position: float) -> List[Dict]:
    """
    拆分指定的字幕段落

    Args:
        segments: 字幕段落列表
        index: 要拆分的段落索引
        split_position: 拆分位置（秒）

    Returns:
        拆分后的字幕段落列表
    """
    if index < 0 or index >= len(segments):
        return segments

    seg = segments[index]
    if split_position <= seg['start'] or split_position >= seg['end']:
        return segments

    # 简单按比例拆分文本
    text = seg['text']
    ratio = (split_position - seg['start']) / (seg['end'] - seg['start'])
    split_char = int(len(text) * ratio)

    # 尝试在空格处拆分
    space_pos = text.rfind(' ', 0, split_char)
    if space_pos > 0:
        split_char = space_pos

    text1 = text[:split_char].strip()
    text2 = text[split_char:].strip()

    # 构建新列表
    result = segments[:index]
    result.append({
        'start': seg['start'],
        'end': split_position,
        'text': text1
    })
    result.append({
        'start': split_position,
        'end': seg['end'],
        'text': text2
    })
    result.extend(segments[index + 1:])

    # 重新编号
    for i, s in enumerate(result):
        s['index'] = i + 1

    return result


def adjust_timing(segments: List[Dict], index: int,
                  start_delta: float = 0, end_delta: float = 0) -> List[Dict]:
    """
    调整指定字幕段落的时间

    Args:
        segments: 字幕段落列表
        index: 要调整的段落索引
        start_delta: 开始时间调整量（秒）
        end_delta: 结束时间调整量（秒）

    Returns:
        调整后的字幕段落列表
    """
    if index < 0 or index >= len(segments):
        return segments

    result = [dict(seg) for seg in segments]  # 深拷贝
    seg = result[index]

    new_start = max(0, seg['start'] + start_delta)
    new_end = max(new_start + 0.1, seg['end'] + end_delta)

    seg['start'] = new_start
    seg['end'] = new_end

    return result
