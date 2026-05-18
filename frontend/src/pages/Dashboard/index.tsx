import { useQuery } from '@tanstack/react-query';
import { Row, Col, Card, Statistic, Spin, Typography, Result, Button } from 'antd';
import {
  RiseOutlined,
  StockOutlined,
  DollarOutlined,
  CalendarOutlined,
  ReloadOutlined,
} from '@ant-design/icons';
import ReactECharts from 'echarts-for-react';
import { dashboardApi } from '../../api/dashboard';
import { factorsApi } from '../../api/factors';

export default function Dashboard() {
  const { data: overview, isLoading: loadingOverview, isError, refetch } = useQuery({
    queryKey: ['dashboard-overview'],
    queryFn: dashboardApi.overview,
  });

  const { data: indexPerf } = useQuery({
    queryKey: ['dashboard-index'],
    queryFn: dashboardApi.indexPerformance,
  });

  const { data: popularFactors } = useQuery({
    queryKey: ['factors-popular'],
    queryFn: factorsApi.popular,
  });

  const ov = (overview as any)?.data || {};

  const indexData = ((indexPerf as any)?.data || []).map(
    (d: { date: string; avg_close: number; total_amount: number; stock_count: number }) => ({
      date: d.date,
      value: d.avg_close,
      amount: d.total_amount,
    })
  );

  const lineOption = {
    tooltip: { trigger: 'axis' as const },
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
    xAxis: {
      type: 'category' as const,
      data: indexData.map((d: { date: string }) => d.date),
      axisLabel: { rotate: 45, fontSize: 10 },
    },
    yAxis: {
      type: 'value' as const,
      name: 'Avg Close',
      axisLabel: { fontSize: 10 },
    },
    series: [
      {
        name: 'Average Close',
        type: 'line',
        data: indexData.map((d: { value: number }) => d.value),
        smooth: true,
        showSymbol: false,
        areaStyle: { opacity: 0.08, color: '#1677ff' },
        lineStyle: { color: '#1677ff', width: 2 },
      },
    ],
  };

  const factorData = ((popularFactors as any)?.data || []).map(
    (f: { name: string; code: string; popularity: number }) => ({
      name: f.name,
      value: f.popularity,
    })
  );

  const barOption = {
    tooltip: { trigger: 'axis' as const },
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
    xAxis: {
      type: 'category' as const,
      data: factorData.map((d: { name: string }) => d.name),
      axisLabel: { rotate: 30, fontSize: 10 },
    },
    yAxis: { type: 'value' as const, name: 'Popularity' },
    series: [
      {
        type: 'bar',
        data: factorData.map((d: { value: number }) => d.value || 10),
        itemStyle: {
          color: '#1677ff',
          borderRadius: [4, 4, 0, 0],
        },
      },
    ],
  };

  if (isError) {
    return (
      <Result
        status="warning"
        title="后端服务未连接"
        subTitle="Dashboard 数据需要后端 API 支持，请确认后端已启动"
        extra={
          <Button type="primary" icon={<ReloadOutlined />} onClick={() => refetch()}>
            重试
          </Button>
        }
      />
    );
  }

  return (
    <Spin spinning={loadingOverview}>
      <Row gutter={[16, 16]}>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Total Stocks"
              value={ov.total_stocks || 0}
              prefix={<StockOutlined />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Latest Trade Date"
              value={ov.latest_trade_date || '-'}
              prefix={<CalendarOutlined />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Avg Close Price"
              value={ov.avg_close ? Number(ov.avg_close).toFixed(2) : 0}
              prefix={<DollarOutlined />}
              suffix={ov.week_change_pct != null ? (
                <span style={{ fontSize: 14, color: ov.week_change_pct >= 0 ? '#3f8600' : '#cf1322' }}>
                  {ov.week_change_pct >= 0 ? '+' : ''}{ov.week_change_pct}%
                </span>
              ) : undefined}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Total Turnover (¥)"
              value={ov.total_amount ? (Number(ov.total_amount) / 1e8).toFixed(2) + '亿' : 0}
              prefix={<RiseOutlined />}
            />
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col xs={24} lg={14}>
          <Card title="Market Trend (60-Day Avg Close)">
            {indexData.length > 0 ? (
              <ReactECharts option={lineOption} style={{ height: 360 }} />
            ) : (
              <Typography.Text type="secondary">
                Download market data first in Data Center
              </Typography.Text>
            )}
          </Card>
        </Col>
        <Col xs={24} lg={10}>
          <Card title="Factor Catalog">
            {factorData.length > 0 ? (
              <ReactECharts option={barOption} style={{ height: 360 }} />
            ) : (
              <div style={{ padding: 24, textAlign: 'center' }}>
                <Typography.Text type="secondary">
                  70 factors available in 7 categories. Visit Factor Library to browse and compute them.
                </Typography.Text>
              </div>
            )}
          </Card>
        </Col>
      </Row>
    </Spin>
  );
}
