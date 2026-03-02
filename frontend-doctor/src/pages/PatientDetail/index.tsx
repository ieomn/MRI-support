/**
 * 患者详情页面 (F-CD-02)
 * 患者360°视图
 */
import React, { useState, useEffect } from 'react';
import { Card, Tabs, Descriptions, Button, Upload, message, Table, Tag } from 'antd';
import { UploadOutlined, ThunderboltOutlined } from '@ant-design/icons';
import { useParams } from 'react-router-dom';
import { patientAPI, imageAPI, aiAPI } from '../../services/api';
import type { UploadProps } from 'antd';

const { TabPane } = Tabs;

const PatientDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const patientId = parseInt(id || '0');
  
  const [patient, setPatient] = useState<any>(null);
  const [images, setImages] = useState<any[]>([]);
  const [aiResults, setAiResults] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  // 加载患者信息
  const loadPatient = async () => {
    try {
      const response: any = await patientAPI.get(patientId);
      if (response.success) {
        setPatient(response.data);
      }
    } catch (error) {
      console.error('加载患者信息失败:', error);
    }
  };

  // 加载影像数据
  const loadImages = async () => {
    try {
      const response: any = await imageAPI.getPatientImages(patientId);
      if (response.success) {
        setImages(response.data);
      }
    } catch (error) {
      console.error('加载影像数据失败:', error);
    }
  };

  // 加载AI分析结果
  const loadAIResults = async () => {
    try {
      const response: any = await aiAPI.getPatientResults(patientId);
      if (response.success) {
        setAiResults(response.data);
      }
    } catch (error) {
      console.error('加载AI结果失败:', error);
    }
  };

  useEffect(() => {
    if (patientId) {
      loadPatient();
      loadImages();
      loadAIResults();
    }
  }, [patientId]);

  // DICOM上传配置
  const uploadProps: UploadProps = {
    name: 'files',
    multiple: true,
    accept: '.dcm,.dicom',
    customRequest: async ({ file, onSuccess, onError }) => {
      try {
        const files = new DataTransfer();
        files.items.add(file as File);
        
        const response: any = await imageAPI.upload(patientId, files.files);
        
        if (response.success) {
          message.success('上传成功');
          onSuccess?.(response);
          loadImages();
        }
      } catch (error) {
        message.error('上传失败');
        onError?.(error as Error);
      }
    },
  };

  // 运行AI分割
  const handleRunSegmentation = async (seriesId: number) => {
    setLoading(true);
    try {
      const response: any = await aiAPI.runSegmentation({
        series_id: seriesId,
        threshold: 0.5,
      });
      
      if (response.success) {
        message.success('AI分割完成');
        loadAIResults();
      }
    } catch (error) {
      console.error('AI分割失败:', error);
    } finally {
      setLoading(false);
    }
  };

  // AI结果表格列
  const aiResultColumns = [
    {
      title: '分析类型',
      dataIndex: 'analysis_type',
      key: 'analysis_type',
      render: (type: string) => (
        type === 'segmentation' ? '病灶分割' : '预后预测'
      ),
    },
    {
      title: '肿瘤体积',
      dataIndex: 'tumor_volume',
      key: 'tumor_volume',
      render: (volume: number) => volume ? `${volume.toFixed(2)} cm³` : '-',
    },
    {
      title: '预后评分',
      dataIndex: 'prognosis_score',
      key: 'prognosis_score',
      render: (score: number) => score ? score.toFixed(3) : '-',
    },
    {
      title: '风险等级',
      dataIndex: 'risk_level',
      key: 'risk_level',
      render: (level: string) => {
        const colorMap: any = { low: 'green', medium: 'orange', high: 'red' };
        const textMap: any = { low: '低风险', medium: '中风险', high: '高风险' };
        return level ? <Tag color={colorMap[level]}>{textMap[level]}</Tag> : '-';
      },
    },
    {
      title: '分析时间',
      dataIndex: 'created_at',
      key: 'created_at',
    },
  ];

  if (!patient) {
    return <div style={{ padding: 24 }}>加载中...</div>;
  }

  return (
    <div style={{ padding: '24px' }}>
      <Card title={`患者详情 - ${patient.name}`}>
        <Tabs defaultActiveKey="1">
          {/* 基本信息 */}
          <TabPane tab="基本信息" key="1">
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
          </TabPane>

          {/* 影像数据 */}
          <TabPane tab="影像数据" key="2">
            <div style={{ marginBottom: 16 }}>
              <Upload {...uploadProps}>
                <Button icon={<UploadOutlined />}>上传DICOM文件</Button>
              </Upload>
            </div>
            
            <Table
              dataSource={images}
              rowKey="id"
              columns={[
                { title: '序列UID', dataIndex: 'series_uid', key: 'series_uid' },
                { title: '成像方式', dataIndex: 'modality', key: 'modality' },
                { title: '序列描述', dataIndex: 'series_description', key: 'series_description' },
                { title: '文件数量', dataIndex: 'file_count', key: 'file_count' },
                { title: '上传时间', dataIndex: 'upload_time', key: 'upload_time' },
                {
                  title: '操作',
                  key: 'action',
                  render: (_, record) => (
                    <Button
                      type="primary"
                      size="small"
                      icon={<ThunderboltOutlined />}
                      onClick={() => handleRunSegmentation(record.id)}
                      loading={loading}
                    >
                      AI分割
                    </Button>
                  ),
                },
              ]}
            />
          </TabPane>

          {/* AI分析报告 */}
          <TabPane tab="AI分析报告" key="3">
            <Table
              dataSource={aiResults}
              rowKey="id"
              columns={aiResultColumns}
            />
          </TabPane>

          {/* 随访记录 */}
          <TabPane tab="随访记录" key="4">
            <div>随访记录功能待实现</div>
          </TabPane>
        </Tabs>
      </Card>
    </div>
  );
};

export default PatientDetail;

