import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { ConfigProvider, App as AntApp, theme } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import enUS from 'antd/locale/en_US';
import dayjs from 'dayjs';
import 'dayjs/locale/zh-cn';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useAppSettings } from './hooks/useAppSettings';
import ErrorBoundary from './components/common/ErrorBoundary';
import AppLayout from './components/Layout/AppLayout';
import Dashboard from './pages/Dashboard';
import FactorLibrary from './pages/FactorLibrary';
import FactorDetail from './pages/FactorLibrary/FactorDetail';
import FactorAnalysis from './pages/FactorAnalysis';
import StockScreener from './pages/StockScreener';
import Backtesting from './pages/Backtesting';
import DataCenter from './pages/DataCenter';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      staleTime: 5 * 60 * 1000,
      refetchOnWindowFocus: false,
    },
  },
});

const antdLocales = {
  'zh-CN': zhCN,
  'en-US': enUS,
};

function ThemedApp() {
  const { locale, themeMode } = useAppSettings();

  dayjs.locale(locale === 'zh-CN' ? 'zh-cn' : 'en');

  return (
    <ConfigProvider
      key={locale}
      locale={antdLocales[locale]}
      theme={{
        algorithm: themeMode === 'dark' ? theme.darkAlgorithm : theme.defaultAlgorithm,
        token: {
          colorPrimary: '#1677ff',
          borderRadius: 8,
        },
      }}
    >
      <AntApp>
        <ErrorBoundary>
          <BrowserRouter>
            <Routes>
              <Route path="/" element={<AppLayout />}>
                <Route index element={<Dashboard />} />
                <Route path="factors" element={<FactorLibrary />} />
                <Route path="factors/:code" element={<FactorDetail />} />
                <Route path="analysis" element={<FactorAnalysis />} />
                <Route path="screener" element={<StockScreener />} />
                <Route path="backtest" element={<Backtesting />} />
                <Route path="data" element={<DataCenter />} />
              </Route>
            </Routes>
          </BrowserRouter>
        </ErrorBoundary>
      </AntApp>
    </ConfigProvider>
  );
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemedApp />
    </QueryClientProvider>
  );
}
