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
import { useTranslation } from '../../locales';

export default function Dashboard() {
  const { t } = useTranslation();

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
        title={t.backendNotConnected}
        subTitle={t.backendNotConnectedHint}
        extra={
          <Button type="primary" icon={<ReloadOutlined />} onClick={() => refetch()}>
            {t.retry}
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
              title={t.totalStocks}
              value={ov.total_stocks || 0}
              prefix={<StockOutlined />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title={t.latestTradeDate}
              value={ov.latest_trade_date || '-'}
              prefix={<CalendarOutlined />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title={t.avgClosePrice}
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
              title={t.totalTurnover}
              value={ov.total_amount ? (Number(ov.total_amount) / 1e8).toFixed(2) + t.yi : 0}
              prefix={<RiseOutlined />}
            />
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col xs={24} lg={14}>
          <Card title={t.marketTrend}>
            {indexData.length > 0 ? (
              <ReactECharts option={lineOption} style={{ height: 360 }} />
            ) : (
              <Typography.Text type="secondary">
                {t.downloadMarketData}
              </Typography.Text>
            )}
          </Card>
        </Col>
        <Col xs={24} lg={10}>
          <Card title={t.factorCatalog}>
            {factorData.length > 0 ? (
              <ReactECharts option={barOption} style={{ height: 360 }} />
            ) : (
              <div style={{ padding: 24, textAlign: 'center' }}>
                <Typography.Text type="secondary">
                  {t.factorCatalogHint}
                </Typography.Text>
              </div>
            )}
          </Card>
        </Col>
      </Row>
    </Spin>
  );
}
