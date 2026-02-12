import React, { useCallback } from 'react';
import { Upload, message } from 'antd';
import { InboxOutlined } from '@ant-design/icons';

const { Dragger } = Upload;

interface UploadAreaProps {
  onUpload: (file: File) => void;
  disabled?: boolean;
}

const UploadArea: React.FC<UploadAreaProps> = ({ onUpload, disabled }) => {
  const beforeUpload = useCallback((file: File) => {
    const isImage = file.type.startsWith('image/');
    if (!isImage) {
      message.error('只能上传图片文件!');
      return false;
    }
    
    const isLt10M = file.size / 1024 / 1024 < 10;
    if (!isLt10M) {
      message.error('图片必须小于10MB!');
      return false;
    }
    
    onUpload(file);
    return false; // 阻止自动上传
  }, [onUpload]);

  return (
    <Dragger
      beforeUpload={beforeUpload}
      showUploadList={false}
      disabled={disabled}
      style={{ padding: '40px 20px' }}
    >
      <p className="ant-upload-drag-icon">
        <InboxOutlined style={{ fontSize: 48, color: '#1890ff' }} />
      </p>
      <p className="ant-upload-text">点击或拖拽图片到此区域上传</p>
      <p className="ant-upload-hint">
        支持 JPG、PNG、WebP 格式，文件大小不超过 10MB
      </p>
    </Dragger>
  );
};

export default UploadArea;
