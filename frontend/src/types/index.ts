export interface TextRegion {
  id: number;
  bbox: number[][];
  text: string;
  translated_text?: string;
  confidence: number;
  language?: string;
}

export interface StyleInfo {
  font_color: number[];
  background_color: number[];
  font_size: number;
  font_weight: string;
  alignment: string;
  is_vertical: boolean;
}

export interface TaskStatus {
  task_id: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  progress: number;
  result_url?: string;
  detected_language?: string;
  text_regions?: TextRegion[];
  error_message?: string;
}

export interface Language {
  code: string;
  name: string;
  native_name: string;
}

export interface TranslationResponse {
  success: boolean;
  data?: {
    task_id: string;
    status: string;
    progress: number;
  };
  message?: string;
}
