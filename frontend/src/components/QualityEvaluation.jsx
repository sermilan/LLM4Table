import React, { useState, useEffect } from 'react'
import { Card, Form, Select, Button, Table, message, Space, Tag, Upload, Descriptions, Input, Tabs, Spin, Radio, Progress, Row, Col, Tooltip } from 'antd'
import { UploadOutlined, BarChartOutlined, PieChartOutlined, LineChartOutlined } from '@ant-design/icons'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, Legend, ResponsiveContainer, LineChart, Line, Cell, ScatterChart, Scatter, ZAxis, RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis } from 'recharts'
import axios from 'axios'

const { TabPane } = Tabs

const QualityEvaluation = () => {
  const [form] = Form.useForm()
  const [dataTables, setDataTables] = useState([])
  const [synthesisTasks, setSynthesisTasks] = useState([])
  const [evaluationResult, setEvaluationResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [fileList, setFileList] = useState([])
  const [activeTab, setActiveTab] = useState('1')
  const [chartType, setChartType] = useState('overview') // 默认显示整体概览
  const [selectedTables, setSelectedTables] = useState([]) // 保存选中的数据表

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
  }, [])

  // 处理原始数据表选择变化
  const handleTableSelectionChange = (selectedTableIds) => {
    // 保存选中的数据表
    setSelectedTables(selectedTableIds)
    
    // 根据选择的原始数据表，过滤相关的合成任务
    // 这里可以根据需要实现过滤逻辑
  }

  const onFinish = async (values) => {
    try {
      setLoading(true)
      
      // 检查是否选择了文件或路径
      if (!values.synthetic_data_path && (!fileList || fileList.length === 0)) {
        message.error('请上传合成数据文件或选择合成任务结果')
        setLoading(false)
        return
      }
      
      let syntheticDataPath = values.synthetic_data_path
      
      // 如果有上传的文件，使用上传的文件路径
      if (fileList && fileList.length > 0 && fileList[0].response) {
        syntheticDataPath = fileList[0].response.data.file_path
      }
      
      const requestData = {
        original_table_ids: values.original_table_ids,
        synthetic_data_path: syntheticDataPath
      }

      const response = await axios.post('/api/evaluation/evaluate', requestData)
      if (response.data.success) {
        message.success('数据质量评估完成')
        setEvaluationResult(response.data.data)
        setActiveTab('2') // 切换到结果标签页
      } else {
        message.error('数据质量评估失败: ' + response.data.message)
      }
    } catch (error) {
      console.error('数据质量评估失败:', error)
      message.error('数据质量评估失败: ' + (error.response?.data?.detail || error.message || '网络错误'))
    } finally {
      setLoading(false)
    }
  }

  const handleUpload = async ({ file, onSuccess, onError }) => {
    try {
      setUploading(true)
      const formData = new FormData()
      formData.append('synthetic_file', file)
      formData.append('original_table_ids', JSON.stringify(form.getFieldValue('original_table_ids') || []))

      const response = await axios.post('/api/evaluation/evaluate/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      })

      if (response.data.success) {
        message.success(`${file.name} 上传并评估成功`)
        onSuccess(response.data, file)
        setEvaluationResult(response.data.data)
        setFileList([{
          uid: file.uid,
          name: file.name,
          status: 'done',
          response: response.data
        }])
        setActiveTab('2') // 切换到结果标签页
      } else {
        message.error(`${file.name} 评估失败: ${response.data.message}`)
        onError(new Error(response.data.message))
      }
    } catch (error) {
      console.error(`${file.name} 评估失败:`, error)
      message.error(`${file.name} 评估失败: ` + (error.response?.data?.detail || error.message || '网络错误'))
      onError(error)
    } finally {
      setUploading(false)
    }
  }

  // 获取与选中数据表相关的合成任务
  const getRelatedTasks = (tableIds) => {
    if (!tableIds || tableIds.length === 0) return []
    
    // 筛选出包含选中的数据表的合成任务
    return synthesisTasks.filter(task => {
      // 检查任务是否包含选中的数据表
      return task.table_ids && task.table_ids.some(id => tableIds.includes(id)) && task.status === 'completed'
    })
  }

  const getScoreTag = (score) => {
    if (score >= 0.8) {
      return <Tag color="success">{(score * 100).toFixed(1)}%</Tag>
    } else if (score >= 0.6) {
      return <Tag color="warning">{(score * 100).toFixed(1)}%</Tag>
    } else {
      return <Tag color="error">{(score * 100).toFixed(1)}%</Tag>
    }
  }

  // 渲染柱状图
  const renderBarChart = (data, title, dataKey) => {
    return (
      <ResponsiveContainer width="100%" height={300}>
        <BarChart
          data={data}
          margin={{
            top: 5,
            right: 30,
            left: 20,
            bottom: 5,
          }}
        >
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="name" />
          <YAxis domain={[0, 1]} />
          <RechartsTooltip formatter={(value) => [(value * 100).toFixed(1) + '%', '得分']} />
          <Legend />
          <Bar dataKey="value" name={title}>
            {data.map((entry, index) => (
              <Cell 
                key={`cell-${index}`} 
                fill={entry.value >= 0.8 ? '#52c41a' : entry.value >= 0.6 ? '#faad14' : '#ff4d4f'} 
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    );
  }

  // 渲染折线图
  const renderLineChart = (data, title) => {
    return (
      <ResponsiveContainer width="100%" height={300}>
        <LineChart
          data={data}
          margin={{
            top: 5,
            right: 30,
            left: 20,
            bottom: 5,
          }}
        >
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="name" />
          <YAxis domain={[0, 1]} />
          <RechartsTooltip formatter={(value) => [(value * 100).toFixed(1) + '%', '得分']} />
          <Legend />
          <Line 
            type="monotone" 
            dataKey="value" 
            name={title} 
            stroke="#1890ff" 
            activeDot={{ r: 8 }} 
          />
        </LineChart>
      </ResponsiveContainer>
    );
  }
  
  // 渲染雷达图
  const renderRadarChart = () => {
    if (!evaluationResult) return null;
    
    // 准备雷达图数据
    const radarData = [
      {
        subject: '整体质量',
        A: evaluationResult.overall_quality,
        fullMark: 1
      },
      {
        subject: '相似度',
        A: evaluationResult.similarity_score,
        fullMark: 1
      },
      {
        subject: '隐私保护',
        A: evaluationResult.privacy_score,
        fullMark: 1
      },
      {
        subject: '分布相似度',
        A: Object.values(evaluationResult.distribution_similarity || {}).reduce((sum, val) => sum + val, 0) / 
           Object.keys(evaluationResult.distribution_similarity || {}).length || 0,
        fullMark: 1
      },
      {
        subject: '特征保持度',
        A: Object.values(evaluationResult.column_correlations || {}).reduce((sum, val) => sum + val, 0) / 
           Object.keys(evaluationResult.column_correlations || {}).length || 0,
        fullMark: 1
      }
    ];
    
    return (
      <div className="radar-chart-container">
        <ResponsiveContainer width="100%" height="100%">
          <RadarChart cx="50%" cy="50%" outerRadius="80%" data={radarData}>
            <PolarGrid />
            <PolarAngleAxis dataKey="subject" />
            <PolarRadiusAxis domain={[0, 1]} />
            <Radar
              name="质量指标"
              dataKey="A"
              stroke="#8884d8"
              fill="#8884d8"
              fillOpacity={0.6}
            />
            <RechartsTooltip formatter={(value) => [(value * 100).toFixed(1) + '%', '得分']} />
          </RadarChart>
        </ResponsiveContainer>
      </div>
    );
  }

  // 渲染热力图
  const renderHeatmap = (correlationData, distributionData) => {
    // 准备热力图数据
    const heatmapData = [];
    const columns = [...new Set([...correlationData.map(d => d.name), ...distributionData.map(d => d.name)])];
    
    columns.forEach(col => {
      const correlationItem = correlationData.find(d => d.name === col);
      const distributionItem = distributionData.find(d => d.name === col);
      
      heatmapData.push({
        name: col,
        correlation: correlationItem ? correlationItem.value : 0,
        distribution: distributionItem ? distributionItem.value : 0
      });
    });
    
    // 获取颜色基于值
    const getColor = (value) => {
      if (value >= 0.8) return '#52c41a'; // 绿色
      if (value >= 0.6) return '#faad14'; // 黄色
      return '#ff4d4f'; // 红色
    };
    
    // 检查是否有SDMetrics热力图数据
    const hasSDMetricsData = evaluationResult && 
      evaluationResult.visualization_data && 
      evaluationResult.visualization_data.sdmetrics_heatmap_data;
      
    const sdmetricsData = hasSDMetricsData ? evaluationResult.visualization_data.sdmetrics_heatmap_data : null;
    const hasColumnSimilarity = sdmetricsData && sdmetricsData.column_similarity;
    const hasColumnPairTrends = sdmetricsData && sdmetricsData.column_pair_trends && sdmetricsData.column_pair_trends.success;
    
    return (
      <div style={{ height: '400px', overflow: 'auto' }}>
        {/* 原始热力图 */}
        <h4>数据质量热力图</h4>
        <table style={{ width: '100%', borderCollapse: 'collapse', marginBottom: '20px' }}>
          <thead>
            <tr>
              <th style={{ border: '1px solid #f0f0f0', padding: '8px', textAlign: 'left', backgroundColor: '#fafafa' }}>列名</th>
              <th style={{ border: '1px solid #f0f0f0', padding: '8px', textAlign: 'center', backgroundColor: '#fafafa' }}>相关性</th>
              <th style={{ border: '1px solid #f0f0f0', padding: '8px', textAlign: 'center', backgroundColor: '#fafafa' }}>分布相似度</th>
            </tr>
          </thead>
          <tbody>
            {heatmapData.map((item, index) => (
              <tr key={index}>
                <td style={{ border: '1px solid #f0f0f0', padding: '8px' }}>{item.name}</td>
                <td style={{ border: '1px solid #f0f0f0', padding: '8px', textAlign: 'center' }}>
                  <Tooltip title={`${(item.correlation * 100).toFixed(1)}%`}>
                    <div 
                      style={{ 
                        backgroundColor: getColor(item.correlation), 
                        height: '20px', 
                        width: `${item.correlation * 100}%`, 
                        minWidth: '20px',
                        borderRadius: '4px',
                        margin: '0 auto'
                      }}
                    />
                  </Tooltip>
                </td>
                <td style={{ border: '1px solid #f0f0f0', padding: '8px', textAlign: 'center' }}>
                  <Tooltip title={`${(item.distribution * 100).toFixed(1)}%`}>
                    <div 
                      style={{ 
                        backgroundColor: getColor(item.distribution), 
                        height: '20px', 
                        width: `${item.distribution * 100}%`, 
                        minWidth: '20px',
                        borderRadius: '4px',
                        margin: '0 auto'
                      }}
                    />
                  </Tooltip>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        
        {/* SDMetrics列相似性热力图 */}
        {hasColumnSimilarity && (
          <div>
            <h4>SDMetrics列相似性热力图</h4>
            <table style={{ width: '100%', borderCollapse: 'collapse', marginBottom: '20px' }}>
              <thead>
                <tr>
                  <th style={{ border: '1px solid #f0f0f0', padding: '8px', textAlign: 'left', backgroundColor: '#fafafa' }}>列名</th>
                  <th style={{ border: '1px solid #f0f0f0', padding: '8px', textAlign: 'center', backgroundColor: '#fafafa' }}>类型</th>
                  <th style={{ border: '1px solid #f0f0f0', padding: '8px', textAlign: 'center', backgroundColor: '#fafafa' }}>相似性得分</th>
                  <th style={{ border: '1px solid #f0f0f0', padding: '8px', textAlign: 'center', backgroundColor: '#fafafa' }}>热力图</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(sdmetricsData.column_similarity).map(([column, data], index) => (
                  <tr key={index}>
                    <td style={{ border: '1px solid #f0f0f0', padding: '8px' }}>{column}</td>
                    <td style={{ border: '1px solid #f0f0f0', padding: '8px', textAlign: 'center' }}>
                      <Tag color={
                        data.type === 'numerical' ? 'blue' : 
                        data.type === 'categorical' ? 'green' : 
                        data.type === 'datetime' ? 'purple' : 'default'
                      }>
                        {data.type}
                      </Tag>
                    </td>
                    <td style={{ border: '1px solid #f0f0f0', padding: '8px', textAlign: 'center' }}>
                      <Tooltip title={`${(data.similarity_score * 100).toFixed(1)}%`}>
                        <span>{(data.similarity_score * 100).toFixed(1)}%</span>
                      </Tooltip>
                    </td>
                    <td style={{ border: '1px solid #f0f0f0', padding: '8px', textAlign: 'center' }}>
                      <Tooltip title={`${(data.similarity_score * 100).toFixed(1)}%`}>
                        <div 
                          style={{ 
                            backgroundColor: getColor(data.similarity_score), 
                            height: '20px', 
                            width: `${data.similarity_score * 100}%`, 
                            minWidth: '20px',
                            borderRadius: '4px',
                            margin: '0 auto'
                          }}
                        />
                      </Tooltip>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        
        {/* SDMetrics列对趋势热力图 */}
        {hasColumnPairTrends && (
          <div>
            <h4>SDMetrics列对趋势热力图 (Column Pair Trends)</h4>
            <div style={{ overflow: 'auto', maxHeight: '300px' }}>
              {renderColumnPairTrendsHeatmap(sdmetricsData.column_pair_trends)}
            </div>
          </div>
        )}
      </div>
    );
  }
  
  // 渲染列对趋势热力图
  const renderColumnPairTrendsHeatmap = (pairTrendsData) => {
    if (!pairTrendsData || !pairTrendsData.success) {
      return <div>暂无列对趋势数据</div>;
    }
    
    const { numerical_columns, similarity_scores } = pairTrendsData;
    
    if (!numerical_columns || numerical_columns.length === 0) {
      return <div>无数值列用于相关性分析</div>;
    }
    
    // 转换相似度数据为数组格式
    const heatmapRows = [];
    numerical_columns.forEach((rowCol, rowIndex) => {
      const row = { name: rowCol };
      numerical_columns.forEach((colCol, colIndex) => {
        const score = similarity_scores[rowCol][colCol];
        row[colCol] = score;
      });
      heatmapRows.push(row);
    });
    
    // 获取颜色基于值
    const getHeatmapColor = (value) => {
      // 使用渐变色：红色(0) -> 黄色(0.5) -> 绿色(1)
      if (value >= 0.8) return '#52c41a'; // 绿色
      if (value >= 0.6) return '#faad14'; // 黄色
      return '#ff4d4f'; // 红色
    };
    
    return (
      <table style={{ width: '100%', borderCollapse: 'collapse' }}>
        <thead>
          <tr>
            <th style={{ border: '1px solid #f0f0f0', padding: '8px', textAlign: 'center', backgroundColor: '#fafafa' }}></th>
            {numerical_columns.map((col, index) => (
              <th key={index} style={{ border: '1px solid #f0f0f0', padding: '8px', textAlign: 'center', backgroundColor: '#fafafa', fontSize: '12px' }}>
                {col}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {heatmapRows.map((row, rowIndex) => (
            <tr key={rowIndex}>
              <td style={{ border: '1px solid #f0f0f0', padding: '8px', textAlign: 'center', backgroundColor: '#fafafa', fontSize: '12px' }}>
                {row.name}
              </td>
              {numerical_columns.map((col, colIndex) => {
                const score = row[col];
                return (
                  <td key={colIndex} style={{ border: '1px solid #f0f0f0', padding: '4px', textAlign: 'center' }}>
                    <Tooltip title={`${(score * 100).toFixed(1)}%`}>
                      <div 
                        style={{ 
                          backgroundColor: getHeatmapColor(score), 
                          height: '20px', 
                          width: '100%',
                          borderRadius: '2px',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          color: 'white',
                          fontSize: '10px',
                          fontWeight: 'bold'
                        }}
                      >
                        {score !== undefined && !isNaN(score) ? (score * 100).toFixed(0) : 'N/A'}
                      </div>
                    </Tooltip>
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    );
  }

  // 渲染SDMetrics热力图
  const renderSDMetricsHeatmap = () => {
    return (
      <div>
        <p>SDMetrics热力图已整合到主热力图中，请选择"热力图"查看。</p>
      </div>
    );
  }

  // 渲染数据对比热力图
  const renderDataComparisonHeatmap = () => {
    // 检查是否有可视化数据
    if (!evaluationResult || !evaluationResult.visualization_data) {
      return <div>暂无可视化数据</div>;
    }
    
    const vizData = evaluationResult.visualization_data;
    
    // 检查必要的数据是否存在
    if (!vizData.detailed_comparison) {
      return <div>暂无足够的对比数据</div>;
    }
    
    // 获取颜色基于值
    const getColor = (value) => {
      if (value >= 0.8) return '#52c41a'; // 绿色
      if (value >= 0.6) return '#faad14'; // 黄色
      return '#ff4d4f'; // 红色
    };
    
    // 获取差异颜色（绿色表示相似，红色表示差异大）
    const getDifferenceColor = (difference) => {
      // 差异值越小颜色越绿，差异值越大颜色越红
      const absDiff = Math.abs(difference);
      if (absDiff < 0.1) return '#52c41a'; // 绿色（差异很小）
      if (absDiff < 0.3) return '#faad14'; // 黄色（差异中等）
      return '#ff4d4f'; // 红色（差异很大）
    };
    
    return (
      <div style={{ height: '600px', overflow: 'auto' }}>
        <h4>原始数据与合成数据对比分析</h4>
        
        {/* 基础质量指标热力图 */}
        <Card title="基础质量指标" style={{ marginBottom: '20px' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr>
                <th style={{ border: '1px solid #f0f0f0', padding: '8px', textAlign: 'left', backgroundColor: '#fafafa' }}>指标</th>
                <th style={{ border: '1px solid #f0f0f0', padding: '8px', textAlign: 'center', backgroundColor: '#fafafa' }}>得分</th>
                <th style={{ border: '1px solid #f0f0f0', padding: '8px', textAlign: 'center', backgroundColor: '#fafafa' }}>热力图</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td style={{ border: '1px solid #f0f0f0', padding: '8px' }}>整体质量</td>
                <td style={{ border: '1px solid #f0f0f0', padding: '8px', textAlign: 'center' }}>
                  <Tooltip title={`${(evaluationResult.overall_quality * 100).toFixed(1)}%`}>
                    <span>{(evaluationResult.overall_quality * 100).toFixed(1)}%</span>
                  </Tooltip>
                </td>
                <td style={{ border: '1px solid #f0f0f0', padding: '8px', textAlign: 'center' }}>
                  <Tooltip title={`${(evaluationResult.overall_quality * 100).toFixed(1)}%`}>
                    <div 
                      style={{ 
                        backgroundColor: getColor(evaluationResult.overall_quality), 
                        height: '20px', 
                        width: `${evaluationResult.overall_quality * 100}%`, 
                        minWidth: '20px',
                        borderRadius: '4px',
                        margin: '0 auto'
                      }}
                    />
                  </Tooltip>
                </td>
              </tr>
              <tr>
                <td style={{ border: '1px solid #f0f0f0', padding: '8px' }}>相似度</td>
                <td style={{ border: '1px solid #f0f0f0', padding: '8px', textAlign: 'center' }}>
                  <Tooltip title={`${(evaluationResult.similarity_score * 100).toFixed(1)}%`}>
                    <span>{(evaluationResult.similarity_score * 100).toFixed(1)}%</span>
                  </Tooltip>
                </td>
                <td style={{ border: '1px solid #f0f0f0', padding: '8px', textAlign: 'center' }}>
                  <Tooltip title={`${(evaluationResult.similarity_score * 100).toFixed(1)}%`}>
                    <div 
                      style={{ 
                        backgroundColor: getColor(evaluationResult.similarity_score), 
                        height: '20px', 
                        width: `${evaluationResult.similarity_score * 100}%`, 
                        minWidth: '20px',
                        borderRadius: '4px',
                        margin: '0 auto'
                      }}
                    />
                  </Tooltip>
                </td>
              </tr>
              <tr>
                <td style={{ border: '1px solid #f0f0f0', padding: '8px' }}>隐私保护</td>
                <td style={{ border: '1px solid #f0f0f0', padding: '8px', textAlign: 'center' }}>
                  <Tooltip title={`${(evaluationResult.privacy_score * 100).toFixed(1)}%`}>
                    <span>{(evaluationResult.privacy_score * 100).toFixed(1)}%</span>
                  </Tooltip>
                </td>
                <td style={{ border: '1px solid #f0f0f0', padding: '8px', textAlign: 'center' }}>
                  <Tooltip title={`${(evaluationResult.privacy_score * 100).toFixed(1)}%`}>
                    <div 
                      style={{ 
                        backgroundColor: getColor(evaluationResult.privacy_score), 
                        height: '20px', 
                        width: `${evaluationResult.privacy_score * 100}%`, 
                        minWidth: '20px',
                        borderRadius: '4px',
                        margin: '0 auto'
                      }}
                    />
                  </Tooltip>
                </td>
              </tr>
            </tbody>
          </table>
        </Card>
        
        {/* 详细统计信息对比 */}
        <Card title="详细统计信息对比" style={{ marginBottom: '20px' }}>
          <Tabs defaultActiveKey="1">
            <TabPane tab="相关性对比" key="1">
              <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                <thead>
                  <tr>
                    <th style={{ border: '1px solid #f0f0f0', padding: '8px', textAlign: 'left', backgroundColor: '#fafafa' }}>列名</th>
                    <th style={{ border: '1px solid #f0f0f0', padding: '8px', textAlign: 'center', backgroundColor: '#fafafa' }}>原始数据均值</th>
                    <th style={{ border: '1px solid #f0f0f0', padding: '8px', textAlign: 'center', backgroundColor: '#fafafa' }}>合成数据均值</th>
                    <th style={{ border: '1px solid #f0f0f0', padding: '8px', textAlign: 'center', backgroundColor: '#fafafa' }}>差异</th>
                    <th style={{ border: '1px solid #f0f0f0', padding: '8px', textAlign: 'center', backgroundColor: '#fafafa' }}>相关性得分</th>
                  </tr>
                </thead>
                <tbody>
                  {vizData.detailed_comparison && Object.keys(vizData.detailed_comparison).map((column, index) => {
                    const colData = vizData.detailed_comparison[column];
                    if (!colData?.original || !colData?.synthetic || colData.type !== 'numerical') return null;
                    
                    const origMean = colData.original.mean || 0;
                    const synthMean = colData.synthetic.mean || 0;
                    const difference = Math.abs(origMean - synthMean);
                    const correlationScore = evaluationResult.column_correlations[column] || 0;
                    
                    return (
                      <tr key={index}>
                        <td style={{ border: '1px solid #f0f0f0', padding: '8px' }}>{column}</td>
                        <td style={{ border: '1px solid #f0f0f0', padding: '8px', textAlign: 'center' }}>{origMean.toFixed(2)}</td>
                        <td style={{ border: '1px solid #f0f0f0', padding: '8px', textAlign: 'center' }}>{synthMean.toFixed(2)}</td>
                        <td style={{ border: '1px solid #f0f0f0', padding: '8px', textAlign: 'center' }}>
                          <Tooltip title={`差异: ${difference.toFixed(2)}`}>
                            <div 
                              style={{ 
                                backgroundColor: getDifferenceColor(difference), 
                                height: '20px', 
                                width: `${Math.min(difference * 20, 100)}%`, 
                                minWidth: '20px',
                                borderRadius: '4px',
                                margin: '0 auto'
                              }}
                            />
                          </Tooltip>
                        </td>
                        <td style={{ border: '1px solid #f0f0f0', padding: '8px', textAlign: 'center' }}>
                          <Tooltip title={`${(correlationScore * 100).toFixed(1)}%`}>
                            <div 
                              style={{ 
                                backgroundColor: getColor(correlationScore), 
                                height: '20px', 
                                width: `${correlationScore * 100}%`, 
                                minWidth: '20px',
                                borderRadius: '4px',
                                margin: '0 auto'
                              }}
                            />
                          </Tooltip>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </TabPane>
            <TabPane tab="分布对比" key="2">
              <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                <thead>
                  <tr>
                    <th style={{ border: '1px solid #f0f0f0', padding: '8px', textAlign: 'left', backgroundColor: '#fafafa' }}>列名</th>
                    <th style={{ border: '1px solid #f0f0f0', padding: '8px', textAlign: 'center', backgroundColor: '#fafafa' }}>原始数据标准差</th>
                    <th style={{ border: '1px solid #f0f0f0', padding: '8px', textAlign: 'center', backgroundColor: '#fafafa' }}>合成数据标准差</th>
                    <th style={{ border: '1px solid #f0f0f0', padding: '8px', textAlign: 'center', backgroundColor: '#fafafa' }}>差异</th>
                    <th style={{ border: '1px solid #f0f0f0', padding: '8px', textAlign: 'center', backgroundColor: '#fafafa' }}>分布相似度</th>
                  </tr>
                </thead>
                <tbody>
                  {vizData.detailed_comparison && Object.keys(vizData.detailed_comparison).map((column, index) => {
                    const colData = vizData.detailed_comparison[column];
                    if (!colData?.original || !colData?.synthetic || colData.type !== 'numerical') return null;
                    
                    const origStd = colData.original.std || 0;
                    const synthStd = colData.synthetic.std || 0;
                    const difference = Math.abs(origStd - synthStd);
                    const distributionScore = evaluationResult.distribution_similarity[column] || 0;
                    
                    return (
                      <tr key={index}>
                        <td style={{ border: '1px solid #f0f0f0', padding: '8px' }}>{column}</td>
                        <td style={{ border: '1px solid #f0f0f0', padding: '8px', textAlign: 'center' }}>{origStd.toFixed(2)}</td>
                        <td style={{ border: '1px solid #f0f0f0', padding: '8px', textAlign: 'center' }}>{synthStd.toFixed(2)}</td>
                        <td style={{ border: '1px solid #f0f0f0', padding: '8px', textAlign: 'center' }}>
                          <Tooltip title={`差异: ${difference.toFixed(2)}`}>
                            <div 
                              style={{ 
                                backgroundColor: getDifferenceColor(difference), 
                                height: '20px', 
                                width: `${Math.min(difference * 20, 100)}%`, 
                                minWidth: '20px',
                                borderRadius: '4px',
                                margin: '0 auto'
                              }}
                            />
                          </Tooltip>
                        </td>
                        <td style={{ border: '1px solid #f0f0f0', padding: '8px', textAlign: 'center' }}>
                          <Tooltip title={`${(distributionScore * 100).toFixed(1)}%`}>
                            <div 
                              style={{ 
                                backgroundColor: getColor(distributionScore), 
                                height: '20px', 
                                width: `${distributionScore * 100}%`, 
                                minWidth: '20px',
                                borderRadius: '4px',
                                margin: '0 auto'
                              }}
                            />
                          </Tooltip>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </TabPane>
          </Tabs>
        </Card>
        
        {/* 列级对比热力图 */}
        <Card title="列级对比分析" style={{ marginBottom: '20px' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr>
                <th style={{ border: '1px solid #f0f0f0', padding: '8px', textAlign: 'left', backgroundColor: '#fafafa' }}>列名</th>
                <th style={{ border: '1px solid #f0f0f0', padding: '8px', textAlign: 'center', backgroundColor: '#fafafa' }}>相关性得分</th>
                <th style={{ border: '1px solid #f0f0f0', padding: '8px', textAlign: 'center', backgroundColor: '#fafafa' }}>分布相似度</th>
                <th style={{ border: '1px solid #f0f0f0', padding: '8px', textAlign: 'center', backgroundColor: '#fafafa' }}>SDMetrics相似性</th>
              </tr>
            </thead>
            <tbody>
              {evaluationResult.column_correlations && Object.keys(evaluationResult.column_correlations).map((column, index) => {
                const correlationScore = evaluationResult.column_correlations[column];
                const distributionScore = evaluationResult.distribution_similarity[column] || 0;
                
                // 获取SDMetrics相似性得分
                let sdmetricsScore = 0;
                if (vizData.sdmetrics_heatmap_data && 
                    vizData.sdmetrics_heatmap_data.column_similarity && 
                    vizData.sdmetrics_heatmap_data.column_similarity[column]) {
                  sdmetricsScore = vizData.sdmetrics_heatmap_data.column_similarity[column].similarity_score || 0;
                }
                
                return (
                  <tr key={index}>
                    <td style={{ border: '1px solid #f0f0f0', padding: '8px' }}>{column}</td>
                    <td style={{ border: '1px solid #f0f0f0', padding: '8px', textAlign: 'center' }}>
                      <Tooltip title={`${(correlationScore * 100).toFixed(1)}%`}>
                        <div 
                          style={{ 
                            backgroundColor: getColor(correlationScore), 
                            height: '20px', 
                            width: `${correlationScore * 100}%`, 
                            minWidth: '20px',
                            borderRadius: '4px',
                            margin: '0 auto'
                          }}
                        />
                      </Tooltip>
                    </td>
                    <td style={{ border: '1px solid #f0f0f0', padding: '8px', textAlign: 'center' }}>
                      <Tooltip title={`${(distributionScore * 100).toFixed(1)}%`}>
                        <div 
                          style={{ 
                            backgroundColor: getColor(distributionScore), 
                            height: '20px', 
                            width: `${distributionScore * 100}%`, 
                            minWidth: '20px',
                            borderRadius: '4px',
                            margin: '0 auto'
                          }}
                        />
                      </Tooltip>
                    </td>
                    <td style={{ border: '1px solid #f0f0f0', padding: '8px', textAlign: 'center' }}>
                      <Tooltip title={`${(sdmetricsScore * 100).toFixed(1)}%`}>
                        <div 
                          style={{ 
                            backgroundColor: getColor(sdmetricsScore), 
                            height: '20px', 
                            width: `${sdmetricsScore * 100}%`, 
                            minWidth: '20px',
                            borderRadius: '4px',
                            margin: '0 auto'
                          }}
                        />
                      </Tooltip>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </Card>
        
        {/* SDMetrics列对趋势热力图 */}
        {vizData.sdmetrics_heatmap_data && 
         vizData.sdmetrics_heatmap_data.column_pair_trends && 
         vizData.sdmetrics_heatmap_data.column_pair_trends.success && (
          <Card title="SDMetrics列对趋势分析 (Column Pair Trends)">
            <div style={{ overflow: 'auto', maxHeight: '300px' }}>
              {renderColumnPairTrendsHeatmap(vizData.sdmetrics_heatmap_data.column_pair_trends)}
            </div>
          </Card>
        )}
      </div>
    );
  }

  // 渲染图表组件
  const renderCharts = () => {
    if (!evaluationResult) return null;

    // 准备图表数据
    const correlationData = Object.entries(evaluationResult.column_correlations).map(([column, score]) => ({
      name: column,
      value: score
    }));
    
    const distributionData = Object.entries(evaluationResult.distribution_similarity).map(([column, score]) => ({
      name: column,
      value: score
    }));

    // 计算综合质量评分
    const calculateQualityScore = () => {
      if (!evaluationResult) return 0;
      
      // 综合计算质量评分
      const weights = {
        overall_quality: 0.3,
        similarity_score: 0.25,
        privacy_score: 0.15,
        avg_correlation: 0.15,
        avg_distribution: 0.15
      };
      
      const avgCorrelation = Object.values(evaluationResult.column_correlations || {}).reduce((sum, val) => sum + val, 0) / 
                            Object.keys(evaluationResult.column_correlations || {}).length || 0;
      const avgDistribution = Object.values(evaluationResult.distribution_similarity || {}).reduce((sum, val) => sum + val, 0) / 
                            Object.keys(evaluationResult.distribution_similarity || {}).length || 0;
      
      const qualityScore = (
        weights.overall_quality * evaluationResult.overall_quality +
        weights.similarity_score * evaluationResult.similarity_score +
        weights.privacy_score * evaluationResult.privacy_score +
        weights.avg_correlation * avgCorrelation +
        weights.avg_distribution * avgDistribution
      ) * 100;
      
      return Math.round(qualityScore);
    };
    
    // 获取质量评分等级
    const getQualityScoreLevel = (score) => {
      if (score >= 80) return 'excellent';
      if (score >= 60) return 'good';
      return 'poor';
    };
    
    // 获取质量评分颜色
    const getQualityScoreColor = (score) => {
      if (score >= 80) return '#52c41a';
      if (score >= 60) return '#faad14';
      return '#ff4d4f';
    };

    return (
      <div className="evaluation-content">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
          <h3 style={{ margin: 0 }}>数据质量可视化分析</h3>
          {/* 图表类型选择 */}
          <Radio.Group 
            value={chartType} 
            onChange={(e) => setChartType(e.target.value)}
            buttonStyle="solid"
          >
            <Radio.Button value="overview">整体概览</Radio.Button>
            <Radio.Button value="dashboard">仪表盘</Radio.Button>
            <Radio.Button value="radar">雷达图</Radio.Button>
            <Radio.Button value="table">表格</Radio.Button>
            <Radio.Button value="bar">柱状图</Radio.Button>
            <Radio.Button value="heatmap_view">热力图</Radio.Button>
            <Radio.Button value="data_comparison">数据对比</Radio.Button>
            <Radio.Button value="line">曲线图</Radio.Button>
            <Radio.Button value="scatter">散点图</Radio.Button>
          </Radio.Group>
        </div>
        
        {/* 自动评分系统 */}
        {chartType === 'overview' && (
          <Card title="生成质量评分" className="dashboard-card">
            <div className={`quality-score ${getQualityScoreLevel(calculateQualityScore())}`}>
              <div>综合质量评分</div>
              <div className="metric-value">{calculateQualityScore()}分</div>
              <Progress 
                percent={calculateQualityScore()} 
                showInfo={false} 
                strokeColor={getQualityScoreColor(calculateQualityScore())}
                size="small"
              />
            </div>
          </Card>
        )}

        {/* 整体评估结果 */}
        {(chartType === 'overview' || chartType === 'dashboard') && (
          <Card title="整体评估结果" className="dashboard-card">
            <Row gutter={16}>
              <Col span={8}>
                <div className="metric-card">
                  <div className="metric-label">整体质量</div>
                  <div className="metric-value" style={{ color: evaluationResult.overall_quality >= 0.8 ? '#52c41a' : evaluationResult.overall_quality >= 0.6 ? '#faad14' : '#ff4d4f' }}>
                    {(evaluationResult.overall_quality * 100).toFixed(1)}%
                  </div>
                  <Progress 
                    percent={Math.round(evaluationResult.overall_quality * 100)} 
                    showInfo={false} 
                    strokeColor={evaluationResult.overall_quality >= 0.8 ? '#52c41a' : evaluationResult.overall_quality >= 0.6 ? '#faad14' : '#ff4d4f'}
                  />
                  <div style={{ fontSize: '12px', marginTop: '4px' }}>
                    {evaluationResult.overall_quality >= 0.8 ? '优秀' : evaluationResult.overall_quality >= 0.6 ? '良好' : '需改进'}
                  </div>
                </div>
              </Col>
              <Col span={8}>
                <div className="metric-card">
                  <div className="metric-label">相似度</div>
                  <div className="metric-value" style={{ color: evaluationResult.similarity_score >= 0.8 ? '#52c41a' : evaluationResult.similarity_score >= 0.6 ? '#faad14' : '#ff4d4f' }}>
                    {(evaluationResult.similarity_score * 100).toFixed(1)}%
                  </div>
                  <Progress 
                    percent={Math.round(evaluationResult.similarity_score * 100)} 
                    showInfo={false} 
                    strokeColor={evaluationResult.similarity_score >= 0.8 ? '#52c41a' : evaluationResult.similarity_score >= 0.6 ? '#faad14' : '#ff4d4f'}
                  />
                  <div style={{ fontSize: '12px', marginTop: '4px' }}>
                    {evaluationResult.similarity_score >= 0.8 ? '高度相似' : evaluationResult.similarity_score >= 0.6 ? '中等相似' : '低度相似'}
                  </div>
                </div>
              </Col>
              <Col span={8}>
                <div className="metric-card">
                  <div className="metric-label">隐私保护</div>
                  <div className="metric-value" style={{ color: evaluationResult.privacy_score >= 0.8 ? '#52c41a' : evaluationResult.privacy_score >= 0.6 ? '#faad14' : '#ff4d4f' }}>
                    {(evaluationResult.privacy_score * 100).toFixed(1)}%
                  </div>
                  <Progress 
                    percent={Math.round(evaluationResult.privacy_score * 100)} 
                    showInfo={false} 
                    strokeColor={evaluationResult.privacy_score >= 0.8 ? '#52c41a' : evaluationResult.privacy_score >= 0.6 ? '#faad14' : '#ff4d4f'}
                  />
                  <div style={{ fontSize: '12px', marginTop: '4px' }}>
                    {evaluationResult.privacy_score >= 0.8 ? '保护良好' : evaluationResult.privacy_score >= 0.6 ? '保护一般' : '保护不足'}
                  </div>
                </div>
              </Col>
            </Row>
            
            {/* 数据量信息 */}
            <div style={{ marginTop: '20px', padding: '16px', backgroundColor: '#f0f2f5', borderRadius: '8px' }}>
              <Row gutter={16}>
                <Col span={12}>
                  <div style={{ fontSize: '16px', fontWeight: 'bold', marginBottom: '8px' }}>数据量信息</div>
                  <div>原始数据行数: {evaluationResult.detailed_metrics?.row_count || 0}</div>
                  <div>合成数据行数: {evaluationResult.visualization_data?.data_shapes?.synthetic_count || 0}</div>
                  <div>列数: {evaluationResult.detailed_metrics?.column_count || 0}</div>
                </Col>
                <Col span={12}>
                  <div style={{ fontSize: '16px', fontWeight: 'bold', marginBottom: '8px' }}>数据类型</div>
                  <div>
                    {evaluationResult.visualization_data?.data_types && 
                      Object.entries(evaluationResult.visualization_data.data_types).slice(0, 5).map(([col, type]) => (
                        <div key={col}>{col}: {type}</div>
                      ))}
                    {evaluationResult.visualization_data?.data_types && 
                      Object.keys(evaluationResult.visualization_data.data_types).length > 5 && <div>...</div>}
                  </div>
                </Col>
              </Row>
            </div>
            
            {/* 评估说明 */}
            <div style={{ marginTop: '20px', padding: '16px', backgroundColor: '#f0f2f5', borderRadius: '8px' }}>
              <h4>评估说明</h4>
              <p><strong>整体质量：</strong>综合考虑相似度、相关性、分布和隐私保护等因素得出的综合评分。80%以上为优秀，60-80%为良好，60%以下需改进。</p>
              <p><strong>相似度：</strong>原始数据与合成数据在数值上的相似程度。80%以上为高度相似，60-80%为中等相似，60%以下为低度相似。</p>
              <p><strong>隐私保护：</strong>合成数据对原始数据隐私信息的保护程度。80%以上为保护良好，60-80%为保护一般，60%以下为保护不足。</p>
            </div>
          </Card>
        )}
        
        {/* 仪表盘视图 */}
        {chartType === 'dashboard' && (
          <Card title="详细指标分析" className="dashboard-card">
            <Row gutter={16}>
              <Col span={6}>
                <div className="metric-card">
                  <div className="metric-label">分布相似度</div>
                  <div className="metric-value" style={{ color: '#1890ff' }}>
                    {(
                      Object.values(evaluationResult.distribution_similarity || {}).reduce((sum, val) => sum + val, 0) / 
                      Object.keys(evaluationResult.distribution_similarity || {}).length * 100
                    ).toFixed(1)}%
                  </div>
                </div>
              </Col>
              <Col span={6}>
                <div className="metric-card">
                  <div className="metric-label">特征保持度</div>
                  <div className="metric-value" style={{ color: '#1890ff' }}>
                    {(
                      Object.values(evaluationResult.column_correlations || {}).reduce((sum, val) => sum + val, 0) / 
                      Object.keys(evaluationResult.column_correlations || {}).length * 100
                    ).toFixed(1)}%
                  </div>
                </div>
              </Col>
              <Col span={6}>
                <div className="metric-card">
                  <div className="metric-label">统计一致性</div>
                  <div className="metric-value" style={{ color: '#1890ff' }}>
                    {(
                      (evaluationResult.similarity_score + evaluationResult.overall_quality) / 2 * 100
                    ).toFixed(1)}%
                  </div>
                </div>
              </Col>
              <Col span={6}>
                <div className="metric-card">
                  <div className="metric-label">相关性差异</div>
                  <div className="metric-value" style={{ color: '#1890ff' }}>
                    {(
                      (1 - Object.values(evaluationResult.column_correlations || {}).reduce((sum, val) => sum + val, 0) / 
                      Object.keys(evaluationResult.column_correlations || {}).length) * 100
                    ).toFixed(1)}%
                  </div>
                </div>
              </Col>
            </Row>
          </Card>
        )}
        
        {/* 雷达图视图 */}
        {chartType === 'radar' && (
          <Card title="质量指标雷达图" className="dashboard-card">
            {renderRadarChart()}
          </Card>
        )}
        
        {/* 仪表盘视图 */}
        {chartType === 'dashboard' && (
          <Card title="详细指标分析" className="dashboard-card">
            <Row gutter={16}>
              <Col span={6}>
                <div className="metric-card">
                  <div className="metric-label">分布相似度</div>
                  <div className="metric-value" style={{ color: '#1890ff' }}>
                    {(
                      Object.values(evaluationResult.distribution_similarity || {}).reduce((sum, val) => sum + val, 0) / 
                      Object.keys(evaluationResult.distribution_similarity || {}).length * 100
                    ).toFixed(1)}%
                  </div>
                </div>
              </Col>
              <Col span={6}>
                <div className="metric-card">
                  <div className="metric-label">特征保持度</div>
                  <div className="metric-value" style={{ color: '#1890ff' }}>
                    {(
                      Object.values(evaluationResult.column_correlations || {}).reduce((sum, val) => sum + val, 0) / 
                      Object.keys(evaluationResult.column_correlations || {}).length * 100
                    ).toFixed(1)}%
                  </div>
                </div>
              </Col>
              <Col span={6}>
                <div className="metric-card">
                  <div className="metric-label">统计一致性</div>
                  <div className="metric-value" style={{ color: '#1890ff' }}>
                    {(
                      (evaluationResult.similarity_score + evaluationResult.overall_quality) / 2 * 100
                    ).toFixed(1)}%
                  </div>
                </div>
              </Col>
              <Col span={6}>
                <div className="metric-card">
                  <div className="metric-label">相关性差异</div>
                  <div className="metric-value" style={{ color: '#1890ff' }}>
                    {(
                      (1 - Object.values(evaluationResult.column_correlations || {}).reduce((sum, val) => sum + val, 0) / 
                      Object.keys(evaluationResult.column_correlations || {}).length) * 100
                    ).toFixed(1)}%
                  </div>
                </div>
              </Col>
            </Row>
          </Card>
        )}

        {/* 原始数据与合成数据对比 */}
        <Card title="原始数据与合成数据对比" style={{ width: '100%', marginTop: '20px' }}>
          <Tabs defaultActiveKey="1">
            <TabPane tab="列相关性分析" key="1">
              <div style={{ height: '300px' }}>
                {chartType === 'table' ? (
                  <Table
                    dataSource={Object.entries(evaluationResult.column_correlations).map(([column, score]) => ({
                      key: column,
                      column,
                      score
                    }))}
                    columns={[
                      {
                        title: '列名',
                        dataIndex: 'column',
                        key: 'column',
                      },
                      {
                        title: '相关性得分',
                        dataIndex: 'score',
                        key: 'score',
                        render: (score) => getScoreTag(score),
                        sorter: (a, b) => a.score - b.score
                      }
                    ]}
                    pagination={false}
                    size="small"
                    scroll={{ y: 200 }}
                  />
                ) : chartType === 'bar' ? (
                  renderBarChart(correlationData, '列相关性', 'value')
                ) : chartType === 'line' ? (
                  renderLineChart(correlationData, '列相关性')
                ) : chartType === 'heatmap_view' ? (
                  renderHeatmap(correlationData, distributionData)
                ) : chartType === 'data_comparison' ? (
                  renderDataComparisonHeatmap()
                ) : chartType === 'scatter' ? (
                  renderScatterComparison()
                ) : (
                  <div>请选择合适的图表类型</div>
                )}
              </div>
            </TabPane>

            <TabPane tab="分布相似度分析" key="2">
              <div style={{ height: '300px' }}>
                {chartType === 'table' ? (
                  <Table
                    dataSource={Object.entries(evaluationResult.distribution_similarity).map(([column, score]) => ({
                      key: column,
                      column,
                      score
                    }))}
                    columns={[
                      {
                        title: '列名',
                        dataIndex: 'column',
                        key: 'column',
                      },
                      {
                        title: '分布相似度',
                        dataIndex: 'score',
                        key: 'score',
                        render: (score) => getScoreTag(score),
                        sorter: (a, b) => a.score - b.score
                      }
                    ]}
                    pagination={false}
                    size="small"
                    scroll={{ y: 200 }}
                  />
                ) : chartType === 'bar' ? (
                  renderBarChart(distributionData, '分布相似度', 'value')
                ) : chartType === 'line' ? (
                  renderLineChart(distributionData, '分布相似度')
                ) : chartType === 'heatmap_view' ? (
                  renderHeatmap(correlationData, distributionData)
                ) : chartType === 'data_comparison' ? (
                  renderDataComparisonHeatmap()
                ) : chartType === 'scatter' ? (
                  renderScatterComparison()
                ) : (
                  <div>请选择合适的图表类型</div>
                )}
              </div>
            </TabPane>

            <TabPane tab="边际分布对比" key="3">
              <div style={{ height: '400px', overflow: 'auto' }}>
                {renderMarginalDistributionComparison()}
              </div>
            </TabPane>

            <TabPane tab="列相关性对比" key="4">
              <div style={{ height: '400px' }}>
                {renderColumnCorrelationComparison()}
              </div>
            </TabPane>
            
            <TabPane tab="散点图对比" key="5">
              <div style={{ height: '400px' }}>
                {renderScatterPlots()}
              </div>
            </TabPane>
            <TabPane tab="直方图对比" key="6">
              <div style={{ height: '400px', overflow: 'auto' }}>
                {renderHistogramComparisons()}
              </div>
            </TabPane>
            <TabPane tab="箱线图对比" key="7">
              <div style={{ height: '400px' }}>
                {renderBoxPlot()}
              </div>
            </TabPane>
          </Tabs>
        </Card>

        {evaluationResult.sdmetrics_result && evaluationResult.sdmetrics_result.success && (
          <Card title="SDMetrics 详细分析" style={{ marginTop: '20px' }}>
            <Descriptions bordered column={2}>
              <Descriptions.Item label="整体得分">
                {getScoreTag(evaluationResult.sdmetrics_result.overall_score)}
              </Descriptions.Item>
              <Descriptions.Item label="列形状得分">
                {evaluationResult.sdmetrics_result.column_shapes_score ? 
                  getScoreTag(evaluationResult.sdmetrics_result.column_shapes_score) : 'N/A'}
              </Descriptions.Item>
              <Descriptions.Item label="列对趋势得分">
                {evaluationResult.sdmetrics_result.column_pair_trends_score ? 
                  getScoreTag(evaluationResult.sdmetrics_result.column_pair_trends_score) : 'N/A'}
              </Descriptions.Item>
            </Descriptions>
            
            {evaluationResult.sdmetrics_result.properties && (
              <div style={{ marginTop: '20px' }}>
                <h4>属性分析</h4>
                <Table
                  dataSource={evaluationResult.sdmetrics_result.properties.map((prop, index) => ({
                    key: index,
                    property: prop.Property,
                    score: prop.Score,
                    description: prop.Description || ''
                  }))}
                  columns={[
                    {
                      title: '属性',
                      dataIndex: 'property',
                      key: 'property',
                    },
                    {
                      title: '得分',
                      dataIndex: 'score',
                      key: 'score',
                      render: (score) => getScoreTag(score)
                    },
                    {
                      title: '描述',
                      dataIndex: 'description',
                      key: 'description',
                    }
                  ]}
                  pagination={false}
                  size="small"
                />
              </div>
            )}
          </Card>
        )}

        <Card title="数据概览" style={{ marginTop: '20px' }}>
          <Descriptions bordered>
            <Descriptions.Item label="列数">
              {evaluationResult.detailed_metrics?.column_count || 'N/A'}
            </Descriptions.Item>
            <Descriptions.Item label="行数">
              {evaluationResult.detailed_metrics?.row_count || 'N/A'}
            </Descriptions.Item>
            <Descriptions.Item label="数据类型" span={2}>
              {evaluationResult.visualization_data?.data_types && 
                Object.entries(evaluationResult.visualization_data.data_types).map(([col, type]) => (
                  <div key={col}>{col}: {type}</div>
                ))}
            </Descriptions.Item>
          </Descriptions>
        </Card>
      </div>
    );
  }

  // 渲染边际分布对比
  const renderMarginalDistributionComparison = () => {
    if (!evaluationResult || !evaluationResult.visualization_data || !evaluationResult.visualization_data.marginal_distribution_comparison) {
      return <div>暂无分布对比数据</div>;
    }

    const marginalData = evaluationResult.visualization_data.marginal_distribution_comparison;
    
    // 检查是否有数据
    if (Object.keys(marginalData).length === 0) {
      return <div>暂无分布对比数据</div>;
    }
    
    return (
      <div>
        <table style={{ width: '100%', borderCollapse: 'collapse', marginBottom: '20px' }}>
          <thead>
            <tr>
              <th style={{ border: '1px solid #f0f0f0', padding: '8px', textAlign: 'left', backgroundColor: '#fafafa' }}>列名</th>
              <th style={{ border: '1px solid #f0f0f0', padding: '8px', textAlign: 'center', backgroundColor: '#fafafa' }}>类型</th>
              <th style={{ border: '1px solid #f0f0f0', padding: '8px', textAlign: 'center', backgroundColor: '#fafafa' }}>原始数据</th>
              <th style={{ border: '1px solid #f0f0f0', padding: '8px', textAlign: 'center', backgroundColor: '#fafafa' }}>合成数据</th>
              <th style={{ border: '1px solid #f0f0f0', padding: '8px', textAlign: 'center', backgroundColor: '#fafafa' }}>分布相似度</th>
            </tr>
          </thead>
          <tbody>
            {Object.entries(marginalData).map(([column, data], index) => (
              <tr key={index}>
                <td style={{ border: '1px solid #f0f0f0', padding: '8px' }}>{column}</td>
                <td style={{ border: '1px solid #f0f0f0', padding: '8px', textAlign: 'center' }}>
                  <Tag color={data.type === 'numerical' ? 'blue' : 'green'}>
                    {data.type === 'numerical' ? '数值型' : '分类型'}
                  </Tag>
                </td>
                <td style={{ border: '1px solid #f0f0f0', padding: '8px' }}>
                  {data.type === 'numerical' ? (
                    <div>
                      <div><strong>均值:</strong> {data.original?.mean?.toFixed(2) || 'N/A'}</div>
                      <div><strong>标准差:</strong> {data.original?.std?.toFixed(2) || 'N/A'}</div>
                      <div><strong>中位数:</strong> {data.original?.median?.toFixed(2) || 'N/A'}</div>
                      <div><strong>偏度:</strong> {data.original?.skewness?.toFixed(2) || 'N/A'}</div>
                      <div><strong>峰度:</strong> {data.original?.kurtosis?.toFixed(2) || 'N/A'}</div>
                      <div><strong>最小值:</strong> {data.original?.min?.toFixed(2) || 'N/A'}</div>
                      <div><strong>最大值:</strong> {data.original?.max?.toFixed(2) || 'N/A'}</div>
                    </div>
                  ) : (
                    <div>
                      <div><strong>值频率分布:</strong></div>
                      {data.original?.value_frequencies && Object.entries(data.original.value_frequencies).slice(0, 5).map(([value, freq]) => (
                        <div key={value}>{value}: {(freq * 100).toFixed(1)}%</div>
                      ))}
                      {data.original?.value_frequencies && Object.keys(data.original.value_frequencies).length > 5 && <div>...</div>}
                      {!data.original?.value_frequencies && <div>无数据</div>}
                    </div>
                  )}
                </td>
                <td style={{ border: '1px solid #f0f0f0', padding: '8px' }}>
                  {data.type === 'numerical' ? (
                    <div>
                      <div><strong>均值:</strong> {data.synthetic?.mean?.toFixed(2) || 'N/A'}</div>
                      <div><strong>标准差:</strong> {data.synthetic?.std?.toFixed(2) || 'N/A'}</div>
                      <div><strong>中位数:</strong> {data.synthetic?.median?.toFixed(2) || 'N/A'}</div>
                      <div><strong>偏度:</strong> {data.synthetic?.skewness?.toFixed(2) || 'N/A'}</div>
                      <div><strong>峰度:</strong> {data.synthetic?.kurtosis?.toFixed(2) || 'N/A'}</div>
                      <div><strong>最小值:</strong> {data.synthetic?.min?.toFixed(2) || 'N/A'}</div>
                      <div><strong>最大值:</strong> {data.synthetic?.max?.toFixed(2) || 'N/A'}</div>
                    </div>
                  ) : (
                    <div>
                      <div><strong>值频率分布:</strong></div>
                      {data.synthetic?.value_frequencies && Object.entries(data.synthetic.value_frequencies).slice(0, 5).map(([value, freq]) => (
                        <div key={value}>{value}: {(freq * 100).toFixed(1)}%</div>
                      ))}
                      {data.synthetic?.value_frequencies && Object.keys(data.synthetic.value_frequencies).length > 5 && <div>...</div>}
                      {!data.synthetic?.value_frequencies && <div>无数据</div>}
                    </div>
                  )}
                </td>
                <td style={{ border: '1px solid #f0f0f0', padding: '8px', textAlign: 'center' }}>
                  <Tooltip title={`${(evaluationResult.distribution_similarity[column] * 100).toFixed(1)}%`}>
                    <Progress 
                      percent={Math.round(evaluationResult.distribution_similarity[column] * 100)} 
                      showInfo={false} 
                      strokeColor={evaluationResult.distribution_similarity[column] >= 0.8 ? '#52c41a' : evaluationResult.distribution_similarity[column] >= 0.6 ? '#faad14' : '#ff4d4f'}
                      size="small"
                    />
                  </Tooltip>
                  <div>{(evaluationResult.distribution_similarity[column] * 100).toFixed(1)}%</div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        
        {/* 分布差异可视化 */}
        <div style={{ marginTop: '20px' }}>
          <h4>分布差异可视化</h4>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '20px' }}>
            {Object.entries(marginalData).slice(0, 4).map(([column, data], index) => (
              <Card title={`${column} 分布差异`} key={index} style={{ width: '45%' }}>
                <div style={{ height: '200px' }}>
                  {renderDistributionDifferenceChart(column, data)}
                </div>
              </Card>
            ))}
          </div>
        </div>
      </div>
    );
  }

  // 渲染分布差异图表
  const renderDistributionDifferenceChart = (column, data) => {
    if (data.type === 'numerical') {
      // 对于数值列，显示统计信息对比
      const statsData = [
        { name: '均值', original: data.original?.mean || 0, synthetic: data.synthetic?.mean || 0 },
        { name: '标准差', original: data.original?.std || 0, synthetic: data.synthetic?.std || 0 },
        { name: '中位数', original: data.original?.median || 0, synthetic: data.synthetic?.median || 0 },
        { name: '最小值', original: data.original?.min || 0, synthetic: data.synthetic?.min || 0 },
        { name: '最大值', original: data.original?.max || 0, synthetic: data.synthetic?.max || 0 }
      ];
      
      return (
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            data={statsData}
            margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
          >
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="name" />
            <YAxis />
            <RechartsTooltip />
            <Legend />
            <Bar dataKey="original" name="原始数据" fill="#1890ff" />
            <Bar dataKey="synthetic" name="合成数据" fill="#52c41a" />
          </BarChart>
        </ResponsiveContainer>
      );
    } else {
      // 对于分类列，显示频率对比
      const freqData = Object.keys(data.original?.value_frequencies || {})
        .slice(0, 10)
        .map(value => ({
          name: value,
          original: (data.original?.value_frequencies[value] || 0) * 100,
          synthetic: (data.synthetic?.value_frequencies[value] || 0) * 100
        }));
      
      return (
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            data={freqData}
            margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
          >
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="name" />
            <YAxis domain={[0, 100]} />
            <RechartsTooltip formatter={(value) => [value.toFixed(1) + '%', '频率']} />
            <Legend />
            <Bar dataKey="original" name="原始数据" fill="#1890ff" />
            <Bar dataKey="synthetic" name="合成数据" fill="#52c41a" />
          </BarChart>
        </ResponsiveContainer>
      );
    }
  }

  // 渲染列相关性对比
  const renderColumnCorrelationComparison = () => {
    if (!evaluationResult || !evaluationResult.visualization_data || !evaluationResult.visualization_data.detailed_comparison) {
      return <div>暂无相关性对比数据</div>;
    }

    const detailedData = evaluationResult.visualization_data.detailed_comparison;
    
    // 检查是否有数据
    if (Object.keys(detailedData).length === 0) {
      return <div>暂无相关性对比数据</div>;
    }
    
    return (
      <div>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr>
              <th style={{ border: '1px solid #f0f0f0', padding: '8px', textAlign: 'left', backgroundColor: '#fafafa' }}>列名</th>
              <th style={{ border: '1px solid #f0f0f0', padding: '8px', textAlign: 'center', backgroundColor: '#fafafa' }}>原始数据统计</th>
              <th style={{ border: '1px solid #f0f0f0', padding: '8px', textAlign: 'center', backgroundColor: '#fafafa' }}>合成数据统计</th>
              <th style={{ border: '1px solid #f0f0f0', padding: '8px', textAlign: 'center', backgroundColor: '#fafafa' }}>相关性得分</th>
            </tr>
          </thead>
          <tbody>
            {Object.entries(detailedData).map(([column, data], index) => (
              <tr key={index}>
                <td style={{ border: '1px solid #f0f0f0', padding: '8px' }}>{column}</td>
                <td style={{ border: '1px solid #f0f0f0', padding: '8px' }}>
                  <div><strong>均值:</strong> {data.original?.mean?.toFixed(2) || 'N/A'}</div>
                  <div><strong>标准差:</strong> {data.original?.std?.toFixed(2) || 'N/A'}</div>
                  <div><strong>中位数:</strong> {data.original?.median?.toFixed(2) || 'N/A'}</div>
                  <div><strong>偏度:</strong> {data.original?.skewness?.toFixed(2) || 'N/A'}</div>
                  <div><strong>峰度:</strong> {data.original?.kurtosis?.toFixed(2) || 'N/A'}</div>
                  <div><strong>最小值:</strong> {data.original?.min?.toFixed(2) || 'N/A'}</div>
                  <div><strong>最大值:</strong> {data.original?.max?.toFixed(2) || 'N/A'}</div>
                </td>
                <td style={{ border: '1px solid #f0f0f0', padding: '8px' }}>
                  <div><strong>均值:</strong> {data.synthetic?.mean?.toFixed(2) || 'N/A'}</div>
                  <div><strong>标准差:</strong> {data.synthetic?.std?.toFixed(2) || 'N/A'}</div>
                  <div><strong>中位数:</strong> {data.synthetic?.median?.toFixed(2) || 'N/A'}</div>
                  <div><strong>偏度:</strong> {data.synthetic?.skewness?.toFixed(2) || 'N/A'}</div>
                  <div><strong>峰度:</strong> {data.synthetic?.kurtosis?.toFixed(2) || 'N/A'}</div>
                  <div><strong>最小值:</strong> {data.synthetic?.min?.toFixed(2) || 'N/A'}</div>
                  <div><strong>最大值:</strong> {data.synthetic?.max?.toFixed(2) || 'N/A'}</div>
                </td>
                <td style={{ border: '1px solid #f0f0f0', padding: '8px', textAlign: 'center' }}>
                  <Tooltip title={`${(evaluationResult.column_correlations[column] * 100).toFixed(1)}%`}>
                    <Progress 
                      percent={Math.round(evaluationResult.column_correlations[column] * 100)} 
                      showInfo={false} 
                      strokeColor={evaluationResult.column_correlations[column] >= 0.8 ? '#52c41a' : evaluationResult.column_correlations[column] >= 0.6 ? '#faad14' : '#ff4d4f'}
                      size="small"
                    />
                  </Tooltip>
                  <div>{(evaluationResult.column_correlations[column] * 100).toFixed(1)}%</div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        
        {/* 相关性差异可视化 */}
        <div style={{ marginTop: '20px' }}>
          <h4>列间相关性差异可视化</h4>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '20px' }}>
            {Object.entries(detailedData)
              .filter(([column, data]) => data.type === 'numerical') // 只显示数值列
              .slice(0, 4)
              .map(([column, data], index) => (
                <Card title={`${column} 相关性对比`} key={index} style={{ width: '45%' }}>
                  <div style={{ height: '200px' }}>
                    {renderDistributionDifferenceChart(column, data)}
                  </div>
                </Card>
              ))}
          </div>
        </div>
      </div>
    );
  }

  // 渲染相关性差异图表
  const renderCorrelationDifferenceChart = (column, data) => {
    if (!data.correlations) return <div>无相关性数据</div>;
    
    // 准备相关性对比数据
    const correlationKeys = Object.keys(data.correlations.original_with_others || {}).slice(0, 10);
    const chartData = correlationKeys.map(key => ({
      name: key,
      original: data.correlations.original_with_others[key],
      synthetic: data.correlations.synthetic_with_others[key],
      difference: data.correlations.differences[key]
    }));
    
    return (
      <ResponsiveContainer width="100%" height="100%">
        <BarChart
          data={chartData}
          margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
        >
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="name" />
          <YAxis domain={[-1, 1]} />
          <RechartsTooltip />
          <Legend />
          <Bar dataKey="original" name="原始数据相关性" fill="#1890ff" />
          <Bar dataKey="synthetic" name="合成数据相关性" fill="#52c41a" />
          <Bar dataKey="difference" name="相关性差异" fill="#faad14" />
        </BarChart>
      </ResponsiveContainer>
    );
  }

  // 渲染散点图对比
  const renderScatterPlots = () => {
    if (!evaluationResult || !evaluationResult.visualization_data || !evaluationResult.visualization_data.detailed_comparison) {
      return <div>暂无散点图数据</div>;
    }

    const detailedData = evaluationResult.visualization_data.detailed_comparison;
    const columns = Object.keys(detailedData).filter(col => detailedData[col].type === 'numerical').slice(0, 4); // 只显示前4个数值列的散点图
    
    return (
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '20px' }}>
        {columns.map((column, index) => (
          <Card title={`${column} 散点图对比`} key={index} style={{ width: '48%' }}>
            <div style={{ height: '250px' }}>
              {renderScatterPlot(column, detailedData[column])}
            </div>
          </Card>
        ))}
      </div>
    );
  }
  
  // 渲染直方图对比
  const renderHistogramComparisons = () => {
    if (!evaluationResult || !evaluationResult.visualization_data || !evaluationResult.visualization_data.detailed_comparison) {
      return <div>暂无直方图数据</div>;
    }

    const detailedData = evaluationResult.visualization_data.detailed_comparison;
    const columns = Object.keys(detailedData).filter(col => detailedData[col].type === 'numerical').slice(0, 4); // 只显示前4个数值列的直方图
    
    return (
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '20px' }}>
        {columns.map((column, index) => (
          <Card title={`${column} 直方图对比`} key={index} style={{ width: '48%' }}>
            <div style={{ height: '250px' }}>
              {renderHistogramComparison(column, detailedData[column])}
            </div>
          </Card>
        ))}
      </div>
    );
  }

  // 渲染散点图对比
  const renderScatterComparison = () => {
    if (!evaluationResult || !evaluationResult.visualization_data || !evaluationResult.visualization_data.detailed_comparison) {
      return <div>暂无散点图数据</div>;
    }

    const detailedData = evaluationResult.visualization_data.detailed_comparison;
    const columns = Object.keys(detailedData).filter(col => detailedData[col].type === 'numerical').slice(0, 2); // 只显示前2个数值列的散点图
    
    return (
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '20px' }}>
        {columns.map((column, index) => (
          <Card title={`${column} 散点图对比`} key={index} style={{ width: '48%' }}>
            <div style={{ height: '250px' }}>
              {renderScatterPlot(column, detailedData[column])}
            </div>
          </Card>
        ))}
      </div>
    );
  }

  // 渲染散点图
  const renderScatterPlot = (column, data) => {
    // 生成示例散点图数据
    const generateScatterData = (mean, std, count = 50) => {
      return Array.from({ length: count }, (_, i) => ({
        x: i,
        y: mean + (Math.random() - 0.5) * std * 2
      }));
    };
    
    const originalData = generateScatterData(data.original?.mean || 0, data.original?.std || 1);
    const syntheticData = generateScatterData(data.synthetic?.mean || 0, data.synthetic?.std || 1);
    
    // 合并数据并添加标识
    const combinedData = [
      ...originalData.map(d => ({ ...d, type: '原始数据' })),
      ...syntheticData.map(d => ({ ...d, type: '合成数据' }))
    ];
    
    return (
      <ResponsiveContainer width="100%" height="100%">
        <ScatterChart
          data={combinedData}
          margin={{ top: 20, right: 20, bottom: 20, left: 20 }}
        >
          <CartesianGrid />
          <XAxis type="number" dataKey="x" name="索引" />
          <YAxis type="number" dataKey="y" name="值" />
          <ZAxis type="category" dataKey="type" name="类型" />
          <RechartsTooltip cursor={{ strokeDasharray: '3 3' }} />
          <Legend />
          <Scatter name="原始数据" data={originalData} fill="#1890ff" />
          <Scatter name="合成数据" data={syntheticData} fill="#52c41a" />
        </ScatterChart>
      </ResponsiveContainer>
    );
  }
  
  // 渲染直方图对比
  const renderHistogramComparison = (column, data) => {
    if (!data || !data.original || !data.synthetic) return <div>无数据</div>;
    
    // 生成直方图数据
    const generateHistogramData = (mean, std, count = 100) => {
      const values = Array.from({ length: count }, () => mean + (Math.random() - 0.5) * std * 2);
      const min = Math.min(...values);
      const max = Math.max(...values);
      const binCount = 20;
      const binWidth = (max - min) / binCount;
      
      const bins = Array(binCount).fill(0);
      values.forEach(value => {
        const binIndex = Math.min(Math.floor((value - min) / binWidth), binCount - 1);
        bins[binIndex]++;
      });
      
      return bins.map((count, index) => ({
        bin: min + index * binWidth,
        count: count
      }));
    };
    
    const originalHistData = generateHistogramData(data.original.mean || 0, data.original.std || 1);
    const syntheticHistData = generateHistogramData(data.synthetic.mean || 0, data.synthetic.std || 1);
    
    // 合并数据用于对比显示
    const combinedData = [];
    for (let i = 0; i < Math.max(originalHistData.length, syntheticHistData.length); i++) {
      combinedData.push({
        bin: originalHistData[i]?.bin || syntheticHistData[i]?.bin || 0,
        original: originalHistData[i]?.count || 0,
        synthetic: syntheticHistData[i]?.count || 0
      });
    }
    
    return (
      <div className="histogram-container">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            data={combinedData}
            margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
          >
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="bin" />
            <YAxis />
            <RechartsTooltip />
            <Legend />
            <Bar dataKey="original" name="原始数据" fill="#1890ff" opacity={0.7} />
            <Bar dataKey="synthetic" name="合成数据" fill="#52c41a" opacity={0.7} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    );
  }
  
  // 渲染箱线图
  const renderBoxPlot = () => {
    if (!evaluationResult || !evaluationResult.visualization_data || !evaluationResult.visualization_data.detailed_comparison) {
      return <div>暂无数据</div>;
    }
    
    const detailedData = evaluationResult.visualization_data.detailed_comparison;
    
    // 准备箱线图数据
    const boxPlotData = Object.entries(detailedData)
      .filter(([column, data]) => data.type === 'numerical')
      .slice(0, 5) // 只显示前5个数值列
      .map(([column, data]) => ({
        name: column,
        original: {
          min: data.original?.min || 0,
          q1: data.original?.q25 || 0,
          median: data.original?.median || 0,
          q3: data.original?.q75 || 0,
          max: data.original?.max || 0
        },
        synthetic: {
          min: data.synthetic?.min || 0,
          q1: data.synthetic?.q25 || 0,
          median: data.synthetic?.median || 0,
          q3: data.synthetic?.q75 || 0,
          max: data.synthetic?.max || 0
        }
      }));
    
    return (
      <div className="box-plot-container">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            data={boxPlotData}
            margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
          >
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="name" />
            <YAxis />
            <RechartsTooltip />
            <Legend />
            <Bar dataKey="original.median" name="原始数据中位数" fill="#1890ff" />
            <Bar dataKey="synthetic.median" name="合成数据中位数" fill="#52c41a" />
          </BarChart>
        </ResponsiveContainer>
      </div>
    );
  }

  return (
    <div className="quality-evaluation-container">
      <h2>数据质量评估</h2>
      <Tabs activeKey={activeTab} onChange={setActiveTab}>
        <TabPane tab="评估设置" key="1">
          <Card title="选择数据">
            <Form form={form} onFinish={onFinish} layout="vertical">
              <Form.Item
                name="original_table_ids"
                label="选择原始数据表"
                rules={[{ required: true, message: '请选择原始数据表' }]}
              >
                <Select
                  mode="multiple"
                  placeholder="请选择原始数据表"
                  loading={loading}
                  disabled={loading}
                  onChange={handleTableSelectionChange}
                  showSearch
                  optionFilterProp="children"
                  filterOption={(input, option) =>
                    option.children.toLowerCase().indexOf(input.toLowerCase()) >= 0
                  }
                >
                  {dataTables.map(table => (
                    <Select.Option key={table.id} value={table.id}>
                      {table.table_name} ({table.file_name})
                    </Select.Option>
                  ))}
                </Select>
              </Form.Item>
              
              {/* 显示选中数据表对应的合成任务 */}
              {selectedTables.length > 0 && (
                <Form.Item
                  label="相关合成任务"
                >
                  <div>
                    {getRelatedTasks(selectedTables).length > 0 ? (
                      getRelatedTasks(selectedTables).map(task => (
                        <Card key={task.task_id} size="small" style={{ marginBottom: '10px' }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <Tag color="blue">任务ID: {task.task_id}</Tag>
                            <Tag color={
                              task.status === 'completed' ? 'success' : 
                              task.status === 'failed' ? 'error' : 'processing'
                            }>
                              {task.status === 'completed' ? '已完成' : 
                               task.status === 'failed' ? '失败' : '进行中'}
                            </Tag>
                          </div>
                          <div style={{ marginTop: '8px' }}>
                            <div><strong>描述:</strong> {task.description || '无描述'}</div>
                            <div><strong>创建时间:</strong> {task.created_at || '未知'}</div>
                            {task.result_path && (
                              <div style={{ marginTop: '4px' }}>
                                <strong>合成数据路径:</strong> 
                                <Input size="small" value={task.result_path} readOnly />
                              </div>
                            )}
                          </div>
                        </Card>
                      ))
                    ) : (
                      <div>暂无相关合成任务</div>
                    )}
                  </div>
                </Form.Item>
              )}
              
              <Form.Item
                name="synthetic_data_path"
                label="合成数据文件路径"
              >
                <Input placeholder="请输入合成数据文件路径" />
              </Form.Item>
              
              <Form.Item label="或上传合成数据文件">
                <Upload
                  beforeUpload={() => false}
                  onChange={({ fileList }) => setFileList(fileList)}
                  fileList={fileList}
                  maxCount={1}
                  disabled={uploading}
                >
                  <Button icon={<UploadOutlined />} loading={uploading}>
                    选择文件
                  </Button>
                </Upload>
              </Form.Item>
              
              <Form.Item>
                <Space>
                  <Button type="primary" htmlType="submit" loading={loading}>
                    开始评估
                  </Button>
                  <Button onClick={() => form.resetFields()}>重置</Button>
                </Space>
              </Form.Item>
            </Form>
          </Card>
        </TabPane>
        
        <TabPane tab="评估结果" key="2" disabled={!evaluationResult}>
          {loading ? (
            <div style={{ textAlign: 'center', padding: '50px' }}>
              <Spin size="large" />
              <div style={{ marginTop: '10px' }}>正在评估数据质量...</div>
            </div>
          ) : evaluationResult ? (
            <div className="quality-evaluation-content">
              {renderCharts()}
            </div>
          ) : (
            <div style={{ textAlign: 'center', padding: '50px' }}>
              <div>请先完成数据质量评估</div>
            </div>
          )}
        </TabPane>
      </Tabs>
    </div>
  );
};

export default QualityEvaluation;