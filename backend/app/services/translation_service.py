import requests
import os
import json
from typing import List, Optional


class TranslationService:
    def __init__(self):
        # 阿里云DashScope API配置
        self.api_key = os.environ.get("DASHSCOPE_API_KEY", "")
        if not self.api_key:
            print("警告: 未设置DASHSCOPE_API_KEY环境变量")
        self.base_url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"
        self.model = "qwen-turbo"  # 可以使用 qwen-turbo, qwen-plus, qwen-max

    def translate(
        self,
        texts: List[str],
        target_language: str,
        source_language: Optional[str] = None,
    ) -> List[str]:
        """
        使用阿里云千问模型批量翻译文字

        Args:
            texts: 待翻译的文字列表
            target_language: 目标语言代码
            source_language: 源语言代码，None表示自动检测

        Returns:
            翻译后的文字列表
        """
        results = []

        # 语言代码映射
        lang_map = {
            "zh": "中文",
            "en": "英文",
            "ja": "日文",
            "ko": "韩文",
            "fr": "法文",
            "de": "德文",
            "es": "西班牙文",
            "ru": "俄文",
            "it": "意大利文",
            "pt": "葡萄牙文",
        }

        target_lang_name = lang_map.get(target_language, target_language)
        source_lang_name = (
            lang_map.get(source_language, source_language)
            if source_language
            else "自动检测"
        )

        for text in texts:
            if not text or not text.strip():
                results.append(text)
                continue

            try:
                translated = self._translate_single(
                    text, target_lang_name, source_lang_name
                )
                results.append(translated)
            except Exception as e:
                print(f"翻译失败 '{text}': {str(e)}")
                # 如果翻译失败，保留原文
                results.append(text)

        return results

    def _translate_single(
        self, text: str, target_language: str, source_language: str
    ) -> str:
        """
        使用千问模型翻译单个文本

        Args:
            text: 待翻译的文本
            target_language: 目标语言名称
            source_language: 源语言名称

        Returns:
            翻译后的文本
        """
        # 构建提示词
        if source_language and source_language != "自动检测":
            prompt = f"请将以下{source_language}翻译成{target_language}，只返回翻译结果，不要解释：\n\n{text}"
        else:
            prompt = f"请将以下内容翻译成{target_language}，只返回翻译结果，不要解释：\n\n{text}"

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

        payload = {
            "model": self.model,
            "input": {
                "messages": [
                    {
                        "role": "system",
                        "content": f"你是一个专业的翻译助手，请将用户提供的文字翻译成{target_language}。只返回翻译结果，不要添加任何解释、说明或额外内容。",
                    },
                    {"role": "user", "content": prompt},
                ]
            },
            "parameters": {
                "result_format": "message",
                "max_tokens": 1500,
                "temperature": 0.3,  # 降低温度以获得更稳定的翻译结果
            },
        }

        try:
            response = requests.post(
                self.base_url, headers=headers, json=payload, timeout=30
            )
            response.raise_for_status()

            data = response.json()

            # 解析响应
            if "output" in data and "choices" in data["output"]:
                choices = data["output"]["choices"]
                if choices and len(choices) > 0:
                    message = choices[0].get("message", {})
                    translated_text = message.get("content", "").strip()

                    # 清理可能的引号或多余内容
                    translated_text = translated_text.strip("\"'")

                    if translated_text:
                        return translated_text

            # 如果解析失败，返回原文
            print(f"千问API响应解析失败: {data}")
            return text

        except requests.exceptions.RequestException as e:
            print(f"请求千问API失败: {str(e)}")
            return text
        except Exception as e:
            print(f"处理千问API响应失败: {str(e)}")
            return text

    def translate_with_fallback(
        self,
        texts: List[str],
        target_language: str,
        source_language: Optional[str] = None,
    ) -> List[str]:
        """
        带备用方案的翻译
        """
        return self.translate(texts, target_language, source_language)
