import { useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import {
  Row, Col, Card, Select, InputNumber, Button, Table, Tag, Typography, Radio, Empty, Space, DatePicker, message,
} from 'antd';
import { SearchOutlined, PlusOutlined, DeleteOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import { factorsApi } from '../../api/factors';
import { screenerApi } from '../../api/backtest';
import type { FactorCatalog, ScreenerCondition } from '../../types';

const OPERATORS = [
  { value: 'gt', label: '>' },
  { value: 'lt', label: '<' },
  { value: 'gte', label: '>=' },
  { value: 'lte', label: '<=' },
];

export default function StockScreener() {
  const [conditions, setConditions] = useState<ScreenerCondition[]>([
    { factor_code: '', operator: 'gt', value: 0 },
  ]);
  const [logic, setLogic] = useState<'AND' | 'OR'>('AND');
  const [dateRange, setDateRange] = useState<[dayjs.Dayjs, dayjs.Dayjs]>([
    dayjs().subtract(60, 'day'),
    dayjs(),
  ]);

  const { data: factorsResp } = useQuery({
    queryKey: ['factors-all-screen'],
    queryFn: () => factorsApi.list({ page: 1, page_size: 100 }),
  });
  const factors = ((factorsResp as any)?.data?.items || []) as FactorCatalog[];

  const screenMut = useMutation({
    mutationFn: () => screenerApi.search({
      conditions: conditions.filter((c) => c.factor_code),
      logic,
      start_date: dateRange[0].format('YYYY-MM-DD'),
      end_date: dateRange[1].format('YYYY-MM-DD'),
      page: 1,
      page_size: 100,
    }),
    onError: (err: any) => {
      const detail = err?.response?.data?.detail || err?.message || 'Unknown error';
      message.error(typeof detail === 'string' ? detail : JSON.stringify(detail));
    },
  });

  const results = ((screenMut.data as any)?.data?.items || []) as any[];
  const total = ((screenMut.data as any)?.data?.total || 0) as number;

  const updateCondition = (index: number, field: string, value: unknown) => {
    const newConds = [...conditions];
    (newConds[index] as any)[field] = value;
    setConditions(newConds);
  };

  const addCondition = () => {
    setConditions([...conditions, { factor_code: '', operator: 'gt', value: 0 }]);
  };

  const removeCondition = (index: number) => {
    if (conditions.length <= 1) return;
    setConditions(conditions.filter((_, i) => i !== index));
  };

  const columns = [
    { title: 'Stock Code', dataIndex: 'ts_code', width: 120 },
    { title: 'Name', dataIndex: 'stock_name', width: 120 },
    ...conditions.filter(c => c.factor_code).map((c) => ({
      title: c.factor_code,
      dataIndex: c.factor_code,
      render: (_: any, record: any) => {
        const val = record.matching_factors?.[c.factor_code];
        return val !== undefined ? val?.toFixed(4) : '-';
      },
    })),
  ];

  return (
    <div>
      <Card title="Stock Screener" style={{ marginBottom: 16 }}>
        <Space direction="vertical" style={{ width: '100%' }} size="middle">
          <Space>
            <Radio.Group value={logic} onChange={(e) => setLogic(e.target.value)}>
              <Radio.Button value="AND">AND (All conditions)</Radio.Button>
              <Radio.Button value="OR">OR (Any condition)</Radio.Button>
            </Radio.Group>
            <DatePicker.RangePicker
              value={dateRange}
              onChange={(dates) => dates && setDateRange(dates as [dayjs.Dayjs, dayjs.Dayjs])}
              size="small"
            />
            <Typography.Text type="secondary">
              Compute factor values first on Factor Detail page
            </Typography.Text>
          </Space>

          {conditions.map((cond, i) => (
            <Row gutter={8} key={i} align="middle">
              <Col flex="auto">
                <Select
                  placeholder="Select factor"
                  style={{ width: '100%' }}
                  value={cond.factor_code || undefined}
                  onChange={(v) => updateCondition(i, 'factor_code', v)}
                  options={factors.map((f) => ({
                    value: f.code,
                    label: `${f.name} [${f.category}]`,
                  }))}
                  showSearch
                  filterOption={(input, option) =>
                    (option?.label as string)?.toLowerCase().includes(input.toLowerCase())
                  }
                />
              </Col>
              <Col>
                <Select
                  value={cond.operator}
                  onChange={(v) => updateCondition(i, 'operator', v)}
                  options={OPERATORS}
                  style={{ width: 80 }}
                />
              </Col>
              <Col>
                <InputNumber
                  value={cond.value}
                  onChange={(v) => updateCondition(i, 'value', v || 0)}
                  step={0.1}
                  style={{ width: 120 }}
                />
              </Col>
              <Col>
                <Button
                  danger
                  icon={<DeleteOutlined />}
                  onClick={() => removeCondition(i)}
                  disabled={conditions.length <= 1}
                />
              </Col>
            </Row>
          ))}

          <Space>
            <Button icon={<PlusOutlined />} onClick={addCondition}>
              Add Condition
            </Button>
            <Button
              type="primary"
              icon={<SearchOutlined />}
              loading={screenMut.isPending}
              onClick={() => screenMut.mutate()}
              disabled={!conditions.some((c) => c.factor_code)}
            >
              Search
            </Button>
          </Space>
        </Space>
      </Card>

      <Card title={`Results (${total})`}>
        {results.length > 0 ? (
          <Table
            dataSource={results}
            columns={columns}
            rowKey="ts_code"
            size="small"
            pagination={{ pageSize: 50, showTotal: (t) => `${t} stocks` }}
          />
        ) : (
          <Empty description="Add conditions and click Search" />
        )}
      </Card>
    </div>
  );
}
