import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Row, Col, Card, Statistic, Button, DatePicker, Table,
  Progress, message, Space, Typography, Tag, Spin, Result,
} from 'antd';
import {
  DownloadOutlined, ReloadOutlined, DatabaseOutlined,
  CalendarOutlined, CheckCircleOutlined,
} from '@ant-design/icons';
import dayjs from 'dayjs';
import { dataApi } from '../../api/data';

const { RangePicker } = DatePicker;

export default function DataCenter() {
  const [downloading, setDownloading] = useState(false);
  const [dlDateRange, setDlDateRange] = useState<[dayjs.Dayjs, dayjs.Dayjs]>([
    dayjs().subtract(30, 'day'),
    dayjs(),
  ]);
  const queryClient = useQueryClient();

  const { data: status, isLoading: loadingStatus, isError, refetch } = useQuery({
    queryKey: ['data-status'],
    queryFn: dataApi.status,
    refetchInterval: downloading ? 3000 : false,
    retry: 1,
  });

  const { data: stocks } = useQuery({
    queryKey: ['data-stocks'],
    queryFn: () => dataApi.stocks({ page: 1, page_size: 20 }),
  });

  const { data: dateRange } = useQuery({
    queryKey: ['data-date-range'],
    queryFn: dataApi.dateRange,
  });

  const downloadStockListMut = useMutation({
    mutationFn: () => dataApi.downloadStockList(),
    onSuccess: () => {
      message.success('Stock list downloaded');
      queryClient.invalidateQueries({ queryKey: ['data-status'] });
    },
    onError: (err: any) => {
      const detail = err?.response?.data?.detail || err?.message || 'Unknown error';
      message.error(typeof detail === 'string' ? detail : JSON.stringify(detail));
    },
  });

  const st = (status as any)?.data || {};
  const stockList = ((stocks as any)?.data?.items || []) as Array<{
    ts_code: string; name: string; industry?: string;
  }>;
  const dr = (dateRange as any)?.data || {};

  const handleDownloadDaily = async () => {
    setDownloading(true);
    try {
      const startDate = dlDateRange[0].format('YYYY-MM-DD');
      const endDate = dlDateRange[1].format('YYYY-MM-DD');
      await dataApi.downloadDaily({ start_date: startDate, end_date: endDate });
      message.info('Daily data download started');
    } catch (err: any) {
      const detail = err?.response?.data?.detail || err?.message || 'Unknown error';
      message.error(typeof detail === 'string' ? detail : JSON.stringify(detail));
      setDownloading(false);
    }
  };

  // Poll for download completion
  const { data: progress } = useQuery({
    queryKey: ['download-progress'],
    queryFn: dataApi.downloadProgress,
    refetchInterval: downloading ? 2000 : false,
  });
  const prog = (progress as any)?.data || {};

  if (!downloading && prog?.in_progress) {
    setDownloading(true);
  }
  if (downloading && !prog?.in_progress && prog?.total > 0) {
    // Download just finished
    if (downloading) {
      message.success('Download completed!');
      setDownloading(false);
      queryClient.invalidateQueries({ queryKey: ['data-status'] });
      queryClient.invalidateQueries({ queryKey: ['data-date-range'] });
    }
  }

  const columns = [
    { title: 'Code', dataIndex: 'ts_code', key: 'ts_code', width: 120 },
    { title: 'Name', dataIndex: 'name', key: 'name' },
    {
      title: 'Industry', dataIndex: 'industry', key: 'industry',
      render: (v: string) => v ? <Tag>{v}</Tag> : '-',
    },
  ];

  const downloadPercent = prog?.total > 0
    ? Math.round((prog.current / prog.total) * 100) : 0;

  if (isError) {
    return (
      <Result
        status="warning"
        title="无法连接后端"
        subTitle="数据中心需要后端 API。请先启动后端服务：cd backend && uvicorn app.main:app --port 8000"
        extra={
          <Button type="primary" icon={<ReloadOutlined />} onClick={() => refetch()}>
            重试
          </Button>
        }
      />
    );
  }

  return (
    <Spin spinning={loadingStatus}>
      <Row gutter={[16, 16]}>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Stocks"
              value={st.stock_count || 0}
              prefix={<DatabaseOutlined />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Daily Records"
              value={st.daily_count || 0}
              prefix={<CalendarOutlined />}
              formatter={(v) => typeof v === 'number' ? (v / 10000).toFixed(0) + '万' : String(v)}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic title="Date Range" value={`${st.min_date || '-'} ~ ${st.max_date || '-'}`} />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic title="Industries" value={st.industry_count || 0} />
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col xs={24} lg={12}>
          <Card
            title="Data Download"
            extra={
              <Button
                icon={<ReloadOutlined />}
                onClick={() => queryClient.invalidateQueries({ queryKey: ['data-status'] })}
              >
                Refresh
              </Button>
            }
          >
            <Space direction="vertical" style={{ width: '100%' }} size="middle">
              <div>
                <Typography.Text strong>Step 1: Download stock list</Typography.Text>
                <br />
                <Button
                  type="primary"
                  icon={<DownloadOutlined />}
                  loading={downloadStockListMut.isPending}
                  onClick={() => downloadStockListMut.mutate()}
                  style={{ marginTop: 8 }}
                >
                  Download Stock List
                </Button>
              </div>

              <div>
                <Typography.Text strong>Step 2: Download daily data</Typography.Text>
                <br />
                <Space style={{ marginTop: 8 }}>
                  <RangePicker
                    value={dlDateRange}
                    onChange={(dates) => dates && setDlDateRange(dates as [dayjs.Dayjs, dayjs.Dayjs])}
                  />
                  <Button
                    type="primary"
                    icon={<DownloadOutlined />}
                    loading={downloading}
                    onClick={handleDownloadDaily}
                    disabled={!st.stock_count}
                  >
                    Download Daily Data
                  </Button>
                </Space>
              </div>

              {downloading && (
                <div>
                  <Typography.Text>Downloading... {prog.current}/{prog.total}</Typography.Text>
                  <Progress percent={downloadPercent} status="active" />
                </div>
              )}

              {!downloading && prog?.total > 0 && prog?.current === prog?.total && (
                <Tag icon={<CheckCircleOutlined />} color="success">
                  Download Complete — {prog.total} stocks processed
                </Tag>
              )}

              <div>
                <Typography.Text type="secondary">
                  Available range: {dr.min_date || 'N/A'} ~ {dr.max_date || 'N/A'}
                </Typography.Text>
              </div>
            </Space>
          </Card>
        </Col>

        <Col xs={24} lg={12}>
          <Card title="Stock List Preview">
            <Table
              dataSource={stockList}
              columns={columns}
              rowKey="ts_code"
              size="small"
              pagination={false}
              scroll={{ y: 300 }}
            />
          </Card>
        </Col>
      </Row>
    </Spin>
  );
}
