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
import type { Locale } from '../../hooks/useAppSettings';

const { Sider, Content, Header } = Layout;

const menuLabels: Record<string, { zh: string; en: string }> = {
  '/': { zh: '仪表盘', en: 'Dashboard' },
  '/factors': { zh: '因子库', en: 'Factor Library' },
  '/analysis': { zh: '因子分析', en: 'Factor Analysis' },
  '/screener': { zh: '股票筛选', en: 'Stock Screener' },
  '/backtest': { zh: '策略回测', en: 'Backtesting' },
  '/data': { zh: '数据中心', en: 'Data Center' },
};

function useMenuItems(locale: Locale) {
  const isZh = locale === 'zh-CN';
  return [
    { key: '/', icon: <DashboardOutlined />, label: isZh ? '仪表盘' : 'Dashboard' },
    { key: '/factors', icon: <AppstoreOutlined />, label: isZh ? '因子库' : 'Factor Library' },
    { key: '/analysis', icon: <FundOutlined />, label: isZh ? '因子分析' : 'Factor Analysis' },
    { key: '/screener', icon: <SearchOutlined />, label: isZh ? '股票筛选' : 'Stock Screener' },
    { key: '/backtest', icon: <BarChartOutlined />, label: isZh ? '策略回测' : 'Backtesting' },
    { key: '/data', icon: <DatabaseOutlined />, label: isZh ? '数据中心' : 'Data Center' },
  ];
}

export default function AppLayout() {
  const [collapsed, setCollapsed] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();
  const { token: themeToken } = theme.useToken();
  const { locale, themeMode, setLocale, toggleTheme } = useAppSettings();

  const selectedKey = '/' + location.pathname.split('/')[1];
  const menuItems = useMenuItems(locale);
  const currentTitle = menuLabels[selectedKey]?.[locale === 'zh-CN' ? 'zh' : 'en'] || '';

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
