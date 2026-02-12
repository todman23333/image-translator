import React from 'react';
import { Select, Space } from 'antd';
import { Language } from '../types';

interface LanguageSelectorProps {
  languages: Language[];
  sourceLanguage: string;
  targetLanguage: string;
  onSourceChange: (value: string) => void;
  onTargetChange: (value: string) => void;
  disabled?: boolean;
}

const LanguageSelector: React.FC<LanguageSelectorProps> = ({
  languages,
  sourceLanguage,
  targetLanguage,
  onSourceChange,
  onTargetChange,
  disabled,
}) => {
  const sourceOptions = [
    { value: 'auto', label: '自动检测', native_name: 'Auto Detect' },
    ...languages,
  ];

  return (
    <Space direction="vertical" style={{ width: '100%' }}>
      <Space>
        <span>源语言：</span>
        <Select
          style={{ width: 150 }}
          value={sourceLanguage}
          onChange={onSourceChange}
          disabled={disabled}
          options={sourceOptions.map((lang) => ({
            value: lang.code,
            label: `${lang.native_name} (${lang.name})`,
          }))}
        />
      </Space>
      <Space>
        <span>目标语言：</span>
        <Select
          style={{ width: 150 }}
          value={targetLanguage}
          onChange={onTargetChange}
          disabled={disabled}
          options={languages.map((lang) => ({
            value: lang.code,
            label: `${lang.native_name} (${lang.name})`,
          }))}
        />
      </Space>
    </Space>
  );
};

export default LanguageSelector;
