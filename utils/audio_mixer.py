"""
音频混音模块
支持将 TTS 配音与原音频混合
"""

import os
from typing import List, Dict, Optional
from pydub import AudioSegment


class AudioMixer:
    """音频混音器"""

    def __init__(self, original_audio_path: Optional[str] = None):
        """
        初始化混音器

        Args:
            original_audio_path: 原始音频文件路径
        """
        self.original = None
        self.original_path = original_audio_path

        if original_audio_path and os.path.exists(original_audio_path):
            self.load_original(original_audio_path)

    def load_original(self, audio_path: str):
        """
        加载原始音频

        Args:
            audio_path: 音频文件路径
        """
        ext = os.path.splitext(audio_path)[1].lower()
        if ext == '.mp3':
            self.original = AudioSegment.from_mp3(audio_path)
        elif ext == '.wav':
            self.original = AudioSegment.from_wav(audio_path)
        elif ext == '.m4a':
            self.original = AudioSegment.from_file(audio_path, format='m4a')
        else:
            self.original = AudioSegment.from_file(audio_path)
        self.original_path = audio_path

    def create_silent_base(self, duration_ms: int) -> AudioSegment:
        """
        创建静音基底

        Args:
            duration_ms: 时长（毫秒）

        Returns:
            静音音频段
        """
        return AudioSegment.silent(duration=duration_ms)

    def mix_with_dubbing(self, tts_segments: List[Dict],
                         mode: str = 'replace',
                         original_volume: float = 0.3) -> AudioSegment:
        """
        将 TTS 音频与原音频混合

        Args:
            tts_segments: TTS 音频段落列表，每个包含 path, start, end
            mode: 混音模式
                - 'replace': 完全替换原音轨
                - 'duck': 降低原音量，突出配音
                - 'overlay': 叠加，保留原音
            original_volume: 原音量比例（仅 duck 模式有效）

        Returns:
            混合后的音频
        """
        if not tts_segments:
            return self.original if self.original else AudioSegment.empty()

        # 计算总时长
        max_end = max(seg['end'] for seg in tts_segments)
        if self.original:
            duration_ms = max(len(self.original), int(max_end * 1000))
        else:
            duration_ms = int(max_end * 1000)

        # 根据模式创建基底
        if mode == 'replace':
            result = self.create_silent_base(duration_ms)
        elif mode == 'duck' and self.original:
            # 降低原音量
            db_reduction = 20 * (1 - original_volume)  # 转换为 dB
            result = self.original - db_reduction
            # 确保长度足够
            if len(result) < duration_ms:
                result = result + self.create_silent_base(duration_ms - len(result))
        elif mode == 'overlay' and self.original:
            result = self.original
            if len(result) < duration_ms:
                result = result + self.create_silent_base(duration_ms - len(result))
        else:
            result = self.create_silent_base(duration_ms)

        # 在对应时间点插入 TTS 音频
        for seg in tts_segments:
            if not os.path.exists(seg['path']):
                continue

            try:
                tts_audio = AudioSegment.from_mp3(seg['path'])
                start_ms = int(seg['start'] * 1000)

                # 叠加音频
                result = result.overlay(tts_audio, position=start_ms)
            except Exception as e:
                print(f"混音失败 {seg['path']}: {e}")
                continue

        return result

    def concatenate_segments(self, tts_segments: List[Dict],
                             gap_ms: int = 100) -> AudioSegment:
        """
        按顺序拼接 TTS 音频段落

        Args:
            tts_segments: TTS 音频段落列表
            gap_ms: 段落间隔（毫秒）

        Returns:
            拼接后的音频
        """
        result = AudioSegment.empty()
        gap = AudioSegment.silent(duration=gap_ms)

        for i, seg in enumerate(tts_segments):
            if not os.path.exists(seg['path']):
                continue

            try:
                tts_audio = AudioSegment.from_mp3(seg['path'])
                if i > 0:
                    result += gap
                result += tts_audio
            except Exception as e:
                print(f"拼接失败 {seg['path']}: {e}")
                continue

        return result

    def export(self, audio: AudioSegment, output_path: str,
               format: str = 'mp3', bitrate: str = '192k') -> str:
        """
        导出音频文件

        Args:
            audio: 音频段
            output_path: 输出路径
            format: 格式 (mp3, wav, etc.)
            bitrate: 比特率

        Returns:
            输出文件路径
        """
        audio.export(output_path, format=format, bitrate=bitrate)
        return output_path


def mix_audio(original_path: str, tts_segments: List[Dict],
              output_path: str, mode: str = 'replace',
              original_volume: float = 0.3) -> str:
    """
    便捷函数：混合音频

    Args:
        original_path: 原始音频路径
        tts_segments: TTS 音频段落列表
        output_path: 输出路径
        mode: 混音模式
        original_volume: 原音量比例

    Returns:
        输出文件路径
    """
    mixer = AudioMixer(original_path)
    mixed = mixer.mix_with_dubbing(tts_segments, mode, original_volume)
    return mixer.export(mixed, output_path)


def create_dubbing_audio(tts_segments: List[Dict],
                         output_path: str,
                         total_duration: float = None) -> str:
    """
    便捷函数：仅从 TTS 段落创建配音音频

    Args:
        tts_segments: TTS 音频段落列表
        output_path: 输出路径
        total_duration: 总时长（秒），如果指定则填充静音

    Returns:
        输出文件路径
    """
    mixer = AudioMixer()
    mixed = mixer.mix_with_dubbing(tts_segments, mode='replace')

    # 如果指定了总时长，确保音频长度
    if total_duration:
        target_ms = int(total_duration * 1000)
        if len(mixed) < target_ms:
            mixed = mixed + AudioSegment.silent(duration=target_ms - len(mixed))

    return mixer.export(mixed, output_path)
