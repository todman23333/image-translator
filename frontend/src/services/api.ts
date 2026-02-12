import axios from 'axios';
import { TaskStatus, Language, TranslationResponse } from '../types';

const API_BASE_URL = '/api/v1';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'multipart/form-data',
  },
});

export const uploadImage = async (
  file: File,
  targetLanguage: string,
  sourceLanguage?: string
): Promise<TranslationResponse> => {
  const formData = new FormData();
  formData.append('image', file);
  formData.append('target_language', targetLanguage);
  if (sourceLanguage) {
    formData.append('source_language', sourceLanguage);
  }

  const response = await api.post('/translate', formData);
  return response.data;
};

export const getTaskStatus = async (taskId: string): Promise<TaskStatus> => {
  const response = await api.get(`/tasks/${taskId}`);
  return response.data.data;
};

export const downloadResult = (taskId: string): string => {
  return `${API_BASE_URL}/download/${taskId}`;
};

export const getLanguages = async (): Promise<Language[]> => {
  const response = await api.get('/languages');
  return response.data.data;
};
