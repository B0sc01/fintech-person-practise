import { useState } from 'react';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import { Layout, Menu, Typography, theme, Button, Space } from 'antd';
import {
  DashboardOutlined,
  AppstoreOutlined,
  FundOutlined,
  SearchOutlined,
  BarChartOutlined,
  DatabaseOutlined,
  TranslationOutlined,
  SunOutlined,
  MoonOutlined,
} from '@ant-design/icons';
import { useAppSettings } from '../../hooks/useAppSettings';
import { useTranslation } from '../../locales';

const { Sider, Content, Header } = Layout;

export default function AppLayout() {
  const [collapsed, setCollapsed] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();
  const { token: themeToken } = theme.useToken();
  const { locale, themeMode, setLocale, toggleTheme } = useAppSettings();
  const { t } = useTranslation();

  const selectedKey = '/' + location.pathname.split('/')[1];

  const menuLabels: Record<string, string> = {
    '/': t.dashboard,
    '/factors': t.factorLibrary,
    '/analysis': t.factorAnalysis,
    '/screener': t.stockScreener,
    '/backtest': t.backtesting,
    '/data': t.dataCenter,
  };

  const menuItems = [
    { key: '/', icon: <DashboardOutlined />, label: t.dashboard },
    { key: '/factors', icon: <AppstoreOutlined />, label: t.factorLibrary },
    { key: '/analysis', icon: <FundOutlined />, label: t.factorAnalysis },
    { key: '/screener', icon: <SearchOutlined />, label: t.stockScreener },
    { key: '/backtest', icon: <BarChartOutlined />, label: t.backtesting },
    { key: '/data', icon: <DatabaseOutlined />, label: t.dataCenter },
  ];

  const currentTitle = menuLabels[selectedKey] || '';

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider
        collapsible
        collapsed={collapsed}
        onCollapse={setCollapsed}
        style={{ background: themeToken.colorBgContainer }}
        width={220}
      >
        <div
          style={{
            height: 64,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            borderBottom: `1px solid ${themeToken.colorBorderSecondary}`,
          }}
        >
          <Typography.Title level={4} style={{ margin: 0, color: themeToken.colorPrimary }}>
            {collapsed ? 'Q' : 'Fintech Quant'}
          </Typography.Title>
        </div>
        <Menu
          key={locale}
          mode="inline"
          selectedKeys={[selectedKey]}
          items={menuItems}
          onClick={({ key }) => navigate(key)}
          style={{ borderRight: 0, marginTop: 8 }}
        />
      </Sider>
      <Layout>
        <Header
          style={{
            padding: '0 24px',
            background: themeToken.colorBgContainer,
            borderBottom: `1px solid ${themeToken.colorBorderSecondary}`,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
          }}
        >
          <Typography.Title level={5} style={{ margin: 0 }}>
            {currentTitle}
          </Typography.Title>

          <Space size="small">
            <Button
              icon={<TranslationOutlined />}
              size="small"
              type="text"
              onClick={() => setLocale(locale === 'zh-CN' ? 'en-US' : 'zh-CN')}
            >
              {locale === 'zh-CN' ? '中文' : 'EN'}
            </Button>

            <Button
              icon={themeMode === 'light' ? <MoonOutlined /> : <SunOutlined />}
              size="small"
              type="text"
              onClick={toggleTheme}
              title={themeMode === 'light' ? 'Dark Mode' : 'Light Mode'}
            />
          </Space>
        </Header>
        <Content
          style={{
            margin: 24,
            padding: 24,
            background: themeToken.colorBgContainer,
            borderRadius: themeToken.borderRadiusLG,
            minHeight: 280,
            overflow: 'auto',
          }}
        >
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  );
}
