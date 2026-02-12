import React from 'react';
import { Progress, Card, Typography, Space } from 'antd';

const { Text } = Typography;

interface ProgressBarProps {
  status: string;
  progress: number;
  message?: string;
}

const ProgressBar: React.FC<ProgressBarProps> = ({ status, progress, message }) => {
  const getStatusText = () => {
    switch (status) {
      case 'pending':
        return '等待处理...';
      case 'processing':
        return message || '正在处理...';
      case 'completed':
        return '处理完成!';
      case 'failed':
        return '处理失败';
      default:
        return '未知状态';
    }
  };

  const getStatusColor = () => {
    switch (status) {
      case 'completed':
        return '#52c41a';
      case 'failed':
        return '#ff4d4f';
      default:
        return '#1890ff';
    }
  };

  return (
    <Card>
      <Space direction="vertical" style={{ width: '100%' }}>
        <Progress
          percent={progress}
          status={status === 'failed' ? 'exception' : 'active'}
          strokeColor={getStatusColor()}
        />
        <Text type="secondary" style={{ textAlign: 'center', display: 'block' }}>
          {getStatusText()}
        </Text>
      </Space>
    </Card>
  );
};

export default ProgressBar;
