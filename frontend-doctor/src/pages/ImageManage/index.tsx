/**
 * 影像管理页面
 */
import React, { useState, useEffect, useCallback } from 'react';
import { Card, Table, Button, Space, Tag, message, Upload, Select, Input, Statistic, Row, Col } from 'antd';
import { UploadOutlined, EyeOutlined, ThunderboltOutlined, RobotOutlined, ReloadOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { imageAPI, patientAPI, aiAPI, medgemmaAPI } from '../../services/api';
import type { UploadProps } from 'antd';

const ImageManage: React.FC = () => {
  const navigate = useNavigate();
  const [patients, setPatients] = useState<any[]>([]);
  const [selectedPatient, setSelectedPatient] = useState<number | null>(null);
  const [images, setImages] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [actionLoading, setActionLoading] = useState<number | null>(null);

  const loadPatients = useCallback(async () => {
    try {
      const res: any = await patientAPI.list({ page: 1, page_size: 200 });
      if (res.success) setPatients(res.data.items || []);
    } catch { /* interceptor */ }
  }, []);

  const loadImages = useCallback(async () => {
    if (!selectedPatient) { setImages([]); return; }
    setLoading(true);
    try {
      const res: any = await imageAPI.getPatientImages(selectedPatient);
      if (res.success) setImages(res.data || []);
    } catch { /* interceptor */ }
    finally { setLoading(false); }
  }, [selectedPatient]);

  useEffect(() => { loadPatients(); }, [loadPatients]);
  useEffect(() => { loadImages(); }, [loadImages]);

  const handleSegmentation = async (seriesId: number) => {
    setActionLoading(seriesId);
    try {
      const res: any = await aiAPI.runSegmentation({ series_id: seriesId });
      if (res.success) message.success('U-Net 分割完成');
    } catch { /* interceptor */ }
    finally { setActionLoading(null); }
  };

  const handleMedGemma = async (seriesId: number) => {
    if (!selectedPatient) return;
    setActionLoading(seriesId);
    try {
      const res: any = await medgemmaAPI.analyzeImage({ series_id: seriesId, patient_id: selectedPatient });
      if (res.success) message.success('MedGemma 分析完成');
    } catch { /* interceptor */ }
    finally { setActionLoading(null); }
  };

  const uploadProps: UploadProps = {
    name: 'files',
    multiple: true,
    accept: '.dcm,.dicom',
    disabled: !selectedPatient,
    customRequest: async ({ file, onSuccess, onError }) => {
      if (!selectedPatient) return;
      try {
        const dt = new DataTransfer();
        dt.items.add(file as File);
        const res: any = await imageAPI.upload(selectedPatient, dt.files);
        if (res.success) { message.success('上传成功'); onSuccess?.(res); loadImages(); }
      } catch (e) { message.error('上传失败'); onError?.(e as Error); }
    },
  };

  const columns = [
    { title: '序列 UID', dataIndex: 'series_uid', key: 'series_uid', ellipsis: true },
    { title: '成像方式', dataIndex: 'modality', key: 'modality', width: 100 },
    { title: '序列描述', dataIndex: 'series_description', key: 'series_description', ellipsis: true },
    { title: '文件数', dataIndex: 'file_count', key: 'file_count', width: 80 },
    {
      title: '层厚',
      dataIndex: 'slice_thickness',
      key: 'slice_thickness',
      width: 80,
      render: (v: number) => v ? `${v} mm` : '-',
    },
    { title: '上传时间', dataIndex: 'upload_time', key: 'upload_time', width: 170 },
    {
      title: '操作',
      key: 'action',
      width: 320,
      render: (_: any, record: any) => (
        <Space>
          <Button size="small" icon={<EyeOutlined />} onClick={() => navigate(`/patients/${selectedPatient}`)}>
            详情
          </Button>
          <Button
            size="small"
            icon={<ThunderboltOutlined />}
            loading={actionLoading === record.id}
            onClick={() => handleSegmentation(record.id)}
          >
            U-Net
          </Button>
          <Button
            type="primary"
            size="small"
            icon={<RobotOutlined />}
            loading={actionLoading === record.id}
            onClick={() => handleMedGemma(record.id)}
          >
            MedGemma
          </Button>
        </Space>
      ),
    },
  ];

  return (
    <div style={{ padding: 24 }}>
      <Card
        title="影像管理"
        extra={
          <Space>
            <Select
              showSearch
              allowClear
              placeholder="选择患者"
              style={{ width: 260 }}
              optionFilterProp="label"
              value={selectedPatient}
              onChange={setSelectedPatient}
              options={patients.map((p) => ({ value: p.id, label: `${p.patient_no} - ${p.name}` }))}
            />
            <Upload {...uploadProps}>
              <Button icon={<UploadOutlined />} disabled={!selectedPatient}>上传 DICOM</Button>
            </Upload>
            <Button icon={<ReloadOutlined />} onClick={loadImages}>刷新</Button>
          </Space>
        }
      >
        <Row gutter={16} style={{ marginBottom: 16 }}>
          <Col span={6}><Statistic title="影像序列总数" value={images.length} /></Col>
          <Col span={6}><Statistic title="MRI 序列" value={images.filter((i) => i.modality === 'MR').length} /></Col>
          <Col span={6}><Statistic title="CT 序列" value={images.filter((i) => i.modality === 'CT').length} /></Col>
          <Col span={6}><Statistic title="其他" value={images.filter((i) => !['MR', 'CT'].includes(i.modality)).length} /></Col>
        </Row>
        <Table columns={columns} dataSource={images} rowKey="id" loading={loading} scroll={{ x: 1000 }} />
      </Card>
    </div>
  );
};

export default ImageManage;
