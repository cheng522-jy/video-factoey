# Video Factory 视频工厂 🎬

自动化 YouTube 视频处理工具 - 从 YouTube 链接到完整多媒体素材包

## 功能特性

### 📥 视频处理
- YouTube 视频下载（多种质量选择）
- 音频提取 (MP3)
- AI 语音识别 (Whisper)
- 智能内容分析

### ✏️ 字幕编辑
- 可视化字幕编辑器
- 时间轴调整
- 字幕合并/拆分
- 多格式导出 (SRT/VTT)

### 🎙️ AI 配音
- 18 种语言支持
- Edge TTS 语音合成
- 多种音色选择（男声/女声）
- 语速/音调调整
- 三种混音模式

## 支持语言

英语、中文、日语、韩语、西班牙语、法语、德语、俄语、葡萄牙语、阿拉伯语、意大利语、荷兰语、波兰语、土耳其语、越南语、泰语、印尼语、印地语

## 安装

```bash
# 克隆仓库
git clone https://github.com/YOUR_USERNAME/video-factory.git
cd video-factory

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
```

## 配置

设置 Groq API Key（用于 AI 分析，可选）：

```bash
export GROQ_API_KEY="your_api_key_here"
```

## 运行

```bash
streamlit run app.py
```

然后在浏览器中打开 http://localhost:8501

## 技术栈

- **前端**: Streamlit
- **视频下载**: yt-dlp
- **语音识别**: OpenAI Whisper
- **翻译**: Google Translator (deep-translator)
- **语音合成**: Microsoft Edge TTS
- **音频处理**: pydub

## 项目结构

```
video-factory/
├── app.py                      # 主入口
├── pages/
│   ├── 1_🎬_视频处理.py        # 视频下载、语音识别
│   ├── 2_✏️_字幕编辑器.py      # 交互式字幕编辑
│   └── 3_🎙️_AI配音.py         # TTS 配音生成
├── utils/
│   ├── tts.py                  # Edge TTS 封装
│   ├── translator.py           # 多语言翻译
│   ├── subtitle.py             # 字幕解析/生成
│   └── audio_mixer.py          # 音频混音
└── requirements.txt
```

## License

MIT License
