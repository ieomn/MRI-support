/**
 * AI 分析结果可视化组件
 * 包含风险仪表盘、生存率折线图、报告展示
 */
import React from 'react';
import { Card, Tag, Space, Typography, Divider, Progress, Row, Col, Statistic } from 'antd';
import {
  CheckCircleOutlined,
  WarningOutlined,
  CloseCircleOutlined,
  ClockCircleOutlined,
  FileTextOutlined,
  RobotOutlined,
} from '@ant-design/icons';
import ReactECharts from 'echarts-for-react';

const { Text, Paragraph } = Typography;

// ==================== 风险仪表盘 ====================

export const RiskGauge: React.FC<{ score: number; level: string }> = ({ score, level }) => {
  const color = level === 'low' ? '#52c41a' : level === 'medium' ? '#faad14' : '#ff4d4f';
  const labelMap: Record<string, string> = { low: '低风险', medium: '中风险', high: '高风险' };

  const option = {
    series: [
      {
        type: 'gauge',
        startAngle: 200,
        endAngle: -20,
        min: 0,
        max: 1,
        splitNumber: 10,
        radius: '100%',
        axisLine: {
          lineStyle: {
            width: 16,
            color: [
              [0.3, '#52c41a'],
              [0.7, '#faad14'],
              [1, '#ff4d4f'],
            ],
          },
        },
        pointer: { itemStyle: { color: '#333' }, length: '60%', width: 4 },
        axisTick: { show: false },
        splitLine: { show: false },
        axisLabel: { show: false },
        detail: {
          valueAnimation: true,
          formatter: `{value|${(score * 100).toFixed(0)}%}\n{label|${labelMap[level] || level}}`,
          rich: {
            value: { fontSize: 22, fontWeight: 'bold', color: color },
            label: { fontSize: 13, color: '#666', padding: [6, 0, 0, 0] },
          },
          offsetCenter: [0, '60%'],
        },
        data: [{ value: score }],
      },
    ],
  };

  return <ReactECharts option={option} style={{ height: 200 }} />;
};

// ==================== 生存率折线图 ====================

export const SurvivalChart: React.FC<{
  survival?: { '1_year': number; '3_year': number; '5_year': number };
  recurrence?: { '2_year': number; '5_year': number };
}> = ({ survival, recurrence }) => {
  if (!survival && !recurrence) return null;

  const option: any = {
    tooltip: { trigger: 'axis', formatter: '{b}: {c}%' },
    legend: { data: [] as string[] },
    grid: { left: 50, right: 20, top: 40, bottom: 30 },
    xAxis: { type: 'category', data: [] as string[], boundaryGap: false },
    yAxis: { type: 'value', min: 0, max: 100, axisLabel: { formatter: '{value}%' } },
    series: [] as any[],
  };

  if (survival) {
    option.legend.data.push('总生存率');
    option.xAxis.data = ['0年', '1年', '3年', '5年'];
    option.series.push({
      name: '总生存率',
      type: 'line',
      smooth: true,
      data: [100, +(survival['1_year'] * 100).toFixed(1), +(survival['3_year'] * 100).toFixed(1), +(survival['5_year'] * 100).toFixed(1)],
      areaStyle: { opacity: 0.15 },
      lineStyle: { color: '#1890ff' },
      itemStyle: { color: '#1890ff' },
    });
  }

  if (recurrence) {
    option.legend.data.push('复发概率');
    if (!option.xAxis.data.length) option.xAxis.data = ['0年', '2年', '5年'];
    option.series.push({
      name: '复发概率',
      type: 'line',
      smooth: true,
      data: survival
        ? [0, null, +(recurrence['2_year'] * 100).toFixed(1), +(recurrence['5_year'] * 100).toFixed(1)]
        : [0, +(recurrence['2_year'] * 100).toFixed(1), +(recurrence['5_year'] * 100).toFixed(1)],
      lineStyle: { color: '#ff4d4f', type: 'dashed' },
      itemStyle: { color: '#ff4d4f' },
    });
  }

  return <ReactECharts option={option} style={{ height: 260 }} />;
};

// ==================== AI 结果卡片 ====================

export const AIResultCard: React.FC<{ result: any }> = ({ result }) => {
  const isMedGemma = result.analysis_type?.startsWith('medgemma');

  const typeConfig: Record<string, { label: string; color: string; icon: React.ReactNode }> = {
    segmentation: { label: 'U-Net 病灶分割', color: 'blue', icon: <CheckCircleOutlined /> },
    prediction: { label: '回归预后预测', color: 'purple', icon: <ClockCircleOutlined /> },
    medgemma_report: { label: 'MedGemma 影像报告', color: 'cyan', icon: <RobotOutlined /> },
    medgemma_prognosis: { label: 'MedGemma 预后分析', color: 'geekblue', icon: <RobotOutlined /> },
  };

  const cfg = typeConfig[result.analysis_type] || { label: result.analysis_type, color: 'default', icon: <FileTextOutlined /> };

  return (
    <Card
      size="small"
      style={{ marginBottom: 12 }}
      title={
        <Space>
          {cfg.icon}
          <Tag color={cfg.color}>{cfg.label}</Tag>
          {result.inference_time && (
            <Text type="secondary" style={{ fontSize: 12 }}>耗时 {result.inference_time.toFixed(1)}s</Text>
          )}
          {result.model_name && <Tag style={{ fontSize: 11 }}>{result.model_name}</Tag>}
        </Space>
      }
      extra={<Text type="secondary" style={{ fontSize: 12 }}>{result.created_at}</Text>}
    >
      {/* U-Net segmentation result */}
      {result.analysis_type === 'segmentation' && result.tumor_volume != null && (
        <Row gutter={24}>
          <Col span={8}><Statistic title="肿瘤体积" value={result.tumor_volume.toFixed(2)} suffix="cm³" /></Col>
        </Row>
      )}

      {/* Traditional regression result */}
      {result.analysis_type === 'prediction' && (
        <Row gutter={16}>
          <Col span={8}>
            {result.prognosis_score != null && <RiskGauge score={result.prognosis_score} level={result.risk_level || 'medium'} />}
          </Col>
          <Col span={16}>
            <SurvivalChart survival={result.survival_prediction} recurrence={result.recurrence_probability ? { '2_year': result.recurrence_probability, '5_year': result.recurrence_probability * 1.5 } : undefined} />
          </Col>
        </Row>
      )}

      {/* MedGemma report */}
      {isMedGemma && result.report_text && (
        <div style={{ whiteSpace: 'pre-wrap', lineHeight: 1.8, maxHeight: 400, overflow: 'auto' }}>
          {result.report_text}
        </div>
      )}
    </Card>
  );
};

export default AIResultCard;
