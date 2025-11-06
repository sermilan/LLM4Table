import React from 'react'
import { BrowserRouter as Router, Routes, Route, useNavigate } from 'react-router-dom'
import { Layout, Menu } from 'antd'
import {
  UploadOutlined,
  RobotOutlined,
  SettingOutlined,
  BarChartOutlined,
  DownloadOutlined
} from '@ant-design/icons'
import DataUpload from './components/DataUpload'
import ModelSelection from './components/ModelSelection'
import DataSynthesis from './components/DataSynthesis'
import QualityEvaluation from './components/QualityEvaluation'
import DataDownload from './components/DataDownload'
import './App.css'

const { Header, Content, Footer, Sider } = Layout

function AppMenu() {
  const navigate = useNavigate();
  
  const menuItems = [
    {
      key: '1',
      icon: <UploadOutlined />,
      label: '数据上传',
      path: '/'
    },
    {
      key: '2',
      icon: <RobotOutlined />,
      label: '模型选择',
      path: '/model'
    },
    {
      key: '3',
      icon: <SettingOutlined />,
      label: '数据合成',
      path: '/synthesis'
    },
    {
      key: '4',
      icon: <BarChartOutlined />,
      label: '质量评估',
      path: '/evaluation'
    },
    {
      key: '5',
      icon: <DownloadOutlined />,
      label: '数据下载',
      path: '/download'
    },
  ];
  
  const handleMenuClick = ({ key }) => {
    const item = menuItems.find(item => item.key === key);
    if (item && item.path) {
      navigate(item.path);
    }
  };

  return (
    <Menu
      theme="dark"
      mode="inline"
      defaultSelectedKeys={['1']}
      items={menuItems}
      onClick={handleMenuClick}
    />
  );
}

function App() {
  return (
    <Router>
      <Layout style={{ minHeight: '100vh' }}>
        <Sider
          breakpoint="lg"
          collapsedWidth="0"
          style={{ 
            position: 'fixed', 
            height: '100vh', 
            overflow: 'auto',
            zIndex: 100,
            left: 0,
            top: 0
          }}
        >
          <div style={{ 
            color: 'white', 
            textAlign: 'center', 
            fontSize: '18px', 
            fontWeight: 'bold', 
            padding: '16px 0', 
            background: '#001529', 
            margin: 0,
            height: '64px',
            lineHeight: '32px'
          }}>
            SDTable
          </div>
          <AppMenu />
        </Sider>
        <Layout 
          style={{ 
            marginLeft: 200,
            transition: 'margin-left 0.2s',
            minHeight: '100vh',
            display: 'flex',
            flexDirection: 'column'
          }}
        >
          <Header style={{ 
            padding: 0, 
            background: '#fff',
            height: '64px',
            lineHeight: '64px',
            boxShadow: '0 2px 8px rgba(0, 0, 0, 0.06)',
            flexShrink: 0
          }} />
          <Content style={{ 
            margin: '0', 
            padding: '0',
            flex: 1,
            overflow: 'auto'
          }}>
            <div
              style={{
                padding: '0 16px',
                minHeight: 'calc(100vh - 64px - 69px)',
                background: '#fff',
              }}
            >
              <Routes>
                <Route path="/" element={<DataUpload />} />
                <Route path="/model" element={<ModelSelection />} />
                <Route path="/synthesis" element={<DataSynthesis />} />
                <Route path="/evaluation" element={<QualityEvaluation />} />
                <Route path="/download" element={<DataDownload />} />
              </Routes>
            </div>
          </Content>
          <Footer style={{ 
            textAlign: 'center',
            flexShrink: 0
          }}>
            SDTable - 基于大语言模型的表数据合成系统 ©2025
          </Footer>
        </Layout>
      </Layout>
    </Router>
  )
}

export default App