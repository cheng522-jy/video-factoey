# Video Factory v2.0 - 功能扩展设计文档

## 概述

本次更新为 Video Factory 添加了三个核心功能：
1. AI 语音合成/配音功能
2. 交互式字幕编辑器
3. 多语言支持扩展

## 项目结构

```
video-factory/
├── app.py                      # 主入口（多页面应用首页）
├── pages/
│   ├── 1_🎬_视频处理.py        # 视频下载、语音识别
│   ├── 2_✏️_字幕编辑器.py      # 交互式字幕编辑
│   └── 3_🎙️_AI配音.py         # TTS 配音生成
├── utils/
│   ├── __init__.py
│   ├── tts.py                  # Edge TTS 封装
│   ├── translator.py           # 多语言翻译
│   ├── subtitle.py             # 字幕解析/生成
│   └── audio_mixer.py          # 音频混音
├── downloads/                  # 下载文件目录
├── tts_output/                 # TTS 输出目录
└── requirements.txt            # 依赖列表
```

## 功能详情

### 1. AI 语音合成/配音 (Edge TTS)

**技术选型**: Microsoft Edge TTS
- 免费、高质量
- 支持 300+ 语音
- 多语言支持

**核心模块**: `utils/tts.py`
- `EdgeTTSEngine`: 异步 TTS 引擎
- `run_tts_segments()`: 批量合成字幕
- `VOICE_OPTIONS`: 各语言可用音色

**功能特性**:
- 多种音色选择（男声/女声）
- 语速调整 (-50% ~ +100%)
- 音调调整 (-50Hz ~ +50Hz)
- 三种混音模式：替换/降低原音/叠加

### 2. 交互式字幕编辑器

**技术选型**: Streamlit `st.data_editor`

**核心模块**: `utils/subtitle.py`
- `SubtitleParser`: SRT/VTT 解析
- `SubtitleGenerator`: 字幕生成
- `merge_segments()`: 合并字幕
- `split_segment()`: 拆分字幕
- `adjust_timing()`: 时间调整

**功能特性**:
- 可编辑表格界面
- 时间轴调整
- 字幕合并/拆分
- 整体时间偏移
- SRT/VTT 导出

### 3. 多语言支持

**技术选型**:
- 语音识别: OpenAI Whisper
- 翻译: Google Translator (deep-translator)
- TTS: Edge TTS

**核心模块**: `utils/translator.py`
- `SUPPORTED_LANGUAGES`: 18 种语言配置
- `MultiLangTranslator`: 翻译器类
- `translate_segments()`: 批量翻译

**支持语言**:
- 英语、中文、日语、韩语
- 西班牙语、法语、德语、俄语
- 葡萄牙语、阿拉伯语、意大利语
- 荷兰语、波兰语、土耳其语
- 越南语、泰语、印尼语、印地语

## 依赖更新

新增依赖:
```
edge-tts>=6.1.0      # TTS 语音合成
pydub>=0.25.1        # 音频处理
moviepy>=1.0.3       # 视频处理（预留）
```

## 使用流程

1. **视频处理页面**
   - 输入 YouTube 链接
   - 选择源语言和目标语言
   - 下载视频/提取音频
   - AI 语音识别 + 翻译

2. **字幕编辑器**（可选）
   - 加载识别/翻译字幕
   - 编辑文本内容
   - 调整时间轴
   - 导出 SRT/VTT

3. **AI 配音页面**
   - 选择字幕来源
   - 选择音色和语速
   - 试听效果
   - 生成完整配音

## 后续扩展

1. **说话人识别** - 使用 pyannote-audio 或 whisperx
2. **视频合成** - 使用 moviepy 将配音合成到视频
3. **字幕烧录** - 将字幕硬编码到视频中
4. **批量处理** - 支持多视频队列处理

## 启动命令

```bash
cd video-factory
./venv/bin/pip install -r requirements.txt
./venv/bin/python -m streamlit run app.py
```
