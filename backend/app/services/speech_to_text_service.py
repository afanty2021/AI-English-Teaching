"""
语音转文本 (STT) 服务
集成 OpenAI Whisper API 实现高质量语音识别
"""

import os
import io
import base64
import aiofiles
import openai
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.responses import StreamingResponse
from typing import Optional, Dict, Any
import logging
import asyncio
from pathlib import Path
import mimetypes

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# OpenAI客户端初始化
openai_client = openai.AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# 支持的语言列表
SUPPORTED_LANGUAGES = {
    "zh": "中文",
    "en": "英语",
    "ja": "日语",
    "ko": "韩语",
    "fr": "法语",
    "es": "西班牙语",
    "de": "德语",
    "it": "意大利语",
    "pt": "葡萄牙语",
    "ru": "俄语",
    "ar": "阿拉伯语"
}

class SpeechToTextService:
    """语音转文本服务"""

    def __init__(self):
        self.client = openai_client
        self.max_file_size = 25 * 1024 * 1024  # 25MB (Whisper API限制)
        self.supported_formats = {".mp3", ".mp4", ".mpeg", ".mpga", ".m4a", ".wav", ".webm"}

    async def transcribe_audio(
        self,
        audio_file: UploadFile,
        language: str = "zh",
        model: str = "whisper-1",
        response_format: str = "verbose_json",
        temperature: float = 0.2
    ) -> Dict[str, Any]:
        """
        转录音频文件

        Args:
            audio_file: 音频文件
            language: 语言代码
            model: Whisper模型
            response_format: 响应格式
            temperature: 生成温度

        Returns:
            转录结果字典
        """
        try:
            # 验证文件格式
            file_extension = Path(audio_file.filename).suffix.lower()
            if file_extension not in self.supported_formats:
                raise HTTPException(
                    status_code=400,
                    detail=f"不支持的音频格式: {file_extension}"
                )

            # 验证文件大小
            audio_content = await audio_file.read()
            if len(audio_content) > self.max_file_size:
                raise HTTPException(
                    status_code=400,
                    detail=f"文件大小超过限制 ({self.max_file_size // 1024 // 1024}MB)"
                )

            # 准备文件对象
            file_buffer = io.BytesIO(audio_content)
            file_buffer.name = audio_file.filename

            logger.info(f"开始转录音频文件: {audio_file.filename}, 语言: {language}")

            # 调用OpenAI Whisper API
            response = await self.client.audio.transcriptions.create(
                model=model,
                file=file_buffer,
                language=language if language != "auto" else None,
                response_format=response_format,
                timestamp_granularities=["word"] if response_format == "verbose_json" else None,
                temperature=temperature
            )

            # 处理响应结果
            result = self._process_transcription_response(response, language)

            logger.info(f"转录完成: {result['text'][:50]}...")
            return result

        except openai.APIError as e:
            logger.error(f"OpenAI API错误: {e}")
            raise HTTPException(status_code=500, detail=f"语音识别服务错误: {str(e)}")
        except Exception as e:
            logger.error(f"转录失败: {e}")
            raise HTTPException(status_code=500, detail=f"转录失败: {str(e)}")

    def _process_transcription_response(self, response, language: str) -> Dict[str, Any]:
        """处理转录响应"""
        base_result = {
            "text": response.text,
            "language": getattr(response, 'language', language),
            "duration": getattr(response, 'duration', None),
            "model": "whisper-1"
        }

        # 如果是详细格式，添加额外信息
        if hasattr(response, 'words') and response.words:
            base_result["words"] = [
                {
                    "word": word.word,
                    "start": word.start,
                    "end": word.end
                }
                for word in response.words
            ]

            # 计算词数统计
            base_result["word_count"] = len(response.words)
            base_result["confidence_score"] = self._calculate_confidence_score(response.words)

        # 添加语言信息
        if language != "auto":
            base_result["language_name"] = SUPPORTED_LANGUAGES.get(language, "未知")

        return base_result

    def _calculate_confidence_score(self, words) -> float:
        """计算置信度分数"""
        if not words:
            return 0.0

        # Whisper不直接提供置信度，这里基于词数和时间间隔估算
        total_duration = words[-1].end - words[0].start if len(words) > 1 else 1.0
        avg_word_duration = total_duration / len(words)

        # 基于平均词持续时间估算置信度 (较短的持续时间通常表示更高的置信度)
        confidence = max(0.5, min(1.0, 1.0 - (avg_word_duration - 0.3) * 0.5))

        return round(confidence, 3)

    async def transcribe_base64_audio(
        self,
        audio_data: str,
        format: str = "wav",
        language: str = "zh"
    ) -> Dict[str, Any]:
        """
        转录Base64编码的音频数据

        Args:
            audio_data: Base64编码的音频数据
            format: 音频格式
            language: 语言代码

        Returns:
            转录结果字典
        """
        try:
            # 解码Base64数据
            audio_bytes = base64.b64decode(audio_data)

            # 创建临时文件
            temp_filename = f"temp_audio.{format}"

            async with aiofiles.tempfile.NamedTemporaryFile(
                delete=False, suffix=f".{format}"
            ) as temp_file:
                await temp_file.write(audio_bytes)
                temp_path = temp_file.name

            try:
                # 创建模拟的UploadFile对象
                class MockUploadFile:
                    def __init__(self, filename: str, content: bytes):
                        self.filename = filename
                        self.content = content

                    async def read(self) -> bytes:
                        return self.content

                mock_file = MockUploadFile(temp_filename, audio_bytes)

                # 使用现有的转录方法
                result = await self.transcribe_audio(
                    mock_file,
                    language=language
                )

                return result

            finally:
                # 清理临时文件
                try:
                    os.unlink(temp_path)
                except:
                    pass

        except Exception as e:
            logger.error(f"Base64音频转录失败: {e}")
            raise HTTPException(status_code=500, detail=f"Base64音频转录失败: {str(e)}")

    async def batch_transcribe(
        self,
        audio_files: list[UploadFile],
        language: str = "zh",
        model: str = "whisper-1"
    ) -> Dict[str, Any]:
        """
        批量转录音频文件

        Args:
            audio_files: 音频文件列表
            language: 语言代码
            model: Whisper模型

        Returns:
            批量转录结果
        """
        results = []
        errors = []

        for i, audio_file in enumerate(audio_files):
            try:
                result = await self.transcribe_audio(
                    audio_file,
                    language=language,
                    model=model
                )
                result["file_index"] = i
                result["filename"] = audio_file.filename
                results.append(result)

            except Exception as e:
                errors.append({
                    "file_index": i,
                    "filename": audio_file.filename,
                    "error": str(e)
                })

        return {
            "total_files": len(audio_files),
            "successful": len(results),
            "failed": len(errors),
            "results": results,
            "errors": errors
        }

    def get_supported_languages(self) -> Dict[str, str]:
        """获取支持的语言列表"""
        return SUPPORTED_LANGUAGES

    def validate_language_code(self, language_code: str) -> bool:
        """验证语言代码是否支持"""
        return language_code in SUPPORTED_LANGUAGES

# 创建服务实例
speech_to_text_service = SpeechToTextService()

# 创建API路由
router = APIRouter(prefix="/api/v1/stt", tags=["语音转文本"])

@router.post("/transcribe")
async def transcribe_audio_endpoint(
    audio_file: UploadFile = File(...),
    language: str = "zh",
    model: str = "whisper-1",
    response_format: str = "verbose_json",
    temperature: float = 0.2,
    service: SpeechToTextService = Depends(lambda: speech_to_text_service)
):
    """
    语音转文本接口

    - **audio_file**: 音频文件 (支持 mp3, mp4, m4a, wav, webm)
    - **language**: 语言代码 (zh, en, ja, ko, fr, es, de, it, pt, ru, ar)
    - **model**: 模型名称 (默认 whisper-1)
    - **response_format**: 响应格式 (json, text, verbose_json, srt, vtt)
    - **temperature**: 生成温度 (0.0-1.0)
    """
    return await service.transcribe_audio(
        audio_file=audio_file,
        language=language,
        model=model,
        response_format=response_format,
        temperature=temperature
    )

@router.post("/transcribe/base64")
async def transcribe_base64_endpoint(
    audio_data: str,
    format: str = "wav",
    language: str = "zh",
    model: str = "whisper-1",
    service: SpeechToTextService = Depends(lambda: speech_to_text_service)
):
    """
    Base64音频转文本接口

    - **audio_data**: Base64编码的音频数据
    - **format**: 音频格式 (wav, mp3, m4a, etc.)
    - **language**: 语言代码
    - **model**: 模型名称
    """
    return await service.transcribe_base64_audio(
        audio_data=audio_data,
        format=format,
        language=language
    )

@router.post("/batch-transcribe")
async def batch_transcribe_endpoint(
    audio_files: list[UploadFile] = File(...),
    language: str = "zh",
    model: str = "whisper-1",
    service: SpeechToTextService = Depends(lambda: speech_to_text_service)
):
    """
    批量语音转文本接口

    - **audio_files**: 音频文件列表
    - **language**: 语言代码
    - **model**: 模型名称
    """
    return await service.batch_transcribe(
        audio_files=audio_files,
        language=language,
        model=model
    )

@router.get("/languages")
async def get_supported_languages_endpoint(
    service: SpeechToTextService = Depends(lambda: speech_to_text_service)
):
    """获取支持的语言列表"""
    return {
        "supported_languages": service.get_supported_languages(),
        "total": len(service.get_supported_languages())
    }

@router.get("/health")
async def health_check():
    """健康检查接口"""
    return {
        "status": "healthy",
        "service": "speech-to-text",
        "version": "1.0.0",
        "supported_formats": list(speech_to_text_service.supported_formats)
    }