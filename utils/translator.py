"""
多语言翻译模块
支持多种语言之间的翻译
"""

from deep_translator import GoogleTranslator
from typing import List, Dict, Optional

# 支持的语言配置
# 格式: 语言代码 -> (显示名称, Whisper代码, 翻译代码, TTS语言代码)
SUPPORTED_LANGUAGES = {
    'en': {
        'name': 'English 英语',
        'whisper': 'en',
        'translate': 'en',
        'tts': 'en-US',
    },
    'zh': {
        'name': '中文',
        'whisper': 'zh',
        'translate': 'zh-CN',
        'tts': 'zh-CN',
    },
    'ja': {
        'name': '日本語 日语',
        'whisper': 'ja',
        'translate': 'ja',
        'tts': 'ja-JP',
    },
    'ko': {
        'name': '한국어 韩语',
        'whisper': 'ko',
        'translate': 'ko',
        'tts': 'ko-KR',
    },
    'es': {
        'name': 'Español 西班牙语',
        'whisper': 'es',
        'translate': 'es',
        'tts': 'es-ES',
    },
    'fr': {
        'name': 'Français 法语',
        'whisper': 'fr',
        'translate': 'fr',
        'tts': 'fr-FR',
    },
    'de': {
        'name': 'Deutsch 德语',
        'whisper': 'de',
        'translate': 'de',
        'tts': 'de-DE',
    },
    'ru': {
        'name': 'Русский 俄语',
        'whisper': 'ru',
        'translate': 'ru',
        'tts': 'ru-RU',
    },
    'pt': {
        'name': 'Português 葡萄牙语',
        'whisper': 'pt',
        'translate': 'pt',
        'tts': 'pt-BR',
    },
    'ar': {
        'name': 'العربية 阿拉伯语',
        'whisper': 'ar',
        'translate': 'ar',
        'tts': 'ar-SA',
    },
    'it': {
        'name': 'Italiano 意大利语',
        'whisper': 'it',
        'translate': 'it',
        'tts': 'it-IT',
    },
    'nl': {
        'name': 'Nederlands 荷兰语',
        'whisper': 'nl',
        'translate': 'nl',
        'tts': 'nl-NL',
    },
    'pl': {
        'name': 'Polski 波兰语',
        'whisper': 'pl',
        'translate': 'pl',
        'tts': 'pl-PL',
    },
    'tr': {
        'name': 'Türkçe 土耳其语',
        'whisper': 'tr',
        'translate': 'tr',
        'tts': 'tr-TR',
    },
    'vi': {
        'name': 'Tiếng Việt 越南语',
        'whisper': 'vi',
        'translate': 'vi',
        'tts': 'vi-VN',
    },
    'th': {
        'name': 'ไทย 泰语',
        'whisper': 'th',
        'translate': 'th',
        'tts': 'th-TH',
    },
    'id': {
        'name': 'Bahasa Indonesia 印尼语',
        'whisper': 'id',
        'translate': 'id',
        'tts': 'id-ID',
    },
    'hi': {
        'name': 'हिन्दी 印地语',
        'whisper': 'hi',
        'translate': 'hi',
        'tts': 'hi-IN',
    },
}


def get_language_options() -> List[tuple]:
    """获取语言选项列表，用于 UI 下拉菜单"""
    return [(code, info['name']) for code, info in SUPPORTED_LANGUAGES.items()]


def get_language_name(code: str) -> str:
    """获取语言显示名称"""
    return SUPPORTED_LANGUAGES.get(code, {}).get('name', code)


def get_whisper_code(code: str) -> str:
    """获取 Whisper 语言代码"""
    return SUPPORTED_LANGUAGES.get(code, {}).get('whisper', 'en')


def get_translate_code(code: str) -> str:
    """获取翻译 API 语言代码"""
    return SUPPORTED_LANGUAGES.get(code, {}).get('translate', 'en')


def get_tts_code(code: str) -> str:
    """获取 TTS 语言代码"""
    return SUPPORTED_LANGUAGES.get(code, {}).get('tts', 'en-US')


class MultiLangTranslator:
    """多语言翻译器"""

    def __init__(self, source_lang: str = 'auto', target_lang: str = 'zh-CN'):
        """
        初始化翻译器

        Args:
            source_lang: 源语言代码，'auto' 表示自动检测
            target_lang: 目标语言代码
        """
        self.source = source_lang
        self.target = target_lang
        self._translator = None

    @property
    def translator(self):
        """延迟初始化翻译器"""
        if self._translator is None:
            self._translator = GoogleTranslator(
                source=self.source,
                target=self.target
            )
        return self._translator

    def translate(self, text: str) -> str:
        """
        翻译单条文本

        Args:
            text: 要翻译的文本

        Returns:
            翻译后的文本
        """
        if not text or not text.strip():
            return text
        try:
            return self.translator.translate(text)
        except Exception as e:
            print(f"翻译失败: {e}")
            return text

    def translate_segments(self, segments: List[Dict],
                           progress_callback=None) -> List[Dict]:
        """
        批量翻译字幕段落，保留时间戳

        Args:
            segments: 字幕段落列表，每个包含 start, end, text
            progress_callback: 进度回调函数 (current, total)

        Returns:
            翻译后的字幕段落列表
        """
        translated = []
        total = len(segments)

        for i, seg in enumerate(segments):
            text = seg.get('text', '')
            translated_text = self.translate(text)

            translated.append({
                'start': seg['start'],
                'end': seg['end'],
                'text': translated_text,
                'original': text
            })

            if progress_callback:
                progress_callback(i + 1, total)

        return translated

    def set_languages(self, source: str, target: str):
        """
        更改翻译语言对

        Args:
            source: 源语言代码
            target: 目标语言代码
        """
        self.source = source
        self.target = target
        self._translator = None  # 重置翻译器


def translate_text(text: str, source: str = 'auto',
                   target: str = 'zh-CN') -> str:
    """
    便捷函数：翻译单条文本

    Args:
        text: 要翻译的文本
        source: 源语言
        target: 目标语言

    Returns:
        翻译后的文本
    """
    translator = MultiLangTranslator(source, target)
    return translator.translate(text)


def translate_segments(segments: List[Dict], source: str = 'auto',
                       target: str = 'zh-CN',
                       progress_callback=None) -> List[Dict]:
    """
    便捷函数：批量翻译字幕段落

    Args:
        segments: 字幕段落列表
        source: 源语言
        target: 目标语言
        progress_callback: 进度回调

    Returns:
        翻译后的字幕段落列表
    """
    translator = MultiLangTranslator(source, target)
    return translator.translate_segments(segments, progress_callback)
