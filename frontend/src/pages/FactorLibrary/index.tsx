import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import {
  Card, Row, Col, Input, Select, Tag, Typography, Spin, Empty, Result, Button, Space,
} from 'antd';
import { SearchOutlined, RiseOutlined, FallOutlined, ReloadOutlined } from '@ant-design/icons';
import { factorsApi } from '../../api/factors';
import type { FactorCatalog } from '../../types';

const { Meta } = Card;
const { Text, Paragraph } = Typography;

const CATEGORY_COLORS: Record<string, string> = {
  momentum: '#f50',
  value: '#2db7f5',
  quality: '#87d068',
  volatility: '#722ed1',
  technical: '#108ee9',
  size: '#eb2f96',
  sentiment: '#faad14',
};

export default function FactorLibrary() {
  const [search, setSearch] = useState('');
  const [category, setCategory] = useState<string | undefined>();
  const navigate = useNavigate();

  const { data: factorsResp, isLoading, isError, error, refetch } = useQuery({
    queryKey: ['factors', category],
    queryFn: () => factorsApi.list({ category, page: 1, page_size: 100 }),
    retry: 1,
  });

  const { data: catsResp } = useQuery({
    queryKey: ['factor-categories'],
    queryFn: factorsApi.categories,
    retry: 1,
  });

  const factors = ((factorsResp as any)?.data?.items || []) as FactorCatalog[];
  const categories = ((catsResp as any)?.data || []) as { category: string; count: number }[];

  const filtered = factors.filter((f) => {
    if (!search) return true;
    const s = search.toLowerCase();
    return (
      f.name.toLowerCase().includes(s) ||
      f.code.toLowerCase().includes(s) ||
      (f.name_cn && f.name_cn.includes(s))
    );
  });

  if (isError) {
    return (
      <Result
        status="error"
        title="无法连接后端服务"
        subTitle={
          <div>
            <p>请确认后端服务已启动：</p>
            <code style={{ background: '#f5f5f5', padding: '4px 8px', borderRadius: 4 }}>
              cd backend && uvicorn app.main:app --reload --port 8000
            </code>
            <p style={{ marginTop: 8, color: '#999', fontSize: 12 }}>
              错误详情: {(error as any)?.message || 'Network Error'}
            </p>
          </div>
        }
        extra={
          <Button type="primary" icon={<ReloadOutlined />} onClick={() => refetch()}>
            重新连接
          </Button>
        }
      />
    );
  }

  return (
    <Spin spinning={isLoading}>
      <Space style={{ marginBottom: 16, width: '100%' }} size="middle">
        <Input
          placeholder="Search factors..."
          prefix={<SearchOutlined />}
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          style={{ width: 260 }}
          allowClear
        />
        <Select
          placeholder="All Categories"
          allowClear
          style={{ width: 180 }}
          value={category}
          onChange={setCategory}
          options={categories.map((c) => ({
            value: c.category,
            label: `${c.category} (${c.count})`,
          }))}
        />
      </Space>

      {!isLoading && factors.length === 0 ? (
        <Empty description="Factor catalog is empty. The backend will seed factors on startup — ensure the backend has started at least once." />
      ) : (
        <Row gutter={[16, 16]}>
          {filtered.map((f) => (
            <Col xs={24} sm={12} lg={8} xl={6} key={f.code}>
              <Card
                hoverable
                onClick={() => navigate(`/factors/${f.code}`)}
                style={{ height: '100%', cursor: 'pointer' }}
              >
                <Meta
                  title={
                    <Space>
                      <span>{f.name}</span>
                      {f.name_cn && (
                        <Text type="secondary" style={{ fontSize: 13 }}>
                          {f.name_cn}
                        </Text>
                      )}
                    </Space>
                  }
                  description={
                    <>
                      <div style={{ marginBottom: 8 }}>
                        <Tag color={CATEGORY_COLORS[f.category] || '#999'}>
                          {f.category}
                        </Tag>
                        {f.sub_category && (
                          <Tag>{f.sub_category}</Tag>
                        )}
                        <Tag
                          icon={f.polarity === 'positive' ? <RiseOutlined /> : <FallOutlined />}
                          color={f.polarity === 'positive' ? 'green' : 'red'}
                        >
                          {f.polarity}
                        </Tag>
                      </div>
                      <Paragraph
                        ellipsis={{ rows: 2 }}
                        type="secondary"
                        style={{ fontSize: 12, marginBottom: 4 }}
                      >
                        {f.description}
                      </Paragraph>
                      <Text type="secondary" style={{ fontSize: 11 }}>
                        {f.source}
                      </Text>
                    </>
                  }
                />
              </Card>
            </Col>
          ))}
        </Row>
      )}
    </Spin>
  );
}
