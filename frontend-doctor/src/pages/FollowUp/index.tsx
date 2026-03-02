/**
 * 随访管理页面
 */
import React, { useState, useEffect, useCallback } from 'react';
import {
  Card, Table, Button, Space, Tag, message, Modal, Form, Input, Select,
  DatePicker, Tabs, Statistic, Row, Col, List, Badge, Empty,
} from 'antd';
import {
  PlusOutlined, CalendarOutlined, CheckCircleOutlined,
  ClockCircleOutlined, WarningOutlined, ReloadOutlined,
} from '@ant-design/icons';
import { patientAPI, followupAPI } from '../../services/api';
import type { TabsProps } from 'antd';

const FollowUp: React.FC = () => {
  const [patients, setPatients] = useState<any[]>([]);
  const [selectedPatient, setSelectedPatient] = useState<number | null>(null);
  const [plans, setPlans] = useState<any[]>([]);
  const [tasks, setTasks] = useState<any[]>([]);
  const [dashboard, setDashboard] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [createVisible, setCreateVisible] = useState(false);
  const [form] = Form.useForm();

  const loadPatients = useCallback(async () => {
    try {
      const res: any = await patientAPI.list({ page: 1, page_size: 200 });
      if (res.success) setPatients(res.data.items || []);
    } catch { /* interceptor */ }
  }, []);

  const loadPlans = useCallback(async () => {
    if (!selectedPatient) { setPlans([]); return; }
    setLoading(true);
    try {
      const res: any = await followupAPI.getPatientPlans(selectedPatient);
      if (res.success) setPlans(res.data || []);
    } catch { /* interceptor */ }
    finally { setLoading(false); }
  }, [selectedPatient]);

  const loadTasks = useCallback(async () => {
    if (!selectedPatient) { setTasks([]); return; }
    try {
      const res: any = await followupAPI.getPatientTasks(selectedPatient);
      if (res.success) setTasks(res.data || []);
    } catch { /* interceptor */ }
  }, [selectedPatient]);

  const loadDashboard = useCallback(async () => {
    try {
      const res: any = await followupAPI.getDashboard();
      if (res.success) setDashboard(res.data);
    } catch { /* interceptor */ }
  }, []);

  useEffect(() => { loadPatients(); loadDashboard(); }, [loadPatients, loadDashboard]);
  useEffect(() => { loadPlans(); loadTasks(); }, [loadPlans, loadTasks]);

  const handleCreatePlan = async () => {
    try {
      const values = await form.validateFields();
      const res: any = await followupAPI.createPlan({
        patient_id: selectedPatient!,
        plan_name: values.plan_name,
        start_date: values.start_date.toISOString(),
        schedule_config: [
          { day: 30, tasks: ['术后1月问卷', '影像复查'] },
          { day: 90, tasks: ['术后3月问卷', '肿瘤标志物'] },
          { day: 180, tasks: ['术后6月问卷', '影像复查', '肿瘤标志物'] },
          { day: 365, tasks: ['术后1年问卷', '全面复查'] },
        ],
      });
      if (res.success) {
        message.success(res.message);
        setCreateVisible(false);
        form.resetFields();
        loadPlans();
        loadTasks();
        loadDashboard();
      }
    } catch { /* validation */ }
  };

  const statusTag = (status: string) => {
    const map: Record<string, { color: string; text: string; icon: React.ReactNode }> = {
      pending: { color: 'blue', text: '待完成', icon: <ClockCircleOutlined /> },
      completed: { color: 'green', text: '已完成', icon: <CheckCircleOutlined /> },
      overdue: { color: 'red', text: '已逾期', icon: <WarningOutlined /> },
    };
    const m = map[status] || { color: 'default', text: status, icon: null };
    return <Tag icon={m.icon} color={m.color}>{m.text}</Tag>;
  };

  const taskColumns = [
    { title: '任务', dataIndex: 'task_title', key: 'task_title' },
    { title: '类型', dataIndex: 'task_type', key: 'task_type', width: 100, render: (t: string) => <Tag>{t}</Tag> },
    { title: '计划日期', dataIndex: 'scheduled_date', key: 'scheduled_date', width: 170 },
    { title: '完成日期', dataIndex: 'completed_date', key: 'completed_date', width: 170, render: (d: string) => d || '-' },
    { title: '状态', dataIndex: 'status', key: 'status', width: 110, render: statusTag },
  ];

  const stats = dashboard?.status_stats || {};

  const tabItems: TabsProps['items'] = [
    {
      key: 'overview',
      label: '随访总览',
      children: (
        <>
          <Row gutter={16} style={{ marginBottom: 24 }}>
            <Col span={6}><Card><Statistic title="待完成任务" value={stats.pending || 0} valueStyle={{ color: '#1890ff' }} prefix={<ClockCircleOutlined />} /></Card></Col>
            <Col span={6}><Card><Statistic title="已完成任务" value={stats.completed || 0} valueStyle={{ color: '#52c41a' }} prefix={<CheckCircleOutlined />} /></Card></Col>
            <Col span={6}><Card><Statistic title="已逾期任务" value={stats.overdue || 0} valueStyle={{ color: '#ff4d4f' }} prefix={<WarningOutlined />} /></Card></Col>
            <Col span={6}><Card><Statistic title="总计划数" value={plans.length} prefix={<CalendarOutlined />} /></Card></Col>
          </Row>
          {dashboard?.overdue_tasks?.length > 0 && (
            <Card title={<Space><WarningOutlined style={{ color: '#ff4d4f' }} /> 逾期任务提醒</Space>} size="small">
              <List
                size="small"
                dataSource={dashboard.overdue_tasks}
                renderItem={(item: any) => (
                  <List.Item>
                    <Space>
                      <Badge status="error" />
                      <span>患者 #{item.patient_id}</span>
                      <span>{item.task_title}</span>
                      <Tag color="red">计划: {item.scheduled_date}</Tag>
                    </Space>
                  </List.Item>
                )}
              />
            </Card>
          )}
          {!dashboard?.overdue_tasks?.length && <Empty description="暂无逾期任务" />}
        </>
      ),
    },
    {
      key: 'plans',
      label: '随访计划',
      children: (
        <>
          <Space style={{ marginBottom: 16 }}>
            <Select
              showSearch allowClear placeholder="选择患者" style={{ width: 260 }}
              optionFilterProp="label" value={selectedPatient} onChange={setSelectedPatient}
              options={patients.map((p) => ({ value: p.id, label: `${p.patient_no} - ${p.name}` }))}
            />
            <Button type="primary" icon={<PlusOutlined />} disabled={!selectedPatient} onClick={() => setCreateVisible(true)}>
              新建随访计划
            </Button>
          </Space>
          <Table
            loading={loading} dataSource={plans} rowKey="id"
            columns={[
              { title: '计划名称', dataIndex: 'plan_name', key: 'plan_name' },
              { title: '开始日期', dataIndex: 'start_date', key: 'start_date', width: 170 },
              { title: '负责医师', dataIndex: 'doctor_name', key: 'doctor_name', width: 120, render: (v: string) => v || '-' },
              { title: '创建时间', dataIndex: 'created_at', key: 'created_at', width: 170 },
            ]}
          />
        </>
      ),
    },
    {
      key: 'tasks',
      label: '随访任务',
      children: (
        <>
          <Space style={{ marginBottom: 16 }}>
            <Select
              showSearch allowClear placeholder="选择患者" style={{ width: 260 }}
              optionFilterProp="label" value={selectedPatient} onChange={setSelectedPatient}
              options={patients.map((p) => ({ value: p.id, label: `${p.patient_no} - ${p.name}` }))}
            />
            <Button icon={<ReloadOutlined />} onClick={loadTasks}>刷新</Button>
          </Space>
          <Table loading={loading} dataSource={tasks} rowKey="id" columns={taskColumns} />
        </>
      ),
    },
  ];

  return (
    <div style={{ padding: 24 }}>
      <Card title="随访管理">
        <Tabs items={tabItems} />
      </Card>

      <Modal title="新建随访计划" open={createVisible} onOk={handleCreatePlan} onCancel={() => setCreateVisible(false)} width={500}>
        <Form form={form} layout="vertical">
          <Form.Item name="plan_name" label="计划名称" rules={[{ required: true }]}>
            <Input placeholder="例：术后标准随访计划" />
          </Form.Item>
          <Form.Item name="start_date" label="开始日期" rules={[{ required: true }]}>
            <DatePicker style={{ width: '100%' }} />
          </Form.Item>
        </Form>
        <div style={{ color: '#999', fontSize: 12, marginTop: 8 }}>
          将自动生成标准子宫内膜癌术后随访任务：1月、3月、6月、1年
        </div>
      </Modal>
    </div>
  );
};

export default FollowUp;
