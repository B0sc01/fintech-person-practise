import { Component, type ReactNode } from 'react';
import { Result, Button } from 'antd';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
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
      return (
        <div style={{ padding: 100, textAlign: 'center' }}>
          <Result
            status="error"
            title="页面渲染错误"
            subTitle={
              <div>
                <p>前端代码发生运行时错误，请尝试刷新页面</p>
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
                刷新页面
              </Button>
            }
          />
        </div>
      );
    }
    return this.props.children;
  }
}
