import { create } from 'zustand';
import { TaskStatus, Language, TextRegion } from '../types';

interface AppState {
  // 当前任务
  currentTask: TaskStatus | null;
  setCurrentTask: (task: TaskStatus | null) => void;
  
  // 图片数据
  originalImage: string | null;
  setOriginalImage: (image: string | null) => void;
  
  translatedImage: string | null;
  setTranslatedImage: (image: string | null) => void;
  
  // 文字区域
  textRegions: TextRegion[];
  setTextRegions: (regions: TextRegion[]) => void;
  updateTextRegion: (id: number, translatedText: string) => void;
  
  // 设置
  targetLanguage: string;
  setTargetLanguage: (lang: string) => void;
  sourceLanguage: string;
  setSourceLanguage: (lang: string) => void;
  
  // 语言列表
  languages: Language[];
  setLanguages: (langs: Language[]) => void;
  
  // 加载状态
  isLoading: boolean;
  setIsLoading: (loading: boolean) => void;
  
  // 错误信息
  error: string | null;
  setError: (error: string | null) => void;
}

export const useStore = create<AppState>((set) => ({
  currentTask: null,
  setCurrentTask: (task) => set({ currentTask: task }),
  
  originalImage: null,
  setOriginalImage: (image) => set({ originalImage: image }),
  
  translatedImage: null,
  setTranslatedImage: (image) => set({ translatedImage: image }),
  
  textRegions: [],
  setTextRegions: (regions) => set({ textRegions: regions }),
  updateTextRegion: (id, translatedText) => set((state) => ({
    textRegions: state.textRegions.map((region) =>
      region.id === id ? { ...region, translated_text: translatedText } : region
    ),
  })),
  
  targetLanguage: 'zh',
  setTargetLanguage: (lang) => set({ targetLanguage: lang }),
  sourceLanguage: 'auto',
  setSourceLanguage: (lang) => set({ sourceLanguage: lang }),
  
  languages: [],
  setLanguages: (langs) => set({ languages: langs }),
  
  isLoading: false,
  setIsLoading: (loading) => set({ isLoading: loading }),
  
  error: null,
  setError: (error) => set({ error }),
}));
