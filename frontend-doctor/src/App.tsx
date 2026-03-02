/**
 * 主应用组件
 */
import React, { useEffect, useState } from 'react';
import { BrowserRouter, Routes, Route, Navigate, useNavigate, useLocation } from 'react-router-dom';
import { ConfigProvider, Layout, Menu, Badge, Tooltip, Space, Tag } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import {
  UserOutlined,
  FileImageOutlined,
  CalendarOutlined,
  DashboardOutlined,
  RobotOutlined,
} from '@ant-design/icons';
import PatientList from './pages/PatientList';
import PatientDetail from './pages/PatientDetail';
import { medgemmaAPI } from './services/api';
import './App.css';

const { Header, Sider, Content } = Layout;

const MENU_ROUTE_MAP: Record<string, string> = {
  patients: '/patients',
  images: '/patients',
  followup: '/patients',
  dashboard: '/patients',
};

const SideMenu: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();

  const selectedKey = location.pathname.startsWith('/patients') ? 'patients' : 'patients';

  const menuItems = [
    { key: 'patients', icon: <UserOutlined />, label: '患者管理' },
    { key: 'images', icon: <FileImageOutlined />, label: '影像管理' },
    { key: 'followup', icon: <CalendarOutlined />, label: '随访管理' },
    { key: 'dashboard', icon: <DashboardOutlined />, label: '数据看板' },
  ];

  return (
    <Menu
      mode="inline"
      selectedKeys={[selectedKey]}
      style={{ height: '100%', borderRight: 0 }}
      items={menuItems}
      onClick={({ key }) => {
        const path = MENU_ROUTE_MAP[key];
        if (path) navigate(path);
      }}
    />
  );
};

const MedGemmaStatus: React.FC = () => {
  const [status, setStatus] = useState<'loading' | 'healthy' | 'offline'>('loading');
  const [gpu, setGpu] = useState('');

  useEffect(() => {
    let cancelled = false;
    const check = async () => {
      try {
        const res: any = await medgemmaAPI.health();
        if (cancelled) return;
        if (res?.success && res.data?.status === 'healthy') {
          setStatus('healthy');
          setGpu(res.data.gpu || '');
        } else {
          setStatus('offline');
        }
      } catch {
        if (!cancelled) setStatus('offline');
      }
    };
    check();
    const timer = setInterval(check, 60_000);
    return () => { cancelled = true; clearInterval(timer); };
  }, []);

  const dotColor = status === 'healthy' ? '#52c41a' : status === 'offline' ? '#ff4d4f' : '#faad14';
  const text = status === 'healthy'
    ? `MedGemma 在线${gpu ? ` (${gpu})` : ''}`
    : status === 'offline'
      ? 'MedGemma 离线'
      : '检测中...';

  return (
    <Tooltip title={text}>
      <Space size={4} style={{ cursor: 'default' }}>
        <Badge color={dotColor} />
        <RobotOutlined style={{ color: 'rgba(255,255,255,0.85)', fontSize: 16 }} />
        <span style={{ color: 'rgba(255,255,255,0.65)', fontSize: 12 }}>
          {status === 'healthy' ? 'AI 就绪' : status === 'offline' ? 'AI 离线' : '...'}
        </span>
      </Space>
    </Tooltip>
  );
};

const AppLayout: React.FC = () => (
  <Layout style={{ minHeight: '100vh' }}>
    <Header
      style={{
        background: '#001529',
        padding: '0 24px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
      }}
    >
      <h2 style={{ color: 'white', margin: 0, fontSize: 18 }}>
        青海子宫内膜癌智能诊疗平台
      </h2>
      <MedGemmaStatus />
    </Header>

    <Layout>
      <Sider width={200} style={{ background: '#fff' }}>
        <SideMenu />
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
);

const App: React.FC = () => (
  <ConfigProvider locale={zhCN}>
    <BrowserRouter>
      <AppLayout />
    </BrowserRouter>
  </ConfigProvider>
);

export default App;
