import React from 'react';
import { Image, Card, Typography, Row, Col } from 'antd';

const { Text, Title } = Typography;

interface ImagePreviewProps {
  originalImage: string | null;
  translatedImage: string | null;
  showComparison?: boolean;
}

const ImagePreview: React.FC<ImagePreviewProps> = ({
  originalImage,
  translatedImage,
  showComparison = true,
}) => {
  if (!originalImage && !translatedImage) {
    return null;
  }

  return (
    <Row gutter={[16, 16]}>
      {showComparison && originalImage && (
        <Col span={translatedImage ? 12 : 24}>
          <Card title="原图" size="small">
            <Image
              src={originalImage}
              alt="原图"
              style={{ maxWidth: '100%', maxHeight: '500px', objectFit: 'contain' }}
              preview={{ src: originalImage }}
            />
          </Card>
        </Col>
      )}
      {translatedImage && (
        <Col span={originalImage && showComparison ? 12 : 24}>
          <Card 
            title="翻译结果" 
            size="small"
            extra={
              <a href={translatedImage} download="translated_image.png">
                下载
              </a>
            }
          >
            <Image
              src={translatedImage}
              alt="翻译结果"
              style={{ maxWidth: '100%', maxHeight: '500px', objectFit: 'contain' }}
              preview={{ src: translatedImage }}
            />
          </Card>
        </Col>
      )}
    </Row>
  );
};

export default ImagePreview;
