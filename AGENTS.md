# AGENTS.md - Image Translator Codebase Guide

## Project Overview

A web-based image translation tool that:
1. Accepts image uploads (JPG, PNG, WebP)
2. Performs OCR text recognition (PaddleOCR)
3. Translates detected text (Alibaba DashScope Qwen API)
4. Redraws translated text onto the original image

**Tech Stack**: FastAPI (Python) backend + React 18 + TypeScript + Ant Design frontend.

## Build & Run Commands

### Docker (Recommended)
```bash
docker-compose up -d        # Start all services
docker-compose down          # Stop all services
docker-compose logs -f       # View logs
```

### Backend Development
```bash
cd backend
python -m venv venv
source venv/bin/activate     # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Development
```bash
cd frontend
npm install
npm run dev                  # Starts Vite dev server on port 3000
npm run build                # Production build (tsc + vite build)
```

### Testing
No test framework currently configured. If adding tests:
- Backend: Use `pytest` with `pytest-asyncio` for FastAPI endpoints
- Frontend: Use `vitest` with `@testing-library/react`

## Project Structure

```
image-translator/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── routes.py      # FastAPI endpoints
│   │   │   └── models.py      # Pydantic schemas
│   │   ├── services/
│   │   │   ├── ocr_service.py       # PaddleOCR wrapper
│   │   │   ├── translation_service.py # Qwen API integration
│   │   │   └── image_service.py     # PIL/OpenCV image processing
│   │   └── main.py            # FastAPI app entry
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/        # Reusable UI components
│   │   ├── pages/             # Page-level components
│   │   ├── services/          # API client (axios)
│   │   ├── store/             # Zustand state management
│   │   └── types/             # TypeScript interfaces
│   └── package.json
├── fonts/                     # CJK fonts for text rendering
├── uploads/                   # User-uploaded images
├── outputs/                   # Translated image results
└── docker-compose.yml
```

## Code Style Guidelines

### Python (Backend)

**Imports**: Standard library → third-party → local, separated by blank lines.
```python
import os
import uuid
from typing import Optional, List

from fastapi import APIRouter, UploadFile, HTTPException
from pydantic import BaseModel

from app.services.ocr_service import OCRService
```

**Type Hints**: Use `typing` module types. Pydantic models for API schemas.
```python
def translate(texts: List[str], target_language: str) -> List[str]:
    ...

class TaskStatus(BaseModel):
    task_id: str
    status: str
    progress: int
```

**Naming**:
- Functions/variables: `snake_case`
- Classes: `PascalCase`
- Constants: `UPPER_SNAKE_CASE`
- Private methods: `_leading_underscore`

**Error Handling**: Raise `HTTPException` for API errors. Log service errors with `print()`.
```python
if not image.filename:
    raise HTTPException(status_code=400, detail="文件名不能为空")
```

**Docstrings**: Use Chinese docstrings for user-facing code. Brief, no Google-style formatting.
```python
def recognize(self, image_path: str) -> List[Dict]:
    """识别图片中的文字"""
```

### TypeScript (Frontend)

**Imports**: React → third-party → local components → types, separated by blank lines.
```typescript
import React, { useEffect, useState, useCallback } from 'react';
import { Layout, Button, message } from 'antd';
import { UploadOutlined } from '@ant-design/icons';

import UploadArea from '../components/UploadArea';
import { useStore } from '../store';
import { TaskStatus, Language } from '../types';
```

**Components**: Use `React.FC<Props>` with explicit interface for props.
```typescript
interface UploadAreaProps {
  onUpload: (file: File) => void;
  disabled?: boolean;
}

const UploadArea: React.FC<UploadAreaProps> = ({ onUpload, disabled }) => {
  ...
};

export default UploadArea;
```

**Naming**:
- Components: `PascalCase`
- Functions/variables: `camelCase`
- Types/interfaces: `PascalCase`
- Constants: `UPPER_SNAKE_CASE` or `camelCase`

**State Management**: Use Zustand store (`useStore`) for global state. Avoid prop drilling.
```typescript
const { currentTask, setCurrentTask, isLoading } = useStore();
```

**Styling**: Prefer Ant Design components. Use inline `style` props for one-offs. No CSS modules or styled-components.

**Error Handling**: Use Ant Design `message.error()` for user notifications.
```typescript
catch (err: any) {
  const errorMsg = err.response?.data?.detail || '上传失败，请重试';
  message.error(errorMsg);
}
```

## Key Patterns

### Backend API Design
- RESTful endpoints under `/api/v1/` prefix
- Background tasks for long-running operations (OCR + translation)
- Task status polling via `GET /tasks/{task_id}`
- Support both JSON API and HTML responses (browser compatibility)

### Frontend State Flow
1. User uploads image → `uploadImage()` → get `task_id`
2. Poll `getTaskStatus()` every 1s until `completed` or `failed`
3. On success → fetch translated image URL from `result_url`

### Image Processing Pipeline
1. `ocr_service.recognize()` → detect text regions with bounding boxes
2. `image_service.extract_styles()` → extract font color, size, background
3. `translation_service.translate()` → batch translate detected text
4. `image_service.redraw_image()` → render translated text onto image

## Environment Variables

Required in `.env` (copy from `.env.example`):
- `DASHSCOPE_API_KEY` - Alibaba DashScope API key for Qwen translation

Optional:
- `UPLOAD_DIR` - Upload directory (default: `/app/uploads`)
- `OUTPUT_DIR` - Output directory (default: `/app/outputs`)
- `FONT_DIR` - Fonts directory (default: `/app/fonts`)

## Common Tasks

### Adding a New Language
1. Add to `LanguageCode` enum in `backend/app/api/models.py`
2. Add to `get_languages()` in `backend/app/api/routes.py`
3. Add language name mapping in `translation_service.py`

### Changing Translation Engine
Replace `TranslationService` in `backend/app/services/translation_service.py`. Must implement `translate(texts, target_lang, source_lang) -> List[str]`.

### Modifying Image Rendering
Edit `ImageService` methods in `backend/app/services/image_service.py`:
- `_draw_text_in_region_v2()` - main text rendering
- `_calculate_optimal_font_and_lines()` - font size and line wrapping
- `_optimize_text_color()` - contrast adjustment

## Notes

- No linter/formatter configured. Maintain consistency with existing code style.
- No tests exist. Add tests when modifying critical paths (OCR, translation, image rendering).
- OCR model downloads on first use (~100MB). Allow 2-3 minutes for initial startup.
- Font files required in `fonts/` directory for CJK text rendering.
