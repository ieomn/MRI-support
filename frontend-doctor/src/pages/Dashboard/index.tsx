/**
 * 数据看板页面
 */
import React, { useState, useEffect, useCallback } from 'react';
import { Card, Row, Col, Statistic, Table, Tag, Space, Typography } from 'antd';
import {
  UserOutlined, FileImageOutlined, RobotOutlined, CalendarOutlined,
  RiseOutlined, CheckCircleOutlined, WarningOutlined, MedicineBoxOutlined,
} from '@ant-design/icons';
import ReactECharts from 'echarts-for-react';
import { patientAPI, followupAPI, medgemmaAPI } from '../../services/api';

const { Title } = Typography;

const Dashboard: React.FC = () => {
  const [stats, setStats] = useState({ patients: 0, stages: {} as Record<string, number>, genders: {} as Record<string, number> });
  const [followupStats, setFollowupStats] = useState<any>(null);
  const [mgStatus, setMgStatus] = useState<any>(null);

  const load = useCallback(async () => {
    try {
      const res: any = await patientAPI.list({ page: 1, page_size: 1000 });
      if (res.success) {
        const items = res.data.items || [];
        const stages: Record<string, number> = {};
        const genders: Record<string, number> = { female: 0, male: 0 };
        items.forEach((p: any) => {
          if (p.stage) stages[p.stage] = (stages[p.stage] || 0) + 1;
          if (p.gender) genders[p.gender] = (genders[p.gender] || 0) + 1;
        });
        setStats({ patients: res.data.total, stages, genders });
      }
    } catch { /* interceptor */ }

    try {
      const res: any = await followupAPI.getDashboard();
      if (res.success) setFollowupStats(res.data);
    } catch { /* interceptor */ }

    try {
      const res: any = await medgemmaAPI.health();
      if (res.success) setMgStatus(res.data);
    } catch { setMgStatus({ status: 'offline' }); }
  }, []);

  useEffect(() => { load(); }, [load]);

  const stageChartOption = {
    tooltip: { trigger: 'item' },
    legend: { bottom: 0 },
    series: [
      {
        type: 'pie',
        radius: ['40%', '70%'],
        avoidLabelOverlap: false,
        itemStyle: { borderRadius: 6, borderColor: '#fff', borderWidth: 2 },
        label: { show: true, formatter: '{b}: {c}例' },
        data: Object.entries(stats.stages).map(([name, value]) => ({ name: `${name}期`, value })),
      },
    ],
  };

  const taskStats = followupStats?.status_stats || {};

  const taskBarOption = {
    tooltip: {},
    xAxis: { type: 'category', data: ['待完成', '已完成', '已逾期'] },
    yAxis: { type: 'value' },
    series: [
      {
        type: 'bar',
        data: [
          { value: taskStats.pending || 0, itemStyle: { color: '#1890ff' } },
          { value: taskStats.completed || 0, itemStyle: { color: '#52c41a' } },
          { value: taskStats.overdue || 0, itemStyle: { color: '#ff4d4f' } },
        ],
        barWidth: 40,
        itemStyle: { borderRadius: [4, 4, 0, 0] },
      },
    ],
  };

  const mgOnline = mgStatus?.status === 'healthy';

  return (
    <div style={{ padding: 24 }}>
      <Title level={4} style={{ marginBottom: 24 }}>数据看板</Title>

      {/* 核心指标 */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Card>
            <Statistic title="患者总数" value={stats.patients} prefix={<UserOutlined />} valueStyle={{ color: '#1890ff' }} />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic title="女性患者" value={stats.genders.female || 0} prefix={<MedicineBoxOutlined />} valueStyle={{ color: '#eb2f96' }} />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="待完成随访"
              value={taskStats.pending || 0}
              prefix={<CalendarOutlined />}
              valueStyle={{ color: '#faad14' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="MedGemma 状态"
              value={mgOnline ? '在线' : '离线'}
              prefix={<RobotOutlined />}
              valueStyle={{ color: mgOnline ? '#52c41a' : '#ff4d4f' }}
            />
            {mgOnline && mgStatus?.gpu && (
              <div style={{ fontSize: 12, color: '#999', marginTop: 4 }}>{mgStatus.gpu}</div>
            )}
          </Card>
        </Col>
      </Row>

      {/* 图表 */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={12}>
          <Card title="患者分期分布">
            {Object.keys(stats.stages).length > 0
              ? <ReactECharts option={stageChartOption} style={{ height: 300 }} />
              : <div style={{ height: 300, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#999' }}>暂无分期数据</div>
            }
          </Card>
        </Col>
        <Col span={12}>
          <Card title="随访任务统计">
            <ReactECharts option={taskBarOption} style={{ height: 300 }} />
          </Card>
        </Col>
      </Row>

      {/* 逾期任务 */}
      {followupStats?.overdue_tasks?.length > 0 && (
        <Card title={<Space><WarningOutlined style={{ color: '#ff4d4f' }} /> 逾期任务提醒</Space>}>
          <Table
            size="small"
            dataSource={followupStats.overdue_tasks}
            rowKey="id"
            pagination={false}
            columns={[
              { title: '患者 ID', dataIndex: 'patient_id', width: 100 },
              { title: '任务', dataIndex: 'task_title' },
              { title: '计划日期', dataIndex: 'scheduled_date', width: 170 },
              { title: '状态', render: () => <Tag color="red">逾期</Tag>, width: 80 },
            ]}
          />
        </Card>
      )}
    </div>
  );
};

export default Dashboard;
