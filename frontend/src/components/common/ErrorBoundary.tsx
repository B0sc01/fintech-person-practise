import { Component, type ReactNode } from 'react';
import { Result, Button } from 'antd';
import zhCN from '../../locales/zh-CN';
import enUS from '../../locales/en-US';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

const translations: Record<string, typeof zhCN> = {
  'zh-CN': zhCN,
  'en-US': enUS,
};

function getLocale(): typeof zhCN {
  try {
    const stored = localStorage.getItem('fintech-locale');
    const locale = stored ? JSON.parse(stored) : 'zh-CN';
    return translations[locale] || zhCN;
  } catch {
    return zhCN;
  }
}

export default class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  render() {
    if (this.state.hasError) {
      const t = getLocale();
      return (
        <div style={{ padding: 100, textAlign: 'center' }}>
          <Result
            status="error"
            title={t.pageRenderError}
            subTitle={
              <div>
                <p>{t.runtimeError}</p>
                <pre style={{
                  textAlign: 'left', maxWidth: 600, margin: '16px auto',
                  padding: 16, background: '#1a1a2e', color: '#e43f5a',
                  borderRadius: 8, fontSize: 13, overflow: 'auto',
                  whiteSpace: 'pre-wrap', wordBreak: 'break-all',
                }}>
                  {this.state.error?.message || 'Unknown Error'}
                  {'\n\n'}
                  {this.state.error?.stack || ''}
                </pre>
              </div>
            }
            extra={
              <Button type="primary" onClick={() => window.location.reload()}>
                {t.refreshPage}
              </Button>
            }
          />
        </div>
      );
    }
    return this.props.children;
  }
}
