/**
 * 主应用组件
 */
import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { ConfigProvider, Layout, Menu } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import {
  UserOutlined,
  FileImageOutlined,
  CalendarOutlined,
  DashboardOutlined,
} from '@ant-design/icons';
import PatientList from './pages/PatientList';
import PatientDetail from './pages/PatientDetail';
import './App.css';

const { Header, Sider, Content } = Layout;

const App: React.FC = () => {
  const menuItems = [
    {
      key: 'patients',
      icon: <UserOutlined />,
      label: '患者管理',
    },
    {
      key: 'images',
      icon: <FileImageOutlined />,
      label: '影像管理',
    },
    {
      key: 'followup',
      icon: <CalendarOutlined />,
      label: '随访管理',
    },
    {
      key: 'dashboard',
      icon: <DashboardOutlined />,
      label: '数据看板',
    },
  ];

  return (
    <ConfigProvider locale={zhCN}>
      <BrowserRouter>
        <Layout style={{ minHeight: '100vh' }}>
          <Header style={{ background: '#001529', color: 'white', padding: '0 24px' }}>
            <h2 style={{ color: 'white', margin: 0 }}>
              青海子宫内膜癌智能诊疗平台
            </h2>
          </Header>
          
          <Layout>
            <Sider width={200} style={{ background: '#fff' }}>
              <Menu
                mode="inline"
                defaultSelectedKeys={['patients']}
                style={{ height: '100%', borderRight: 0 }}
                items={menuItems}
              />
            </Sider>
            
            <Layout style={{ padding: '0 24px 24px' }}>
              <Content
                style={{
                  padding: 24,
                  margin: 0,
                  minHeight: 280,
                  background: '#f0f2f5',
                }}
              >
                <Routes>
                  <Route path="/" element={<Navigate to="/patients" replace />} />
                  <Route path="/patients" element={<PatientList />} />
                  <Route path="/patients/:id" element={<PatientDetail />} />
                  <Route path="*" element={<div>页面不存在</div>} />
                </Routes>
              </Content>
            </Layout>
          </Layout>
        </Layout>
      </BrowserRouter>
    </ConfigProvider>
  );
};

export default App;

