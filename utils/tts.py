"""
Edge TTS 语音合成模块
使用微软免费 TTS API 生成高质量语音
"""

import edge_tts
import asyncio
import os
from typing import List, Dict, Optional

# 每种语言的可用音色
VOICE_OPTIONS = {
    'zh-CN': [
        ('zh-CN-XiaoxiaoNeural', '晓晓 (女声，温柔)'),
        ('zh-CN-XiaoyiNeural', '晓伊 (女声，活泼)'),
        ('zh-CN-YunxiNeural', '云希 (男声，年轻)'),
        ('zh-CN-YunjianNeural', '云健 (男声，成熟)'),
        ('zh-CN-YunyangNeural', '云扬 (男声，新闻)'),
    ],
    'en-US': [
        ('en-US-JennyNeural', 'Jenny (Female, Friendly)'),
        ('en-US-GuyNeural', 'Guy (Male, Casual)'),
        ('en-US-AriaNeural', 'Aria (Female, Professional)'),
        ('en-US-DavisNeural', 'Davis (Male, Calm)'),
    ],
    'ja-JP': [
        ('ja-JP-NanamiNeural', 'Nanami (女声)'),
        ('ja-JP-KeitaNeural', 'Keita (男声)'),
    ],
    'ko-KR': [
        ('ko-KR-SunHiNeural', 'SunHi (여성)'),
        ('ko-KR-InJoonNeural', 'InJoon (남성)'),
    ],
    'es-ES': [
        ('es-ES-ElviraNeural', 'Elvira (Femenino)'),
        ('es-ES-AlvaroNeural', 'Alvaro (Masculino)'),
    ],
    'fr-FR': [
        ('fr-FR-DeniseNeural', 'Denise (Féminin)'),
        ('fr-FR-HenriNeural', 'Henri (Masculin)'),
    ],
    'de-DE': [
        ('de-DE-KatjaNeural', 'Katja (Weiblich)'),
        ('de-DE-ConradNeural', 'Conrad (Männlich)'),
    ],
    'ru-RU': [
        ('ru-RU-SvetlanaNeural', 'Светлана (Женский)'),
        ('ru-RU-DmitryNeural', 'Дмитрий (Мужской)'),
    ],
    'pt-BR': [
        ('pt-BR-FranciscaNeural', 'Francisca (Feminino)'),
        ('pt-BR-AntonioNeural', 'Antonio (Masculino)'),
    ],
    'ar-SA': [
        ('ar-SA-ZariyahNeural', 'زارية (أنثى)'),
        ('ar-SA-HamedNeural', 'حامد (ذكر)'),
    ],
}

# 语言代码到默认音色的映射
DEFAULT_VOICES = {
    'zh-CN': 'zh-CN-XiaoxiaoNeural',
    'en-US': 'en-US-JennyNeural',
    'ja-JP': 'ja-JP-NanamiNeural',
    'ko-KR': 'ko-KR-SunHiNeural',
    'es-ES': 'es-ES-ElviraNeural',
    'fr-FR': 'fr-FR-DeniseNeural',
    'de-DE': 'de-DE-KatjaNeural',
    'ru-RU': 'ru-RU-SvetlanaNeural',
    'pt-BR': 'pt-BR-FranciscaNeural',
    'ar-SA': 'ar-SA-ZariyahNeural',
}


class EdgeTTSEngine:
    """Edge TTS 语音合成引擎"""

    def __init__(self, voice: str = 'zh-CN-XiaoxiaoNeural',
                 rate: str = '+0%', pitch: str = '+0Hz'):
        """
        初始化 TTS 引擎

        Args:
            voice: 音色名称
            rate: 语速调整，范围 -50% ~ +100%
            pitch: 音调调整，范围 -50Hz ~ +50Hz
        """
        self.voice = voice
        self.rate = rate
        self.pitch = pitch

    async def synthesize(self, text: str, output_path: str) -> str:
        """
        合成单段语音

        Args:
            text: 要合成的文本
            output_path: 输出音频文件路径

        Returns:
            输出文件路径
        """
        if not text.strip():
            return output_path

        communicate = edge_tts.Communicate(
            text, self.voice, rate=self.rate, pitch=self.pitch
        )
        await communicate.save(output_path)
        return output_path

    async def synthesize_segments(self, segments: List[Dict],
                                   output_dir: str,
                                   progress_callback=None) -> List[Dict]:
        """
        批量合成字幕段落的语音

        Args:
            segments: 字幕段落列表，每个包含 start, end, text
            output_dir: 输出目录
            progress_callback: 进度回调函数 (current, total)

        Returns:
            音频文件信息列表
        """
        os.makedirs(output_dir, exist_ok=True)
        audio_files = []
        total = len(segments)

        for i, seg in enumerate(segments):
            text = seg.get('text', '').strip()
            if not text:
                continue

            output_path = os.path.join(output_dir, f"segment_{i:04d}.mp3")
            await self.synthesize(text, output_path)

            audio_files.append({
                'path': output_path,
                'start': seg['start'],
                'end': seg['end'],
                'text': text,
                'index': i
            })

            if progress_callback:
                progress_callback(i + 1, total)

        return audio_files


def run_tts(text: str, output_path: str, voice: str,
            rate: str = '+0%', pitch: str = '+0Hz') -> str:
    """
    同步包装器，供 Streamlit 调用

    Args:
        text: 要合成的文本
        output_path: 输出文件路径
        voice: 音色名称
        rate: 语速
        pitch: 音调

    Returns:
        输出文件路径
    """
    engine = EdgeTTSEngine(voice=voice, rate=rate, pitch=pitch)
    asyncio.run(engine.synthesize(text, output_path))
    return output_path


def run_tts_segments(segments: List[Dict], output_dir: str,
                     voice: str, rate: str = '+0%',
                     progress_callback=None) -> List[Dict]:
    """
    同步批量合成，供 Streamlit 调用

    Args:
        segments: 字幕段落列表
        output_dir: 输出目录
        voice: 音色名称
        rate: 语速
        progress_callback: 进度回调

    Returns:
        音频文件信息列表
    """
    engine = EdgeTTSEngine(voice=voice, rate=rate)
    return asyncio.run(engine.synthesize_segments(
        segments, output_dir, progress_callback
    ))


def get_voices_for_language(lang_code: str) -> List[tuple]:
    """获取指定语言的可用音色列表"""
    return VOICE_OPTIONS.get(lang_code, VOICE_OPTIONS['en-US'])


def get_default_voice(lang_code: str) -> str:
    """获取指定语言的默认音色"""
    return DEFAULT_VOICES.get(lang_code, 'en-US-JennyNeural')
