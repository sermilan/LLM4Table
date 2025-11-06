import React, { useState, useEffect } from 'react'
import { Card, Form, Select, InputNumber, Button, Table, message, Space, Tag, Progress, Modal, Descriptions, Collapse, Input, Row, Col, Switch } from 'antd'
import axios from 'axios'

const { Panel } = Collapse

const DataSynthesis = () => {
  const [form] = Form.useForm()
  const [dataTables, setDataTables] = useState([])
  const [synthesisTasks, setSynthesisTasks] = useState([])
  const [loading, setLoading] = useState(false)
  const [taskLoading, setTaskLoading] = useState(false)
  const [taskDetailModalVisible, setTaskDetailModalVisible] = useState(false)
  const [selectedTask, setSelectedTask] = useState(null)
  const [trainingParams, setTrainingParams] = useState({})

  // 获取已上传的数据表列表
  const fetchDataTables = async () => {
    try {
      setLoading(true)
      const response = await axios.get('/api/data/list')
      if (response.data.success) {
        setDataTables(response.data.data)
      } else {
        message.error('获取数据表列表失败: ' + response.data.message)
      }
    } catch (error) {
      console.error('获取数据表列表失败:', error)
      message.error('获取数据表列表失败: ' + (error.response?.data?.detail || error.message || '网络错误'))
    } finally {
      setLoading(false)
    }
  }

  // 获取合成任务列表
  const fetchSynthesisTasks = async () => {
    try {
      const response = await axios.get('/api/synthesis/tasks')
      if (response.data.success) {
        setSynthesisTasks(response.data.data)
      } else {
        message.error('获取合成任务列表失败: ' + response.data.message)
      }
    } catch (error) {
      console.error('获取合成任务列表失败:', error)
      message.error('获取合成任务列表失败: ' + (error.response?.data?.detail || error.message || '网络错误'))
    }
  }

  useEffect(() => {
    fetchDataTables()
    fetchSynthesisTasks()
    
    // 定期刷新任务状态
    const interval = setInterval(() => {
      fetchSynthesisTasks()
    }, 3000)
    
    return () => clearInterval(interval)
  }, [])

  const onFinish = async (values) => {
    try {
      setTaskLoading(true)
      
      // 获取当前模型配置
      const modelResponse = await axios.get('/api/model/current')
      if (!modelResponse.data.success) {
        message.error('请先配置模型')
        setTaskLoading(false)
        return
      }
      
      const requestData = {
        table_ids: values.table_ids,
        row_count: values.row_count,
        model_config: modelResponse.data.data,
        description: values.description,
        training_params: trainingParams
      }

      const response = await axios.post('/api/synthesis/generate', requestData)
      if (response.data.success) {
        message.success('合成任务已启动，请等待任务完成')
        fetchSynthesisTasks() // 刷新任务列表
      } else {
        message.error('启动合成任务失败: ' + response.data.message)
      }
    } catch (error) {
      console.error('启动合成任务失败:', error)
      message.error('启动合成任务失败: ' + (error.response?.data?.detail || error.message || '网络错误'))
    } finally {
      setTaskLoading(false)
    }
  }

  const getStatusTag = (status) => {
    switch (status) {
      case 'pending':
        return <Tag color="default">待处理</Tag>
      case 'training':
        return <Tag color="processing">训练中</Tag>
      case 'processing':
        return <Tag color="processing">处理中</Tag>
      case 'completed':
        return <Tag color="success">已完成</Tag>
      case 'failed':
        return <Tag color="error">失败</Tag>
      default:
        return <Tag>{status}</Tag>
    }
  }

  const viewTaskDetails = async (taskId) => {
    try {
      const response = await axios.get(`/api/synthesis/task/${taskId}`)
      if (response.data.success) {
        setSelectedTask(response.data.data)
        setTaskDetailModalVisible(true)
      } else {
        message.error('获取任务详情失败: ' + response.data.message)
      }
    } catch (error) {
      console.error('获取任务详情失败:', error)
      message.error('获取任务详情失败: ' + (error.response?.data?.detail || error.message || '网络错误'))
    }
  }

  const downloadResult = async (taskId) => {
    try {
      const response = await axios.get(`/api/synthesis/task/${taskId}/result`)
      if (response.data.success) {
        // 创建Blob对象
        const blob = new Blob([response.data.data.content], { type: 'text/csv;charset=utf-8;' });
        
        // 创建下载链接
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.setAttribute('download', response.data.data.file_name || `synthetic_data_${taskId}.csv`);
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);
      } else {
        message.error('获取下载内容失败: ' + response.data.message)
      }
    } catch (error) {
      console.error('下载失败:', error)
      message.error('下载失败: ' + (error.response?.data?.detail || error.message || '网络错误'))
    }
  }

  // 更新训练参数
  const updateTrainingParam = (key, value) => {
    setTrainingParams(prev => ({
      ...prev,
      [key]: value
    }))
  }

  // 渲染训练参数配置面板
  const renderTrainingParamsPanel = () => {
    return (
      <div>
        <Row gutter={16}>
          <Col span={12}>
            <Form.Item label="训练轮数">
              <InputNumber
                min={1}
                max={1000}
                value={trainingParams.epochs || 100}
                onChange={(value) => updateTrainingParam('epochs', value)}
                style={{ width: '100%' }}
              />
            </Form.Item>
          </Col>
          <Col span={12}>
            <Form.Item label="批次大小">
              <InputNumber
                min={1}
                max={1000}
                value={trainingParams.batch_size || 500}
                onChange={(value) => updateTrainingParam('batch_size', value)}
                style={{ width: '100%' }}
              />
            </Form.Item>
          </Col>
        </Row>
        <Row gutter={16}>
          <Col span={12}>
            <Form.Item label="学习率">
              <InputNumber
                min={0.0001}
                max={1}
                step={0.0001}
                value={trainingParams.learning_rate || 0.005}
                onChange={(value) => updateTrainingParam('learning_rate', value)}
                style={{ width: '100%' }}
              />
            </Form.Item>
          </Col>
          <Col span={12}>
            <Form.Item label="早停轮数">
              <InputNumber
                min={1}
                max={100}
                value={trainingParams.early_stopping_rounds || 10}
                onChange={(value) => updateTrainingParam('early_stopping_rounds', value)}
                style={{ width: '100%' }}
              />
            </Form.Item>
          </Col>
        </Row>
        <Row gutter={16}>
          <Col span={12}>
            <Form.Item label="启用早停">
              <Switch
                checked={trainingParams.early_stopping !== undefined ? trainingParams.early_stopping : true}
                onChange={(checked) => updateTrainingParam('early_stopping', checked)}
              />
            </Form.Item>
          </Col>
        </Row>
      </div>
    )
  }

  const taskColumns = [
    {
      title: '任务ID',
      dataIndex: 'task_id',
      key: 'task_id',
    },
    {
      title: '描述',
      dataIndex: 'description',
      key: 'description',
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status) => getStatusTag(status),
    },
    {
      title: '进度',
      dataIndex: 'progress',
      key: 'progress',
      render: (progress) => (
        <Progress percent={progress} size="small" />
      ),
    },
    {
      title: '操作',
      key: 'action',
      render: (_, record) => (
        <Space size="middle">
          <Button 
            size="small"
            onClick={() => viewTaskDetails(record.task_id)}
          >
            查看详情
          </Button>
          {record.status === 'completed' && (
            <Button 
              type="primary" 
              size="small"
              onClick={() => downloadResult(record.task_id)}
            >
              下载结果
            </Button>
          )}
        </Space>
      ),
    },
  ]

  return (
    <div className="synthesis-container">
      <Card title="数据合成" style={{ marginBottom: 20 }}>
        <Form
          form={form}
          layout="vertical"
          onFinish={onFinish}
        >
          <Form.Item
            name="table_ids"
            label="选择数据表"
            rules={[{ required: true, message: '请选择至少一个数据表' }]}
          >
            <Select
              mode="multiple"
              placeholder="请选择用于合成的数据表"
              optionFilterProp="children"
            >
              {dataTables.map(table => (
                <Select.Option key={table.id} value={table.id}>
                  {table.table_name}
                </Select.Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item
            name="row_count"
            label="生成行数"
            rules={[{ required: true, message: '请输入要生成的行数' }]}
          >
            <InputNumber min={1} max={100000} placeholder="请输入行数" style={{ width: '100%' }} />
          </Form.Item>

          <Collapse>
            <Panel header="模型训练参数（可选）" key="1">
              {renderTrainingParamsPanel()}
            </Panel>
          </Collapse>

          <Form.Item
            name="description"
            label="任务描述"
            style={{ marginTop: 16 }}
          >
            <input placeholder="请输入任务描述（可选）" style={{ width: '100%', padding: '4px 11px', borderRadius: '6px', border: '1px solid #d9d9d9' }} />
          </Form.Item>

          <Form.Item>
            <Button type="primary" htmlType="submit" loading={taskLoading}>
              开始合成
            </Button>
            <p style={{ marginTop: 8, color: '#888' }}>
              合成任务将在后台执行，请在任务列表中查看进度
            </p>
          </Form.Item>
        </Form>
      </Card>

      <Card title="合成任务">
        <Table
          columns={taskColumns}
          dataSource={synthesisTasks}
          loading={loading}
          rowKey="task_id"
          pagination={{
            pageSize: 5,
          }}
        />
      </Card>

      {/* 任务详情模态框 */}
      <Modal
        title="合成任务详情"
        visible={taskDetailModalVisible}
        onCancel={() => setTaskDetailModalVisible(false)}
        footer={null}
        width={600}
      >
        {selectedTask && (
          <Descriptions title="任务信息" bordered column={1}>
            <Descriptions.Item label="任务ID">{selectedTask.task_id}</Descriptions.Item>
            <Descriptions.Item label="状态">{getStatusTag(selectedTask.status)}</Descriptions.Item>
            <Descriptions.Item label="进度">
              <Progress percent={selectedTask.progress} />
            </Descriptions.Item>
            <Descriptions.Item label="描述">{selectedTask.description || '无描述'}</Descriptions.Item>
            {selectedTask.training_info && (
              <Descriptions.Item label="训练信息">
                <div>开始时间: {selectedTask.training_info.start_time || 'N/A'}</div>
                <div>结束时间: {selectedTask.training_info.end_time || 'N/A'}</div>
                <div>状态: {selectedTask.training_info.status || 'N/A'}</div>
                {selectedTask.training_info.current_step && (
                  <div>当前步骤: {selectedTask.training_info.current_step}</div>
                )}
              </Descriptions.Item>
            )}
            {selectedTask.error_message && (
              <Descriptions.Item label="错误信息">
                <span style={{ color: 'red' }}>{selectedTask.error_message}</span>
              </Descriptions.Item>
            )}
            {selectedTask.result_path && (
              <Descriptions.Item label="结果文件路径">{selectedTask.result_path}</Descriptions.Item>
            )}
            <Descriptions.Item label="创建时间">{selectedTask.created_at || '未知'}</Descriptions.Item>
          </Descriptions>
        )}
      </Modal>
    </div>
  )
}

export default DataSynthesis