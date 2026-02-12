import React, { useEffect, useState, useCallback } from 'react';
import { Layout, Typography, Button, Space, message, Alert } from 'antd';
import { TranslationOutlined } from '@ant-design/icons';
import UploadArea from '../components/UploadArea';
import LanguageSelector from '../components/LanguageSelector';
import ProgressBar from '../components/ProgressBar';
import ImagePreview from '../components/ImagePreview';
import { useStore } from '../store';
import { uploadImage, getTaskStatus, getLanguages, downloadResult } from '../services/api';

const { Header, Content } = Layout;
const { Title } = Typography;

const POLLING_INTERVAL = 1000; // 1秒轮询一次

const HomePage: React.FC = () => {
  const {
    currentTask,
    setCurrentTask,
    originalImage,
    setOriginalImage,
    translatedImage,
    setTranslatedImage,
    targetLanguage,
    setTargetLanguage,
    sourceLanguage,
    setSourceLanguage,
    languages,
    setLanguages,
    isLoading,
    setIsLoading,
    error,
    setError,
  } = useStore();

  // 加载语言列表
  useEffect(() => {
    const loadLanguages = async () => {
      try {
        const langs = await getLanguages();
        setLanguages(langs);
      } catch (err) {
        console.error('加载语言列表失败:', err);
      }
    };
    loadLanguages();
  }, [setLanguages]);

  // 轮询任务状态
  useEffect(() => {
    if (!currentTask || currentTask.status === 'completed' || currentTask.status === 'failed') {
      return;
    }

    const interval = setInterval(async () => {
      try {
        const status = await getTaskStatus(currentTask.task_id);
        setCurrentTask(status);

        if (status.status === 'completed') {
          if (status.result_url) {
            setTranslatedImage(downloadResult(currentTask.task_id));
          }
          setIsLoading(false);
          message.success('翻译完成！');
        } else if (status.status === 'failed') {
          setIsLoading(false);
          setError(status.error_message || '处理失败');
          message.error(status.error_message || '处理失败');
        }
      } catch (err) {
        console.error('获取任务状态失败:', err);
      }
    }, POLLING_INTERVAL);

    return () => clearInterval(interval);
  }, [currentTask, setCurrentTask, setTranslatedImage, setIsLoading, setError]);

  const handleUpload = useCallback(async (file: File) => {
    setIsLoading(true);
    setError(null);
    
    // 创建本地预览
    const reader = new FileReader();
    reader.onload = (e) => {
      setOriginalImage(e.target?.result as string);
    };
    reader.readAsDataURL(file);

    try {
      const response = await uploadImage(file, targetLanguage, sourceLanguage);
      
      if (response.success && response.data) {
        setCurrentTask({
          task_id: response.data.task_id,
          status: 'processing',
          progress: 0,
        });
        message.success('上传成功，开始处理...');
      } else {
        setIsLoading(false);
        setError(response.message || '上传失败');
        message.error(response.message || '上传失败');
      }
    } catch (err: any) {
      setIsLoading(false);
      const errorMsg = err.response?.data?.detail || '上传失败，请重试';
      setError(errorMsg);
      message.error(errorMsg);
    }
  }, [targetLanguage, sourceLanguage, setIsLoading, setError, setOriginalImage, setCurrentTask]);

  const handleReset = () => {
    setCurrentTask(null);
    setOriginalImage(null);
    setTranslatedImage(null);
    setError(null);
  };

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Header style={{ background: '#fff', boxShadow: '0 2px 8px rgba(0,0,0,0.1)' }}>
        <Space align="center">
          <TranslationOutlined style={{ fontSize: 28, color: '#1890ff' }} />
          <Title level={3} style={{ margin: 0, color: '#1890ff' }}>
            图片翻译工具
          </Title>
        </Space>
      </Header>

      <Content style={{ padding: '24px', maxWidth: 1200, margin: '0 auto', width: '100%' }}>
        <Space direction="vertical" style={{ width: '100%' }} size="large">
          {/* 语言选择器 */}
          <LanguageSelector
            languages={languages}
            sourceLanguage={sourceLanguage}
            targetLanguage={targetLanguage}
            onSourceChange={setSourceLanguage}
            onTargetChange={setTargetLanguage}
            disabled={isLoading}
          />

          {/* 错误提示 */}
          {error && (
            <Alert
              message="错误"
              description={error}
              type="error"
              closable
              onClose={() => setError(null)}
            />
          )}

          {/* 上传区域 */}
          {!isLoading && !translatedImage && (
            <UploadArea onUpload={handleUpload} disabled={isLoading} />
          )}

          {/* 进度条 */}
          {isLoading && currentTask && (
            <ProgressBar
              status={currentTask.status}
              progress={currentTask.progress}
              message={currentTask.status === 'processing' ? '正在处理...' : undefined}
            />
          )}

          {/* 图片预览 */}
          {(originalImage || translatedImage) && (
            <ImagePreview
              originalImage={originalImage}
              translatedImage={translatedImage}
              showComparison={true}
            />
          )}

          {/* 重置按钮 */}
          {translatedImage && (
            <Button type="primary" onClick={handleReset} block>
              翻译新图片
            </Button>
          )}
        </Space>
      </Content>
    </Layout>
  );
};

export default HomePage;
