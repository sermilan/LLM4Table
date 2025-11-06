import React, { useState, useEffect } from 'react'
import { Upload, Button, Table, message, Card, Space, Typography, Popconfirm, Modal, Descriptions, List, Row, Col, Statistic, Input, Pagination } from 'antd'
import { UploadOutlined, DeleteOutlined, EyeOutlined, SearchOutlined } from '@ant-design/icons'
import axios from 'axios'

const { Title } = Typography

const DataUpload = () => {
  const [fileList, setFileList] = useState([])
  const [dataTables, setDataTables] = useState([])
  const [loading, setLoading] = useState(false)
  const [detailModalVisible, setDetailModalVisible] = useState(false)
  const [selectedTable, setSelectedTable] = useState(null)
  const [tableData, setTableData] = useState([])
  const [filteredTableData, setFilteredTableData] = useState([])
  const [searchText, setSearchText] = useState('')
  const [currentPage, setCurrentPage] = useState(1)
  const [pageSize, setPageSize] = useState(10)
  const [totalRows, setTotalRows] = useState(0)
  const [loadingPreview, setLoadingPreview] = useState(false)

  // 获取已上传的数据表列表
  const fetchDataTables = async () => {
    try {
      setLoading(true)
      const response = await axios.get('/api/data/list')
      if (response.data.success) {
        setDataTables(response.data.data)
      }
    } catch (error) {
      message.error('获取数据表列表失败: ' + (error.response?.data?.detail || error.message))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchDataTables()
  }, [])

  // 当搜索文本改变时过滤数据
  useEffect(() => {
    if (!searchText) {
      setFilteredTableData(tableData)
      setTotalRows(tableData.length)
    } else {
      const filtered = tableData.filter(record => 
        Object.values(record).some(value => 
          String(value).toLowerCase().includes(searchText.toLowerCase())
        )
      )
      setFilteredTableData(filtered)
      setTotalRows(filtered.length)
    }
    setCurrentPage(1)
  }, [searchText, tableData])

  const handleUpload = async ({ file, onSuccess, onError }) => {
    try {
      const formData = new FormData()
      formData.append('file', file)
      formData.append('table_name', file.name.split('.')[0])
      formData.append('description', `Uploaded on ${new Date().toLocaleString()}`)

      const response = await axios.post('/api/data/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      })

      if (response.data.success) {
        message.success(`${file.name} 上传成功`)
        onSuccess(response.data, file)
        fetchDataTables() // 刷新数据表列表
      } else {
        message.error(`${file.name} 上传失败: ${response.data.message}`)
        onError(new Error(response.data.message))
      }
    } catch (error) {
      message.error(`${file.name} 上传失败: ` + (error.response?.data?.detail || error.message))
      onError(error)
    }
  }

  const handleDelete = async (tableId) => {
    try {
      const response = await axios.delete(`/api/data/${tableId}`)
      if (response.data.success) {
        message.success('数据表删除成功')
        fetchDataTables() // 刷新数据表列表
      } else {
        message.error('删除失败: ' + response.data.message)
      }
    } catch (error) {
      message.error('删除失败: ' + (error.response?.data?.detail || error.message))
    }
  }

  const columns = [
    {
      title: '表名',
      dataIndex: 'table_name',
      key: 'table_name',
    },
    {
      title: '文件名',
      dataIndex: 'file_name',
      key: 'file_name',
    },
    {
      title: '描述',
      dataIndex: 'description',
      key: 'description',
    },
    {
      title: '行数',
      dataIndex: 'row_count',
      key: 'row_count',
    },
    {
      title: '列数',
      dataIndex: 'column_count',
      key: 'column_count',
    },
    {
      title: '操作',
      key: 'action',
      render: (_, record) => (
        <Space size="middle">
          <Button icon={<EyeOutlined />} onClick={() => viewTableDetails(record.id)}>查看</Button>
          <Popconfirm
            title="确定要删除这个数据表吗？"
            onConfirm={() => handleDelete(record.id)}
            okText="确定"
            cancelText="取消"
          >
            <Button icon={<DeleteOutlined />} danger>删除</Button>
          </Popconfirm>
        </Space>
      ),
    },
  ]

  const viewTableDetails = async (tableId) => {
    try {
      // 获取数据表详细信息
      const response = await axios.get(`/api/data/${tableId}`)
      if (response.data.success) {
        setSelectedTable(response.data.data)
        
        // 获取实际的表格数据
        await loadTableData(tableId, 1, pageSize);
        
        setDetailModalVisible(true);
        setSearchText('');
        setCurrentPage(1);
      } else {
        message.error('获取数据表详情失败: ' + response.data.message);
      }
    } catch (error) {
      message.error('获取数据表详情失败: ' + (error.response?.data?.detail || error.message));
    }
  }

  // 加载表格数据
  const loadTableData = async (tableId, page, size) => {
    try {
      setLoadingPreview(true);
      const offset = (page - 1) * size;
      
      const previewResponse = await axios.get(`/api/data/${tableId}/preview`, {
        params: { 
          limit: size,
          offset: offset
        }
      });
      
      if (previewResponse.data.success) {
        setTableData(previewResponse.data.data.rows);
        setFilteredTableData(previewResponse.data.data.rows);
        setTotalRows(selectedTable?.row_count || 0);
      } else {
        setTableData([]);
        setFilteredTableData([]);
        setTotalRows(0);
      }
    } catch (previewError) {
      console.error('预览数据获取失败:', previewError);
      message.error('预览数据获取失败: ' + (previewError.response?.data?.detail || previewError.message));
      setTableData([]);
      setFilteredTableData([]);
      setTotalRows(0);
    } finally {
      setLoadingPreview(false);
    }
  }

  // 处理分页变化
  const handlePageChange = async (page, size) => {
    setCurrentPage(page);
    setPageSize(size);
    if (selectedTable) {
      await loadTableData(selectedTable.id, page, size);
    }
  }

  // 获取当前页的数据
  const getCurrentPageData = () => {
    const startIndex = (currentPage - 1) * pageSize;
    const endIndex = startIndex + pageSize;
    return filteredTableData.slice(startIndex, endIndex);
  }

  return (
    <div className="upload-container">
      <Card title="数据上传" style={{ marginBottom: 20 }}>
        <Upload
          customRequest={handleUpload}
          fileList={fileList}
          onChange={({ fileList }) => setFileList(fileList)}
          multiple={true}
        >
          <Button icon={<UploadOutlined />}>选择文件</Button>
        </Upload>
        <p style={{ marginTop: 10 }}>
          支持 CSV、Excel 文件格式，可上传多个相关联的数据表
        </p>
      </Card>

      <Card title="已上传数据表">
        <Table
          columns={columns}
          dataSource={dataTables}
          loading={loading}
          rowKey="id"
          pagination={{
            pageSize: 5,
          }}
        />
      </Card>

      {/* 数据表详情模态框 */}
      <Modal
        title="数据表详情"
        visible={detailModalVisible}
        onCancel={() => setDetailModalVisible(false)}
        footer={null}
        width={1200}
        height={800}
      >
        {selectedTable && (
          <>
            <Row gutter={16} style={{ marginBottom: 16 }}>
              <Col span={6}>
                <Statistic title="总行数" value={selectedTable.row_count} />
              </Col>
              <Col span={6}>
                <Statistic title="总列数" value={selectedTable.column_count} />
              </Col>
              <Col span={6}>
                <Statistic title="显示行数" value={filteredTableData.length} />
              </Col>
            </Row>
            
            <Descriptions title="基本信息" bordered column={2}>
              <Descriptions.Item label="表名">{selectedTable.table_name}</Descriptions.Item>
              <Descriptions.Item label="文件名">{selectedTable.file_name}</Descriptions.Item>
              <Descriptions.Item label="描述" span={2}>{selectedTable.description}</Descriptions.Item>
              <Descriptions.Item label="列名" span={2}>
                <List
                  dataSource={selectedTable.columns}
                  renderItem={item => <List.Item>{item}</List.Item>}
                  grid={{ column: 4 }}
                />
              </Descriptions.Item>
            </Descriptions>
            
            <div style={{ marginTop: 20 }}>
              <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between' }}>
                <h3>数据预览</h3>
                <div style={{ width: 300 }}>
                  <Input
                    placeholder="搜索数据..."
                    prefix={<SearchOutlined />}
                    value={searchText}
                    onChange={e => setSearchText(e.target.value)}
                  />
                </div>
              </div>
              
              <Table
                dataSource={getCurrentPageData()}
                columns={selectedTable.columns.map((col, index) => ({
                  title: col,
                  dataIndex: col,
                  key: col,
                  width: Math.min(300, Math.max(100, col.length * 12)),
                  ellipsis: true,
                  sorter: (a, b) => {
                    const aVal = a[col] || '';
                    const bVal = b[col] || '';
                    if (typeof aVal === 'number' && typeof bVal === 'number') {
                      return aVal - bVal;
                    }
                    return String(aVal).localeCompare(String(bVal));
                  }
                }))}
                pagination={false}
                scroll={{ y: 400, x: 'max-content' }}
                size="small"
                sticky
                loading={loadingPreview}
              />
              
              <div style={{ marginTop: 16, display: 'flex', justifyContent: 'flex-end' }}>
                <Pagination
                  current={currentPage}
                  pageSize={pageSize}
                  total={selectedTable.row_count}
                  onChange={handlePageChange}
                  showSizeChanger
                  showQuickJumper
                  showTotal={(total) => `共 ${total} 条数据`}
                />
              </div>
            </div>
          </>
        )}
      </Modal>
    </div>
  )
}

export default DataUpload