import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation } from '@tanstack/react-query';
import {
  Card, Row, Col, Descriptions, Tag, Button, Typography, Spin, Table, theme, DatePicker, message,
} from 'antd';
import { ArrowLeftOutlined, CalculatorOutlined } from '@ant-design/icons';
import ReactECharts from 'echarts-for-react';
import dayjs from 'dayjs';
import { factorsApi } from '../../api/factors';
import MathFormula from '../../components/common/MathFormula';
import type { FactorDetail } from '../../types';

const CATEGORY_COLORS: Record<string, string> = {
  momentum: '#f50',
  value: '#2db7f5',
  quality: '#87d068',
  volatility: '#722ed1',
  technical: '#108ee9',
  size: '#eb2f96',
  sentiment: '#faad14',
};

export default function FactorDetailPage() {
  const { code } = useParams<{ code: string }>();
  const navigate = useNavigate();
  const { token: themeToken } = theme.useToken();
  const [dateRange, setDateRange] = useState<[dayjs.Dayjs, dayjs.Dayjs]>([
    dayjs().subtract(60, 'day'),
    dayjs(),
  ]);

  const { data, isLoading, refetch } = useQuery({
    queryKey: ['factor-detail', code],
    queryFn: () => factorsApi.detail(code!),
    enabled: !!code,
  });

  const computeMut = useMutation({
    mutationFn: () => factorsApi.compute({
      factor_code: code!,
      start_date: dateRange[0].format('YYYY-MM-DD'),
      end_date: dateRange[1].format('YYYY-MM-DD'),
    }),
    onSuccess: (res: any) => {
      const count = res?.data?.rows_computed ?? 0;
      message.success(`Computed ${count} factor values for ${code}`);
      refetch();
    },
    onError: (err: any) => {
      const detail = err?.response?.data?.detail || err?.message || 'Unknown error';
      message.error(typeof detail === 'string' ? detail : JSON.stringify(detail));
    },
  });

  const factor = (data as any)?.data as FactorDetail | undefined;

  if (isLoading) return <Spin style={{ width: '100%', textAlign: 'center', padding: 100 }} />;
  if (!factor) return <Typography.Text>Factor not found</Typography.Text>;

  const recentValues = factor.recent_values || [];
  const valuesForChart = recentValues.slice(0, 50).reverse();

  const tsOption = {
    tooltip: { trigger: 'axis' as const },
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
    xAxis: {
      type: 'category' as const,
      data: valuesForChart.map((v: any) => v.trade_date),
      axisLabel: { rotate: 45, fontSize: 9 },
    },
    yAxis: { type: 'value' as const },
    series: [
      {
        name: 'Normalized Value',
        type: 'line',
        data: valuesForChart.map((v: any) => v.normalized_value),
        smooth: true,
        showSymbol: false,
        areaStyle: { opacity: 0.1 },
      },
    ],
  };

  const columns = [
    { title: 'Stock', dataIndex: 'ts_code', width: 120 },
    { title: 'Date', dataIndex: 'trade_date', width: 120 },
    {
      title: 'Raw Value', dataIndex: 'raw_value',
      render: (v: number) => v?.toFixed(4),
    },
    {
      title: 'Z-Score', dataIndex: 'normalized_value',
      render: (v: number) => v?.toFixed(4),
    },
  ];

  return (
    <div>
      <div style={{ marginBottom: 16, display: 'flex', gap: 12, alignItems: 'center', flexWrap: 'wrap' }}>
        <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/factors')}>
          Back to Library
        </Button>
        <DatePicker.RangePicker
          value={dateRange}
          onChange={(dates) => dates && setDateRange(dates as [dayjs.Dayjs, dayjs.Dayjs])}
          size="small"
        />
        <Button
          type="primary"
          icon={<CalculatorOutlined />}
          loading={computeMut.isPending}
          onClick={() => computeMut.mutate()}
        >
          Compute Values
        </Button>
      </div>

      <Card style={{ marginBottom: 16 }}>
        <Descriptions title={factor.name} column={{ xs: 1, sm: 2, lg: 3 }}>
          <Descriptions.Item label="Code">{factor.code}</Descriptions.Item>
          <Descriptions.Item label="Name (CN)">{factor.name_cn || '-'}</Descriptions.Item>
          <Descriptions.Item label="Category">
            <Tag color={CATEGORY_COLORS[factor.category]}>{factor.category}</Tag>
          </Descriptions.Item>
          <Descriptions.Item label="Sub Category">{factor.sub_category || '-'}</Descriptions.Item>
          <Descriptions.Item label="Polarity">
            <Tag color={factor.polarity === 'positive' ? 'green' : 'red'}>
              {factor.polarity}
            </Tag>
          </Descriptions.Item>
          <Descriptions.Item label="Source">{factor.source || '-'}</Descriptions.Item>
          <Descriptions.Item label="Formula" span={3}>
            <div style={{
              background: themeToken.colorFillQuaternary,
              padding: '16px 20px', borderRadius: 8,
              border: `1px solid ${themeToken.colorBorderSecondary}`,
              fontSize: 16, lineHeight: 2, overflow: 'auto',
            }}>
              <MathFormula formula={factor.formula || ''} />
            </div>
          </Descriptions.Item>
          <Descriptions.Item label="Description" span={3}>
            {factor.description || '-'}
          </Descriptions.Item>
          {factor.paper_reference && (
            <Descriptions.Item label="Reference" span={3}>
              {factor.paper_reference}
            </Descriptions.Item>
          )}
        </Descriptions>
      </Card>

      <Row gutter={[16, 16]}>
        <Col xs={24} lg={14}>
          <Card title="Factor Values (Sample)">
            {valuesForChart.length > 0 ? (
              <ReactECharts option={tsOption} style={{ height: 340 }} />
            ) : (
              <Typography.Text type="secondary">No values computed yet</Typography.Text>
            )}
          </Card>
        </Col>
        <Col xs={24} lg={10}>
          <Card title="Recent Values">
            <Table
              dataSource={recentValues.slice(0, 10)}
              columns={columns}
              rowKey={(r: any) => `${r.ts_code}_${r.trade_date}`}
              size="small"
              pagination={false}
              scroll={{ y: 280 }}
            />
          </Card>
        </Col>
      </Row>
    </div>
  );
}
