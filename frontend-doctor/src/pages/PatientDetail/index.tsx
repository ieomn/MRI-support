/**
 * 患者详情页面 (F-CD-02)
 * 患者 360° 视图 — 基本信息 / 影像 / AI 分析 / MedGemma / 随访
 */
import React, { useState, useEffect, useCallback } from 'react';
import {
  Card,
  Tabs,
  Descriptions,
  Button,
  Upload,
  message,
  Table,
  Tag,
  Space,
  Spin,
  Input,
  Form,
  InputNumber,
  Select,
  Switch,
  Typography,
  Alert,
  Divider,
  Empty,
} from 'antd';
import {
  UploadOutlined,
  ThunderboltOutlined,
  RobotOutlined,
  SendOutlined,
  FileTextOutlined,
  MedicineBoxOutlined,
  ArrowLeftOutlined,
} from '@ant-design/icons';
import { useParams, useNavigate } from 'react-router-dom';
import { patientAPI, imageAPI, aiAPI, medgemmaAPI, followupAPI } from '../../services/api';
import { RiskGauge, SurvivalChart, AIResultCard } from '../../components/AIResultViz';
import type { UploadProps, TabsProps } from 'antd';

const { TextArea } = Input;
const { Title, Paragraph, Text } = Typography;

// ==================== 报告展示组件 ====================

const ReportViewer: React.FC<{
  title: string;
  content: string;
  inferenceTime?: number;
  modelId?: string;
}> = ({ title, content, inferenceTime, modelId }) => (
  <Card
    size="small"
    title={
      <Space>
        <FileTextOutlined />
        <span>{title}</span>
      </Space>
    }
    extra={
      <Space size="middle">
        {inferenceTime != null && (
          <Text type="secondary" style={{ fontSize: 12 }}>
            耗时 {inferenceTime.toFixed(1)}s
          </Text>
        )}
        {modelId && (
          <Tag color="blue" style={{ fontSize: 11 }}>
            {modelId}
          </Tag>
        )}
      </Space>
    }
    style={{ marginBottom: 16 }}
  >
    <Typography>
      <div style={{ whiteSpace: 'pre-wrap', lineHeight: 1.8 }}>{content}</div>
    </Typography>
  </Card>
);

// ==================== 主组件 ====================

const PatientDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const patientId = parseInt(id || '0');

  const [patient, setPatient] = useState<any>(null);
  const [images, setImages] = useState<any[]>([]);
  const [aiResults, setAiResults] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  const [followupTasks, setFollowupTasks] = useState<any[]>([]);

  // MedGemma 状态
  const [mgImageLoading, setMgImageLoading] = useState(false);
  const [mgProgLoading, setMgProgLoading] = useState(false);
  const [mgAskLoading, setMgAskLoading] = useState(false);
  const [mgImageReport, setMgImageReport] = useState<any>(null);
  const [mgProgReport, setMgProgReport] = useState<any>(null);
  const [mgAnswer, setMgAnswer] = useState<any>(null);

  const [progForm] = Form.useForm();
  const [question, setQuestion] = useState('');

  // ========== 数据加载 ==========

  const loadPatient = useCallback(async () => {
    try {
      const res: any = await patientAPI.get(patientId);
      if (res.success) setPatient(res.data);
    } catch { /* handled by interceptor */ }
  }, [patientId]);

  const loadImages = useCallback(async () => {
    try {
      const res: any = await imageAPI.getPatientImages(patientId);
      if (res.success) setImages(res.data || []);
    } catch { /* handled by interceptor */ }
  }, [patientId]);

  const loadAIResults = useCallback(async () => {
    try {
      const res: any = await aiAPI.getPatientResults(patientId);
      if (res.success) setAiResults(res.data || []);
    } catch { /* handled by interceptor */ }
  }, [patientId]);

  const loadFollowup = useCallback(async () => {
    try {
      const res: any = await followupAPI.getPatientTasks(patientId);
      if (res.success) setFollowupTasks(res.data || []);
    } catch { /* interceptor */ }
  }, [patientId]);

  useEffect(() => {
    if (patientId) {
      loadPatient();
      loadImages();
      loadAIResults();
      loadFollowup();
    }
  }, [patientId, loadPatient, loadImages, loadAIResults, loadFollowup]);

  // ========== U-Net 分割 ==========

  const handleRunSegmentation = async (seriesId: number) => {
    setLoading(true);
    try {
      const res: any = await aiAPI.runSegmentation({ series_id: seriesId, threshold: 0.5 });
      if (res.success) {
        message.success('U-Net 分割完成');
        loadAIResults();
      }
    } catch { /* interceptor */ }
    finally { setLoading(false); }
  };

  // ========== MedGemma 影像分析 ==========

  const handleMedGemmaImage = async (seriesId: number) => {
    setMgImageLoading(true);
    setMgImageReport(null);
    try {
      const clinicalContext = patient
        ? `${patient.age || ''}岁${patient.gender === 'female' ? '女' : '男'}性，诊断：${patient.diagnosis || '子宫内膜癌'}，分期：${patient.stage || '未知'}`
        : undefined;

      const res: any = await medgemmaAPI.analyzeImage({
        series_id: seriesId,
        patient_id: patientId,
        clinical_context: clinicalContext,
      });
      if (res.success) {
        setMgImageReport(res.data);
        message.success('MedGemma 影像分析完成');
        loadAIResults();
      }
    } catch { /* interceptor */ }
    finally { setMgImageLoading(false); }
  };

  // ========== MedGemma 预后分析 ==========

  const handleMedGemmaPrognosis = async () => {
    try {
      const values = await progForm.validateFields();
      setMgProgLoading(true);
      setMgProgReport(null);

      const res: any = await medgemmaAPI.analyzePrognosis({
        patient_id: patientId,
        clinical_data: values,
      });
      if (res.success) {
        setMgProgReport(res.data);
        message.success('MedGemma 预后分析完成');
        loadAIResults();
      }
    } catch (e: any) {
      if (e?.errorFields) return;
    } finally {
      setMgProgLoading(false);
    }
  };

  // ========== MedGemma 自由问答 ==========

  const handleAsk = async () => {
    if (!question.trim()) { message.warning('请输入问题'); return; }
    setMgAskLoading(true);
    setMgAnswer(null);
    try {
      const res: any = await medgemmaAPI.ask({ question, patient_id: patientId });
      if (res.success) {
        setMgAnswer(res.data);
      }
    } catch { /* interceptor */ }
    finally { setMgAskLoading(false); }
  };

  // ========== DICOM 上传 ==========

  const uploadProps: UploadProps = {
    name: 'files',
    multiple: true,
    accept: '.dcm,.dicom',
    customRequest: async ({ file, onSuccess, onError }) => {
      try {
        const dt = new DataTransfer();
        dt.items.add(file as File);
        const res: any = await imageAPI.upload(patientId, dt.files);
        if (res.success) { message.success('上传成功'); onSuccess?.(res); loadImages(); }
      } catch (err) { message.error('上传失败'); onError?.(err as Error); }
    },
  };

  // ========== AI 结果表格列 ==========

  const analysisTypeLabel: Record<string, { text: string; color: string }> = {
    segmentation: { text: 'U-Net 分割', color: 'blue' },
    prediction: { text: '回归预测', color: 'purple' },
    medgemma_report: { text: 'MedGemma 影像报告', color: 'cyan' },
    medgemma_prognosis: { text: 'MedGemma 预后分析', color: 'geekblue' },
  };

  const aiResultColumns = [
    {
      title: '分析类型',
      dataIndex: 'analysis_type',
      key: 'analysis_type',
      width: 180,
      render: (type: string) => {
        const info = analysisTypeLabel[type] || { text: type, color: 'default' };
        return <Tag color={info.color}>{info.text}</Tag>;
      },
    },
    {
      title: '肿瘤体积',
      dataIndex: 'tumor_volume',
      key: 'tumor_volume',
      width: 120,
      render: (v: number) => (v != null ? `${v.toFixed(2)} cm³` : '-'),
    },
    {
      title: '预后评分',
      dataIndex: 'prognosis_score',
      key: 'prognosis_score',
      width: 100,
      render: (s: number) => (s != null ? s.toFixed(3) : '-'),
    },
    {
      title: '风险等级',
      dataIndex: 'risk_level',
      key: 'risk_level',
      width: 100,
      render: (level: string) => {
        if (!level) return '-';
        const map: Record<string, { color: string; text: string }> = {
          low: { color: 'green', text: '低风险' },
          medium: { color: 'orange', text: '中风险' },
          high: { color: 'red', text: '高风险' },
        };
        const m = map[level] || { color: 'default', text: level };
        return <Tag color={m.color}>{m.text}</Tag>;
      },
    },
    {
      title: '报告摘要',
      dataIndex: 'report_text',
      key: 'report_text',
      ellipsis: true,
      render: (text: string) => text ? <Text type="secondary">{text.slice(0, 80)}...</Text> : '-',
    },
    {
      title: '时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 180,
    },
  ];

  // ========== Tab 定义 ==========

  if (!patient) {
    return (
      <div style={{ padding: 24, textAlign: 'center' }}>
        <Spin size="large" tip="加载中..." />
      </div>
    );
  }

  const tabItems: TabsProps['items'] = [
    {
      key: 'info',
      label: '基本信息',
      children: (
        <Descriptions bordered column={2}>
          <Descriptions.Item label="患者编号">{patient.patient_no}</Descriptions.Item>
          <Descriptions.Item label="姓名">{patient.name}</Descriptions.Item>
          <Descriptions.Item label="性别">{patient.gender === 'female' ? '女' : '男'}</Descriptions.Item>
          <Descriptions.Item label="年龄">{patient.age || '-'}</Descriptions.Item>
          <Descriptions.Item label="联系电话">{patient.phone || '-'}</Descriptions.Item>
          <Descriptions.Item label="家庭地址">{patient.address || '-'}</Descriptions.Item>
          <Descriptions.Item label="所属医院">{patient.hospital || '-'}</Descriptions.Item>
          <Descriptions.Item label="入院日期">{patient.admission_date || '-'}</Descriptions.Item>
          <Descriptions.Item label="诊断结果" span={2}>{patient.diagnosis || '-'}</Descriptions.Item>
          <Descriptions.Item label="分期">{patient.stage || '-'}</Descriptions.Item>
        </Descriptions>
      ),
    },
    {
      key: 'images',
      label: '影像数据',
      children: (
        <>
          <div style={{ marginBottom: 16 }}>
            <Upload {...uploadProps}>
              <Button icon={<UploadOutlined />}>上传 DICOM 文件</Button>
            </Upload>
          </div>
          <Table
            dataSource={images}
            rowKey="id"
            columns={[
              { title: '序列 UID', dataIndex: 'series_uid', key: 'series_uid', ellipsis: true },
              { title: '成像方式', dataIndex: 'modality', key: 'modality', width: 100 },
              { title: '序列描述', dataIndex: 'series_description', key: 'series_description', ellipsis: true },
              { title: '文件数', dataIndex: 'file_count', key: 'file_count', width: 80 },
              { title: '上传时间', dataIndex: 'upload_time', key: 'upload_time', width: 180 },
              {
                title: '操作',
                key: 'action',
                width: 260,
                render: (_: any, record: any) => (
                  <Space>
                    <Button
                      size="small"
                      icon={<ThunderboltOutlined />}
                      onClick={() => handleRunSegmentation(record.id)}
                      loading={loading}
                    >
                      U-Net 分割
                    </Button>
                    <Button
                      type="primary"
                      size="small"
                      icon={<RobotOutlined />}
                      onClick={() => handleMedGemmaImage(record.id)}
                      loading={mgImageLoading}
                    >
                      MedGemma 分析
                    </Button>
                  </Space>
                ),
              },
            ]}
          />
          {mgImageReport && (
            <ReportViewer
              title="MedGemma 影像分析报告"
              content={mgImageReport.report}
              inferenceTime={mgImageReport.inference_time}
              modelId={mgImageReport.model_id}
            />
          )}
        </>
      ),
    },
    {
      key: 'ai-results',
      label: 'AI 分析结果',
      children: (
        <>
          {aiResults.length === 0 ? (
            <Empty description="暂无 AI 分析结果" />
          ) : (
            <>
              {aiResults.map((r: any) => (
                <AIResultCard key={r.id} result={r} />
              ))}
              <Divider>详细列表</Divider>
              <Table dataSource={aiResults} rowKey="id" columns={aiResultColumns} size="small" />
            </>
          )}
        </>
      ),
    },
    {
      key: 'medgemma',
      label: (
        <Space>
          <RobotOutlined />
          MedGemma 智能分析
        </Space>
      ),
      children: (
        <div>
          {/* ---- MedGemma 预后分析 ---- */}
          <Card
            title={<Space><MedicineBoxOutlined /> MedGemma 预后风险评估</Space>}
            style={{ marginBottom: 24 }}
          >
            <Alert
              type="info"
              showIcon
              message="填写患者临床数据后，MedGemma 将基于循证医学证据给出综合风险评估、复发概率及治疗建议。"
              style={{ marginBottom: 16 }}
            />
            <Form
              form={progForm}
              layout="inline"
              style={{ flexWrap: 'wrap', gap: 8 }}
              initialValues={{
                age: patient.age,
                stage: patient.stage,
                grade: 2,
                tumor_size: 3.0,
                lymph_node_positive: 0,
                bmi: 24.0,
              }}
            >
              <Form.Item name="age" label="年龄" rules={[{ required: true }]}>
                <InputNumber min={1} max={120} />
              </Form.Item>
              <Form.Item name="stage" label="分期" rules={[{ required: true }]}>
                <Select style={{ width: 100 }}>
                  <Select.Option value="I">I</Select.Option>
                  <Select.Option value="II">II</Select.Option>
                  <Select.Option value="III">III</Select.Option>
                  <Select.Option value="IV">IV</Select.Option>
                </Select>
              </Form.Item>
              <Form.Item name="grade" label="分级" rules={[{ required: true }]}>
                <Select style={{ width: 80 }}>
                  <Select.Option value={1}>G1</Select.Option>
                  <Select.Option value={2}>G2</Select.Option>
                  <Select.Option value={3}>G3</Select.Option>
                </Select>
              </Form.Item>
              <Form.Item name="tumor_size" label="肿瘤大小(cm)">
                <InputNumber min={0} step={0.1} />
              </Form.Item>
              <Form.Item name="lymph_node_positive" label="阳性淋巴结">
                <InputNumber min={0} />
              </Form.Item>
              <Form.Item name="bmi" label="BMI">
                <InputNumber min={10} max={60} step={0.1} />
              </Form.Item>
              <Form.Item name="histology" label="组织学类型">
                <Select style={{ width: 160 }} allowClear placeholder="请选择">
                  <Select.Option value="子宫内膜样腺癌">子宫内膜样腺癌</Select.Option>
                  <Select.Option value="浆液性癌">浆液性癌</Select.Option>
                  <Select.Option value="透明细胞癌">透明细胞癌</Select.Option>
                  <Select.Option value="癌肉瘤">癌肉瘤</Select.Option>
                </Select>
              </Form.Item>
              <Form.Item name="myometrial_invasion" label="肌层浸润">
                <Select style={{ width: 120 }} allowClear placeholder="请选择">
                  <Select.Option value="<50%">{'<50%'}</Select.Option>
                  <Select.Option value=">=50%">{'>=50%'}</Select.Option>
                </Select>
              </Form.Item>
              <Form.Item name="lvsi" label="LVSI" valuePropName="checked">
                <Switch checkedChildren="阳性" unCheckedChildren="阴性" />
              </Form.Item>
            </Form>
            <div style={{ marginTop: 16 }}>
              <Button
                type="primary"
                icon={<RobotOutlined />}
                loading={mgProgLoading}
                onClick={handleMedGemmaPrognosis}
              >
                开始 MedGemma 预后分析
              </Button>
            </div>
            {mgProgReport && (
              <div style={{ marginTop: 16 }}>
                {mgProgReport.risk_score != null && (
                  <Card size="small" style={{ marginBottom: 12 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 32 }}>
                      <div style={{ width: 200 }}>
                        <RiskGauge
                          score={mgProgReport.risk_score ?? 0.5}
                          level={mgProgReport.risk_level || 'medium'}
                        />
                      </div>
                      <div style={{ flex: 1 }}>
                        <SurvivalChart
                          survival={mgProgReport.survival}
                          recurrence={mgProgReport.recurrence}
                        />
                      </div>
                    </div>
                  </Card>
                )}
                <ReportViewer
                  title="MedGemma 预后分析报告"
                  content={mgProgReport.report}
                  inferenceTime={mgProgReport.inference_time}
                  modelId={mgProgReport.model_id}
                />
              </div>
            )}
          </Card>

          {/* ---- MedGemma 医学问答 ---- */}
          <Card title={<Space><SendOutlined /> MedGemma 医学问答</Space>}>
            <Alert
              type="info"
              showIcon
              message="输入任何关于该患者或子宫内膜癌的医学问题，MedGemma 将基于医学知识给出回答。"
              style={{ marginBottom: 16 }}
            />
            <Space.Compact style={{ width: '100%' }}>
              <TextArea
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                placeholder="例：该患者 FIGO IIB 期、G2，推荐的辅助治疗方案是什么？"
                autoSize={{ minRows: 2, maxRows: 4 }}
                onPressEnter={(e) => {
                  if (!e.shiftKey) { e.preventDefault(); handleAsk(); }
                }}
                style={{ flex: 1 }}
              />
            </Space.Compact>
            <div style={{ marginTop: 8 }}>
              <Button
                type="primary"
                icon={<SendOutlined />}
                loading={mgAskLoading}
                onClick={handleAsk}
              >
                发送
              </Button>
              <Text type="secondary" style={{ marginLeft: 12, fontSize: 12 }}>
                Enter 发送，Shift+Enter 换行
              </Text>
            </div>
            {mgAnswer && (
              <div style={{ marginTop: 16 }}>
                <ReportViewer
                  title="MedGemma 回答"
                  content={mgAnswer.answer}
                  inferenceTime={mgAnswer.inference_time}
                />
              </div>
            )}
          </Card>
        </div>
      ),
    },
    {
      key: 'followup',
      label: '随访记录',
      children: (
        <>
          {followupTasks.length === 0 ? (
            <Empty description="暂无随访任务，请在「随访管理」中创建随访计划" />
          ) : (
            <Table
              dataSource={followupTasks}
              rowKey="id"
              columns={[
                { title: '任务', dataIndex: 'task_title', key: 'task_title' },
                { title: '类型', dataIndex: 'task_type', key: 'task_type', width: 100, render: (t: string) => <Tag>{t}</Tag> },
                { title: '计划日期', dataIndex: 'scheduled_date', key: 'scheduled_date', width: 170 },
                { title: '完成日期', dataIndex: 'completed_date', key: 'completed_date', width: 170, render: (d: string) => d || '-' },
                {
                  title: '状态',
                  dataIndex: 'status',
                  key: 'status',
                  width: 100,
                  render: (s: string) => {
                    const map: Record<string, { color: string; text: string }> = {
                      pending: { color: 'blue', text: '待完成' },
                      completed: { color: 'green', text: '已完成' },
                      overdue: { color: 'red', text: '已逾期' },
                    };
                    const m = map[s] || { color: 'default', text: s };
                    return <Tag color={m.color}>{m.text}</Tag>;
                  },
                },
              ]}
            />
          )}
        </>
      ),
    },
  ];

  return (
    <div style={{ padding: 24 }}>
      <Card
        title={
          <Space>
            <Button
              type="text"
              icon={<ArrowLeftOutlined />}
              onClick={() => navigate('/patients')}
            />
            <span>患者详情 — {patient.name}</span>
            {patient.stage && <Tag color="orange">{patient.stage} 期</Tag>}
          </Space>
        }
      >
        <Tabs defaultActiveKey="info" items={tabItems} />
      </Card>
    </div>
  );
};

export default PatientDetail;
