import React from 'react';
import { ConfigProvider } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import HomePage from './pages/HomePage';

function App() {
  return (
    <ConfigProvider locale={zhCN}>
      <HomePage />
    </ConfigProvider>
  );
}

export default App;
