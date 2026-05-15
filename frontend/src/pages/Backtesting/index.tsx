import { useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import {
  Row, Col, Card, Select, DatePicker, InputNumber, Input, Button,
  Statistic, Table, Typography, Spin, Space, message,
} from 'antd';
import { BarChartOutlined, CalculatorOutlined } from '@ant-design/icons';
import ReactECharts from 'echarts-for-react';
import dayjs from 'dayjs';
import { factorsApi } from '../../api/factors';
import { backtestApi } from '../../api/backtest';
import type { FactorCatalog, BacktestResult } from '../../types';

const { RangePicker } = DatePicker;

export default function Backtesting() {
  const [factorCode, setFactorCode] = useState<string>();
  const [dateRange, setDateRange] = useState<[dayjs.Dayjs, dayjs.Dayjs]>([
    dayjs().subtract(180, 'day'),
    dayjs(),
  ]);
  const [nQuantiles, setNQuantiles] = useState(5);
  const [btName, setBtName] = useState('');

  const { data: factorsResp } = useQuery({
    queryKey: ['factors-backtest'],
    queryFn: () => factorsApi.list({ page: 1, page_size: 100 }),
  });
  const factors = ((factorsResp as any)?.data?.items || []) as FactorCatalog[];

  const computeMut = useMutation({
    mutationFn: () => factorsApi.compute({
      factor_code: factorCode!,
      start_date: dateRange[0].format('YYYY-MM-DD'),
      end_date: dateRange[1].format('YYYY-MM-DD'),
    }),
    onSuccess: (res: any) => {
      message.success(`Computed ${res?.data?.rows_computed ?? 0} values`);
    },
    onError: (err: any) => {
      const detail = err?.response?.data?.detail || err?.message || 'Unknown error';
      message.error(typeof detail === 'string' ? detail : JSON.stringify(detail));
    },
  });

  const runMut = useMutation({
    mutationFn: () => backtestApi.run({
      name: btName || `${factorCode}_backtest`,
      factor_code: factorCode!,
      strategy_type: 'factor_quantile',
      start_date: dateRange[0].format('YYYY-MM-DD'),
      end_date: dateRange[1].format('YYYY-MM-DD'),
      n_quantiles: nQuantiles,
      top_quantile: 1,
      rebalance_freq: 'daily',
    }),
    onSuccess: (res: any) => {
      const jobId = res?.data?.job_id;
      message.info(`Backtest started, job ID: ${jobId}`);
      setCurrentJobId(jobId);
    },
    onError: (err: any) => {
      const detail = err?.response?.data?.detail || err?.message || 'Unknown error';
      message.error(typeof detail === 'string' ? detail : JSON.stringify(detail));
    },
  });

  const [currentJobId, setCurrentJobId] = useState<number | null>(null);

  const { data: btResult, refetch: refetchBt } = useQuery({
    queryKey: ['backtest-result', currentJobId],
    queryFn: () => backtestApi.get(currentJobId!),
    enabled: !!currentJobId,
    refetchInterval: (query) => {
      const status = (query.state.data as any)?.data?.status;
      return status === 'pending' || status === 'running' ? 3000 : false;
    },
  });

  const { data: btList } = useQuery({
    queryKey: ['backtest-list'],
    queryFn: backtestApi.list,
  });

  const result = (btResult as any)?.data as BacktestResult | undefined;
  const equityCurve = result?.equity_curve || [];
  const btJobs = ((btList as any)?.data || []) as BacktestResult[];

  const equityOption = {
    tooltip: { trigger: 'axis' as const },
    grid: { left: '3%', right: '4%', bottom: '3%', top: '10%', containLabel: true },
    xAxis: {
      type: 'category' as const,
      data: equityCurve.map((p: any) => p.date),
      axisLabel: { fontSize: 10 },
    },
    yAxis: [
      {
        type: 'value' as const,
        name: 'Equity',
        axisLabel: { fontSize: 10 },
      },
      {
        type: 'value' as const,
        name: 'Drawdown %',
        axisLabel: { fontSize: 10, formatter: '{value}%' },
      },
    ],
    series: [
      {
        name: 'Equity Curve',
        type: 'line',
        data: equityCurve.map((p: any) => p.value),
        smooth: true,
        showSymbol: false,
        areaStyle: { opacity: 0.1 },
      },
      {
        name: 'Drawdown',
        type: 'line',
        yAxisIndex: 1,
        data: equityCurve.map((p: any) => ((p.drawdown || 0) * 100).toFixed(2)),
        smooth: true,
        showSymbol: false,
        lineStyle: { color: '#ff4d4f', type: 'dashed' },
      },
    ],
  };

  const historyColumns = [
    { title: 'ID', dataIndex: 'id', width: 50 },
    { title: 'Name', dataIndex: 'name' },
    {
      title: 'Status', dataIndex: 'status',
      render: (v: string) => (
        <span style={{ color: v === 'completed' ? '#52c41a' : v === 'failed' ? '#ff4d4f' : '#faad14' }}>
          {v}
        </span>
      ),
    },
    { title: 'Total Return', dataIndex: 'total_return', render: (v?: number) => v ? `${(v * 100).toFixed(2)}%` : '-' },
    { title: 'Annual Return', dataIndex: 'annual_return', render: (v?: number) => v ? `${(v * 100).toFixed(2)}%` : '-' },
    { title: 'Sharpe', dataIndex: 'sharpe_ratio', render: (v?: number) => v?.toFixed(2) || '-' },
    { title: 'Max DD', dataIndex: 'max_drawdown', render: (v?: number) => v ? `${(v * 100).toFixed(2)}%` : '-' },
  ];

  return (
    <div>
      <Card title="Strategy Configuration" style={{ marginBottom: 16 }}>
        <Row gutter={[16, 16]} align="middle">
          <Col xs={24} sm={12} lg={6}>
            <Typography.Text strong>Factor</Typography.Text>
            <Select
              placeholder="Select factor"
              style={{ width: '100%', marginTop: 4 }}
              value={factorCode}
              onChange={setFactorCode}
              options={factors.map((f) => ({ value: f.code, label: f.name }))}
              showSearch
              filterOption={(input, option) =>
                (option?.label as string)?.toLowerCase().includes(input.toLowerCase())
              }
            />
          </Col>
          <Col xs={24} sm={12} lg={6}>
            <Typography.Text strong>Backtest Period</Typography.Text>
            <br />
            <RangePicker
              value={dateRange}
              onChange={(dates) => dates && setDateRange(dates as [dayjs.Dayjs, dayjs.Dayjs])}
              style={{ marginTop: 4 }}
            />
          </Col>
          <Col xs={12} sm={8} lg={3}>
            <Typography.Text strong>Quantiles</Typography.Text>
            <InputNumber
              min={2} max={10}
              value={nQuantiles}
              onChange={(v) => setNQuantiles(v || 5)}
              style={{ width: '100%', marginTop: 4 }}
            />
          </Col>
          <Col xs={12} sm={8} lg={4}>
            <Typography.Text strong>Strategy Name</Typography.Text>
            <Input
              placeholder="My Strategy"
              value={btName}
              onChange={(e) => setBtName(e.target.value)}
              style={{ marginTop: 4 }}
            />
          </Col>
          <Col xs={24} sm={8} lg={5}>
            <Space style={{ marginTop: 24 }}>
              <Button
                icon={<CalculatorOutlined />}
                loading={computeMut.isPending}
                onClick={() => computeMut.mutate()}
                disabled={!factorCode}
              >
                Compute
              </Button>
              <Button
                type="primary"
                icon={<BarChartOutlined />}
                loading={runMut.isPending}
                onClick={() => runMut.mutate()}
                disabled={!factorCode}
              >
                Run Backtest
              </Button>
            </Space>
          </Col>
        </Row>
      </Card>

      {result && (
        <>
          <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
            <Col xs={12} sm={8} lg={4}>
              <Card><Statistic title="Total Return" value={result.total_return ? `${(result.total_return * 100).toFixed(2)}%` : '-'} /></Card>
            </Col>
            <Col xs={12} sm={8} lg={4}>
              <Card><Statistic title="Annual Return" value={result.annual_return ? `${(result.annual_return * 100).toFixed(2)}%` : '-'} /></Card>
            </Col>
            <Col xs={12} sm={8} lg={4}>
              <Card><Statistic title="Volatility" value={result.volatility ? `${(result.volatility * 100).toFixed(2)}%` : '-'} /></Card>
            </Col>
            <Col xs={12} sm={8} lg={4}>
              <Card><Statistic title="Sharpe Ratio" value={result.sharpe_ratio?.toFixed(2) || '-'} /></Card>
            </Col>
            <Col xs={12} sm={8} lg={4}>
              <Card><Statistic title="Max Drawdown" value={result.max_drawdown ? `${(result.max_drawdown * 100).toFixed(2)}%` : '-'} /></Card>
            </Col>
            <Col xs={12} sm={8} lg={4}>
              <Card><Statistic title="Win Rate" value={result.win_rate ? `${(result.win_rate * 100).toFixed(1)}%` : '-'} /></Card>
            </Col>
          </Row>

          <Card title="Equity Curve" style={{ marginBottom: 16 }}>
            {equityCurve.length > 0 ? (
              <ReactECharts option={equityOption} style={{ height: 400 }} />
            ) : (
              <Spin />
            )}
          </Card>
        </>
      )}

      <Card title="Backtest History">
        <Table
          dataSource={btJobs}
          columns={historyColumns}
          rowKey="id"
          size="small"
          onRow={(record) => ({
            onClick: () => setCurrentJobId(record.id),
            style: { cursor: 'pointer' },
          })}
        />
      </Card>
    </div>
  );
}
