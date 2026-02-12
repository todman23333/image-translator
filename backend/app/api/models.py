from pydantic import BaseModel
from typing import List, Optional, Tuple
from enum import Enum

class LanguageCode(str, Enum):
    ZH = "zh"  # 中文
    EN = "en"  # 英文
    JA = "ja"  # 日文
    KO = "ko"  # 韩文
    FR = "fr"  # 法文
    DE = "de"  # 德文
    ES = "es"  # 西班牙文
    RU = "ru"  # 俄文
    IT = "it"  # 意大利文
    PT = "pt"  # 葡萄牙文

class TextRegion(BaseModel):
    id: int
    bbox: List[List[int]]  # [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
    text: str
    translated_text: Optional[str] = None
    confidence: float
    language: Optional[str] = None

class StyleInfo(BaseModel):
    font_color: List[int]  # [R, G, B]
    background_color: List[int]  # [R, G, B]
    font_size: int
    font_weight: str  # normal, bold
    alignment: str  # left, center, right
    is_vertical: bool = False

class TextRegionWithStyle(BaseModel):
    region: TextRegion
    style: Optional[StyleInfo] = None

class TranslationRequest(BaseModel):
    target_language: LanguageCode
    source_language: Optional[LanguageCode] = None

class TranslationResponse(BaseModel):
    success: bool
    data: Optional[dict] = None
    message: Optional[str] = None

class TaskStatus(BaseModel):
    task_id: str
    status: str  # pending, processing, completed, failed
    progress: int  # 0-100
    result_url: Optional[str] = None
    detected_language: Optional[str] = None
    text_regions: Optional[List[TextRegion]] = None
    error_message: Optional[str] = None

class Language(BaseModel):
    code: str
    name: str
    native_name: str
