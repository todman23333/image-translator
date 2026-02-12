function App() {
  return (
    <div style={{ padding: '20px', fontFamily: 'Arial' }}>
      <h1>🖼️ 图片翻译工具</h1>
      <p>服务运行正常！</p>
      <div style={{ marginTop: '20px' }}>
        <h2>使用说明：</h2>
        <ol>
          <li>选择源语言和目标语言</li>
          <li>上传图片（JPG、PNG、WebP，最大10MB）</li>
          <li>等待处理完成</li>
          <li>下载翻译后的图片</li>
        </ol>
      </div>
      <div style={{ marginTop: '20px', padding: '10px', background: '#f0f0f0' }}>
        <p>📍 后端API: http://localhost:8000</p>
        <p>📍 前端: http://localhost:3000</p>
        <p>📍 API文档: http://localhost:8000/docs</p>
      </div>
    </div>
  );
}

export default App;
