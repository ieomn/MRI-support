/**
 * 患者列表页面 (F-CD-01)
 */
import React, { useState, useEffect } from 'react';
import {
  Card,
  Table,
  Button,
  Input,
  Space,
  Tag,
  Modal,
  Form,
  Select,
  DatePicker,
  message,
} from 'antd';
import {
  PlusOutlined,
  SearchOutlined,
  EditOutlined,
  DeleteOutlined,
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { patientAPI, Patient, PatientCreateData } from '../../services/api';
import type { ColumnsType } from 'antd/es/table';

const { Search } = Input;
const { Option } = Select;

const PatientList: React.FC = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [patients, setPatients] = useState<Patient[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [keyword, setKeyword] = useState('');
  const [createModalVisible, setCreateModalVisible] = useState(false);
  const [form] = Form.useForm();

  // 加载患者列表
  const loadPatients = async () => {
    setLoading(true);
    try {
      const response: any = await patientAPI.list({
        page,
        page_size: pageSize,
        keyword: keyword || undefined,
      });
      
      if (response.success) {
        setPatients(response.data.items);
        setTotal(response.data.total);
      }
    } catch (error) {
      console.error('加载患者列表失败:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadPatients();
  }, [page, pageSize, keyword]);

  // 表格列定义
  const columns: ColumnsType<Patient> = [
    {
      title: '患者编号',
      dataIndex: 'patient_no',
      key: 'patient_no',
      width: 150,
    },
    {
      title: '姓名',
      dataIndex: 'name',
      key: 'name',
      width: 100,
    },
    {
      title: '性别',
      dataIndex: 'gender',
      key: 'gender',
      width: 80,
      render: (gender: string) => (
        <Tag color={gender === 'female' ? 'pink' : 'blue'}>
          {gender === 'female' ? '女' : '男'}
        </Tag>
      ),
    },
    {
      title: '年龄',
      dataIndex: 'age',
      key: 'age',
      width: 80,
    },
    {
      title: '联系电话',
      dataIndex: 'phone',
      key: 'phone',
      width: 130,
    },
    {
      title: '所属医院',
      dataIndex: 'hospital',
      key: 'hospital',
      width: 150,
    },
    {
      title: '诊断',
      dataIndex: 'diagnosis',
      key: 'diagnosis',
      ellipsis: true,
    },
    {
      title: '分期',
      dataIndex: 'stage',
      key: 'stage',
      width: 80,
      render: (stage: string) => (
        stage ? <Tag color="orange">{stage}</Tag> : '-'
      ),
    },
    {
      title: '操作',
      key: 'action',
      width: 150,
      fixed: 'right',
      render: (_, record) => (
        <Space size="small">
          <Button
            type="link"
            size="small"
            onClick={() => navigate(`/patients/${record.id}`)}
          >
            查看
          </Button>
          <Button
            type="link"
            size="small"
            icon={<EditOutlined />}
            onClick={() => handleEdit(record)}
          >
            编辑
          </Button>
          <Button
            type="link"
            danger
            size="small"
            icon={<DeleteOutlined />}
            onClick={() => handleDelete(record)}
          >
            删除
          </Button>
        </Space>
      ),
    },
  ];

  // 创建患者
  const handleCreate = async () => {
    try {
      const values = await form.validateFields();
      const data: PatientCreateData = {
        ...values,
        birth_date: values.birth_date?.format('YYYY-MM-DD'),
        admission_date: values.admission_date?.format('YYYY-MM-DD'),
      };
      
      const response: any = await patientAPI.create(data);
      
      if (response.success) {
        message.success('患者创建成功');
        setCreateModalVisible(false);
        form.resetFields();
        loadPatients();
      }
    } catch (error) {
      console.error('创建患者失败:', error);
    }
  };

  // 编辑患者
  const handleEdit = (patient: Patient) => {
    // TODO: 实现编辑功能
    message.info('编辑功能待实现');
  };

  // 删除患者
  const handleDelete = (patient: Patient) => {
    Modal.confirm({
      title: '确认删除',
      content: `确定要删除患者 ${patient.name} 吗？`,
      okText: '确认',
      cancelText: '取消',
      onOk: async () => {
        try {
          await patientAPI.delete(patient.id);
          message.success('删除成功');
          loadPatients();
        } catch (error) {
          console.error('删除失败:', error);
        }
      },
    });
  };

  return (
    <div style={{ padding: '24px' }}>
      <Card>
        <Space style={{ marginBottom: 16, width: '100%', justifyContent: 'space-between' }}>
          <Search
            placeholder="搜索患者姓名或编号"
            allowClear
            style={{ width: 300 }}
            onSearch={setKeyword}
            enterButton={<SearchOutlined />}
          />
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => setCreateModalVisible(true)}
          >
            新建患者
          </Button>
        </Space>

        <Table
          columns={columns}
          dataSource={patients}
          rowKey="id"
          loading={loading}
          scroll={{ x: 1200 }}
          pagination={{
            current: page,
            pageSize,
            total,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total) => `共 ${total} 条`,
            onChange: (page, pageSize) => {
              setPage(page);
              setPageSize(pageSize);
            },
          }}
        />
      </Card>

      {/* 创建患者模态框 */}
      <Modal
        title="新建患者"
        open={createModalVisible}
        onOk={handleCreate}
        onCancel={() => {
          setCreateModalVisible(false);
          form.resetFields();
        }}
        width={600}
      >
        <Form form={form} layout="vertical">
          <Form.Item
            name="name"
            label="姓名"
            rules={[{ required: true, message: '请输入姓名' }]}
          >
            <Input placeholder="请输入患者姓名" />
          </Form.Item>

          <Form.Item
            name="gender"
            label="性别"
            rules={[{ required: true, message: '请选择性别' }]}
          >
            <Select placeholder="请选择性别">
              <Option value="female">女</Option>
              <Option value="male">男</Option>
            </Select>
          </Form.Item>

          <Form.Item name="birth_date" label="出生日期">
            <DatePicker style={{ width: '100%' }} />
          </Form.Item>

          <Form.Item name="phone" label="联系电话">
            <Input placeholder="请输入联系电话" />
          </Form.Item>

          <Form.Item name="address" label="家庭地址">
            <Input.TextArea placeholder="请输入家庭地址" rows={2} />
          </Form.Item>

          <Form.Item name="hospital" label="所属医院">
            <Input placeholder="请输入所属医院" />
          </Form.Item>

          <Form.Item name="admission_date" label="入院日期">
            <DatePicker style={{ width: '100%' }} />
          </Form.Item>

          <Form.Item name="diagnosis" label="诊断结果">
            <Input.TextArea placeholder="请输入诊断结果" rows={3} />
          </Form.Item>

          <Form.Item name="stage" label="分期">
            <Select placeholder="请选择分期">
              <Option value="I">I期</Option>
              <Option value="II">II期</Option>
              <Option value="III">III期</Option>
              <Option value="IV">IV期</Option>
            </Select>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default PatientList;

