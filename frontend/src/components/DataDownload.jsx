import React, { useState, useEffect } from 'react'
import { Card, Table, Button, message, Space, Tag, Modal, Descriptions, Input, Row, Col, Statistic } from 'antd'
import { DownloadOutlined, EyeOutlined, SearchOutlined } from '@ant-design/icons'
import axios from 'axios'

const DataDownload = () => {
  const [synthesisTasks, setSynthesisTasks] = useState([])
  const [loading, setLoading] = useState(false)
  const [previewVisible, setPreviewVisible] = useState(false)
  const [previewContent, setPreviewContent] = useState('')
  const [previewTitle, setPreviewTitle] = useState('')
  const [tableData, setTableData] = useState([])
  const [tableColumns, setTableColumns] = useState([])
  const [filteredTableData, setFilteredTableData] = useState([])
  const [searchText, setSearchText] = useState('')

  // 获取合成任务列表
  const fetchSynthesisTasks = async () => {
    try {
      setLoading(true)
      const response = await axios.get('/api/synthesis/tasks')
      if (response.data.success) {
        setSynthesisTasks(response.data.data)
      } else {
        message.error('获取合成任务列表失败: ' + response.data.message)
      }
    } catch (error) {
      console.error('获取合成任务列表失败:', error)
      message.error('获取合成任务列表失败: ' + (error.response?.data?.detail || error.message || '网络错误'))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchSynthesisTasks()
  }, [])

  // 当搜索文本改变时过滤数据
  useEffect(() => {
    if (!searchText) {
      setFilteredTableData(tableData)
    } else {
      const filtered = tableData.filter(record => 
        Object.values(record).some(value => 
          String(value).toLowerCase().includes(searchText.toLowerCase())
        )
      )
      setFilteredTableData(filtered)
    }
  }, [searchText, tableData])

  const getStatusTag = (status) => {
    switch (status) {
      case 'pending':
        return <Tag color="default">待处理</Tag>
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

  const previewResult = async (taskId) => {
    try {
      const response = await axios.get(`/api/synthesis/task/${taskId}/result`)
      if (response.data.success) {
        // 解析CSV内容为表格数据
        const csvContent = response.data.data.content;
        const lines = csvContent.split('\n').filter(line => line.trim() !== '');
        
        if (lines.length > 0) {
          // 解析表头
          const headers = lines[0].split(',').map(header => header.trim().replace(/"/g, ''));
          const columns = headers.map((header, index) => ({
            title: header,
            dataIndex: header,
            key: `${header}_${index}`,
            sorter: (a, b) => {
              const aVal = a[header] || '';
              const bVal = b[header] || '';
              return aVal.toString().localeCompare(bVal.toString());
            },
            // 添加列宽控制
            width: Math.min(200, Math.max(100, header.length * 12)),
            ellipsis: true
          }));
          
          // 解析数据行
          const data = [];
          for (let i = 1; i < lines.length; i++) {
            const values = lines[i].split(',').map(value => value.trim().replace(/"/g, ''));
            if (values.length === headers.length) {
              const row = {};
              headers.forEach((header, index) => {
                row[header] = values[index];
              });
              data.push({ ...row, key: i });
            }
          }
          
          setTableColumns(columns);
          setTableData(data);
          setFilteredTableData(data);
          setPreviewTitle(response.data.data.file_name || `synthetic_data_${taskId}.csv`);
          setPreviewVisible(true);
          setSearchText('');
        } else {
          // 如果无法解析为表格，显示原始内容
          setPreviewContent(csvContent);
          setPreviewTitle(response.data.data.file_name || `synthetic_data_${taskId}.csv`);
          setPreviewVisible(true);
        }
      } else {
        message.error('获取预览内容失败: ' + response.data.message)
      }
    } catch (error) {
      console.error('预览失败:', error)
      message.error('预览失败: ' + (error.response?.data?.detail || error.message || '网络错误'))
    }
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
      title: '操作',
      key: 'action',
      render: (_, record) => (
        <Space size="middle">
          {record.status === 'completed' && (
            <>
              <Button 
                type="primary" 
                icon={<DownloadOutlined />}
                onClick={() => downloadResult(record.task_id)}
              >
                下载
              </Button>
              <Button 
                icon={<EyeOutlined />}
                onClick={() => previewResult(record.task_id)}
              >
                预览
              </Button>
            </>
          )}
        </Space>
      ),
    },
  ]

  return (
    <div className="download-container">
      <Card title="合成数据下载">
        <Table
          columns={taskColumns}
          dataSource={synthesisTasks}
          loading={loading}
          rowKey="task_id"
          pagination={{
            pageSize: 10,
          }}
        />
      </Card>

      {/* 预览模态框 */}
      <Modal
        title={`数据预览 - ${previewTitle}`}
        visible={previewVisible}
        onCancel={() => setPreviewVisible(false)}
        onOk={() => setPreviewVisible(false)}
        width={1200}
        height={700}
        footer={[
          <Button key="close" onClick={() => setPreviewVisible(false)}>
            关闭
          </Button>
        ]}
      >
        {tableColumns.length > 0 && tableData.length > 0 ? (
          <>
            {/* 数据统计信息 */}
            <Row gutter={16} style={{ marginBottom: 16 }}>
              <Col span={6}>
                <Statistic title="总行数" value={tableData.length} />
              </Col>
              <Col span={6}>
                <Statistic title="总列数" value={tableColumns.length} />
              </Col>
            </Row>
            
            {/* 搜索框 */}
            <div style={{ marginBottom: 16 }}>
              <Input
                placeholder="搜索数据..."
                prefix={<SearchOutlined />}
                value={searchText}
                onChange={e => setSearchText(e.target.value)}
                style={{ width: 300 }}
              />
            </div>
            
            {/* 表格数据 */}
            <Table
              columns={tableColumns}
              dataSource={filteredTableData}
              pagination={{ 
                pageSize: 15,
                showSizeChanger: true,
                pageSizeOptions: ['10', '15', '20', '50']
              }}
              scroll={{ y: 400, x: 'max-content' }}
              size="middle"
              sticky
            />
          </>
        ) : (
          <div style={{ maxHeight: '400px', overflow: 'auto' }}>
            <pre style={{ 
              whiteSpace: 'pre-wrap', 
              wordWrap: 'break-word',
              backgroundColor: '#f5f5f5',
              padding: '10px',
              borderRadius: '4px',
              fontSize: '12px',
              fontFamily: 'monospace'
            }}>
              {previewContent}
            </pre>
          </div>
        )}
      </Modal>
    </div>
  )
}

export default DataDownload