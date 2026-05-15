import { useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { Row, Col, Card, Select, DatePicker, Button, Typography, Spin, Empty, message } from 'antd';
import { FundOutlined, CalculatorOutlined } from '@ant-design/icons';
import ReactECharts from 'echarts-for-react';
import dayjs from 'dayjs';
import { analysisApi } from '../../api/analysis';
import { factorsApi } from '../../api/factors';
import type { FactorCatalog } from '../../types';

const { RangePicker } = DatePicker;

export default function FactorAnalysis() {
  const [selectedFactors, setSelectedFactors] = useState<string[]>([]);
  const [dateRange, setDateRange] = useState<[dayjs.Dayjs, dayjs.Dayjs]>([
    dayjs().subtract(60, 'day'),
    dayjs(),
  ]);

  const { data: factorsResp } = useQuery({
    queryKey: ['factors-all'],
    queryFn: () => factorsApi.list({ page: 1, page_size: 100 }),
  });
  const factors = ((factorsResp as any)?.data?.items || []) as FactorCatalog[];

  const { data: icResp, isLoading: loadingIC, refetch: refetchIC } = useQuery({
    queryKey: ['analysis-ic', selectedFactors, dateRange],
    queryFn: () => analysisApi.ic({
      factor_codes: selectedFactors,
      start_date: dateRange[0].format('YYYY-MM-DD'),
      end_date: dateRange[1].format('YYYY-MM-DD'),
      forward_period: 1,
    }),
    enabled: selectedFactors.length > 0,
  });

  const { data: corrResp, isLoading: loadingCorr, refetch: refetchCorr } = useQuery({
    queryKey: ['analysis-correlation', selectedFactors, dateRange],
    queryFn: () => analysisApi.correlation({
      factor_codes: selectedFactors,
      start_date: dateRange[0].format('YYYY-MM-DD'),
      end_date: dateRange[1].format('YYYY-MM-DD'),
    }),
    enabled: selectedFactors.length >= 2,
  });

  const icResults = (icResp as any)?.data || [];
  const corrData = (corrResp as any)?.data;

  const computeMut = useMutation({
    mutationFn: async () => {
      for (const fc of selectedFactors) {
        await factorsApi.compute({
          factor_code: fc,
          start_date: dateRange[0].format('YYYY-MM-DD'),
          end_date: dateRange[1].format('YYYY-MM-DD'),
        });
      }
    },
    onSuccess: () => {
      message.success('Factors computed, running analysis...');
      refetchIC();
      refetchCorr();
    },
    onError: (err: any) => {
      const detail = err?.response?.data?.detail || err?.message || 'Unknown error';
      message.error(typeof detail === 'string' ? detail : JSON.stringify(detail));
    },
  });

  const icOption = {
    tooltip: { trigger: 'axis' as const },
    legend: { data: icResults.map((r: any) => r.factor_code), top: 0 },
    grid: { left: '3%', right: '4%', bottom: '3%', top: 40, containLabel: true },
    xAxis: { type: 'category' as const, data: icResults[0]?.ic_series?.map((p: any) => p.trade_date) || [], axisLabel: { fontSize: 10 } },
    yAxis: { type: 'value' as const, name: 'IC (Pearson)' },
    series: icResults.map((r: any) => ({
      name: r.factor_code,
      type: 'line' as const,
      data: r.ic_series?.map((p: any) => p.ic_pearson) || [],
      smooth: true,
      showSymbol: false,
    })),
  };

  const heatmapOption = corrData?.factors ? {
    tooltip: {},
    grid: { left: '10%', right: '5%', bottom: '5%', top: '5%' },
    xAxis: {
      type: 'category' as const,
      data: corrData.factors,
      axisLabel: { rotate: 45, fontSize: 10 },
      position: 'top' as const,
    },
    yAxis: {
      type: 'category' as const,
      data: corrData.factors,
      axisLabel: { fontSize: 10 },
      inverse: true,
    },
    visualMap: {
      min: -1,
      max: 1,
      inRange: { color: ['#313695', '#4575b4', '#74add1', '#abd9e9', '#fee090', '#fdae61', '#f46d43', '#d73027', '#a50026'] },
      calculable: true,
      orient: 'horizontal' as const,
      left: 'center',
      bottom: 0,
    },
    series: [{
      type: 'heatmap',
      data: corrData.factors.flatMap((f1: string, i: number) =>
        corrData.factors.map((f2: string, j: number) => [j, i, corrData.matrix[i]?.[j] ?? 0])
      ),
      label: { show: true, fontSize: 11 },
      emphasis: { itemStyle: { shadowBlur: 10, shadowColor: 'rgba(0,0,0,0.5)' } },
    }],
  } : null;

  return (
    <Spin spinning={loadingIC || loadingCorr}>
      <Row gutter={[16, 16]}>
        <Col xs={24}>
          <Card>
            <Row gutter={16} align="middle">
              <Col flex="auto">
                <Select
                  mode="multiple"
                  placeholder="Select factors to analyze"
                  style={{ width: '100%' }}
                  value={selectedFactors}
                  onChange={setSelectedFactors}
                  options={factors.map((f) => ({
                    value: f.code,
                    label: `${f.name} (${f.category})`,
                  }))}
                  maxTagCount={5}
                />
              </Col>
              <Col>
                <RangePicker
                  value={dateRange}
                  onChange={(dates) => dates && setDateRange(dates as [dayjs.Dayjs, dayjs.Dayjs])}
                />
              </Col>
              <Col>
                <Button
                  icon={<CalculatorOutlined />}
                  onClick={() => computeMut.mutate()}
                  disabled={selectedFactors.length === 0}
                  loading={computeMut.isPending}
                >
                  Compute
                </Button>
              </Col>
              <Col>
                <Button type="primary" icon={<FundOutlined />}
                  onClick={() => { refetchIC(); refetchCorr(); }}
                  disabled={selectedFactors.length === 0}
                >
                  Analyze
                </Button>
              </Col>
            </Row>
          </Card>
        </Col>
      </Row>

      {selectedFactors.length === 0 ? (
        <Empty style={{ marginTop: 48 }} description="Select factors above, click Compute, then Analyze" />
      ) : (
        <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
          <Col xs={24}>
            <Card title="Factor IC Time Series (Pearson)">
              {icResults.length > 0 ? (
                <ReactECharts option={icOption} style={{ height: 400 }} />
              ) : (
                <Typography.Text type="secondary">Compute factors first, then analyze here</Typography.Text>
              )}
            </Card>
          </Col>

          {icResults.length > 0 && (
            <Col xs={24}>
              <Card title="IC Summary Statistics">
                <Row gutter={[16, 16]}>
                  {icResults.map((r: any) => (
                    <Col xs={24} sm={12} md={8} lg={6} key={r.factor_code}>
                      <Card size="small" title={r.factor_code}>
                        <div>IC Mean: <strong>{r.ic_mean?.toFixed(4)}</strong></div>
                        <div>IC Std: <strong>{r.ic_std?.toFixed(4)}</strong></div>
                        <div>IR: <strong>{r.ir?.toFixed(4)}</strong></div>
                        <div>IC &gt; 0 Ratio: <strong>{((r.ic_positive_ratio ?? 0) * 100).toFixed(1)}%</strong></div>
                        <div>t-stat: <strong>{r.t_stat?.toFixed(2)}</strong></div>
                      </Card>
                    </Col>
                  ))}
                </Row>
              </Card>
            </Col>
          )}

          {heatmapOption && (
            <Col xs={24}>
              <Card title="Factor Correlation Matrix">
                <ReactECharts option={heatmapOption} style={{ height: 400 + (corrData?.factors?.length || 5) * 30 }} />
              </Card>
            </Col>
          )}
        </Row>
      )}
    </Spin>
  );
}
