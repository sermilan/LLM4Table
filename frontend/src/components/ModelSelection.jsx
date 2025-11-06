import React, { useState, useEffect } from 'react'
import { Card, Form, Select, Input, Button, Table, message, Space, Tag, Descriptions, Modal, Collapse, InputNumber, Switch, Row, Col, Tooltip } from 'antd'
import { QuestionCircleOutlined } from '@ant-design/icons'
import axios from 'axios'

const { Panel } = Collapse

// 参数说明字典
const PARAMETER_DESCRIPTIONS = {
  // OpenAI参数
  temperature: "控制生成文本的随机性。值越高，输出越随机；值越低，输出越确定。",
  max_tokens: "生成文本的最大token数量。",
  top_p: "控制生成文本的多样性。值为1时使用所有可能的token，值较低时只使用概率较高的token。",
  frequency_penalty: "减少重复词汇的使用。正值鼓励使用新词汇，负值鼓励重复使用已有词汇。",
  presence_penalty: "鼓励使用新的话题。正值鼓励讨论新话题，负值鼓励重复已有话题。",
  max_new_tokens: "生成新文本的最大token数量。",
  top_k: "在每一步生成时只考虑概率最高的k个token。",
  repetition_penalty: "控制重复token的惩罚程度。",
  default_distribution: "默认的概率分布类型。",
  enforce_min_max_values: "是否强制执行最小/最大值约束。",
  enforce_rounding: "是否强制执行四舍五入。",
  numerical_distributions: "数值列的分布类型配置。",
  model_type: "模型类型。",
  embedding_dim: "嵌入维度。",
  generator_dim: "生成器维度。",
  discriminator_dim: "判别器维度。",
  batch_size: "批次大小。",
  epochs: "训练轮数。",
  generator_lr: "生成器学习率。",
  openai_API_key: "OpenAI API密钥。",
  openai_API_url: "OpenAI API地址。",
  timeout: "超时时间(秒)。",
  gpt_model: "GPT模型。",
  query_batch: "查询批次大小。",
  // OpenDP参数
  epsilon: "差分隐私的ε参数，控制隐私预算，值越小隐私保护越强。",
  delta: "差分隐私的δ参数，通常设置为1/n^1.5。",
  algorithm: "使用的差分隐私算法类型。"
}

const ModelSelection = () => {
  const [form] = Form.useForm()
  const [availableModels, setAvailableModels] = useState([])
  const [providerModels, setProviderModels] = useState([])
  const [currentModel, setCurrentModel] = useState(null)
  const [loading, setLoading] = useState(false)
  const [testLoading, setTestLoading] = useState(false)
  const [parametersModalVisible, setParametersModalVisible] = useState(false)
  const [modelParameters, setModelParameters] = useState({})
  const [advancedParameters, setAdvancedParameters] = useState({})

  // 获取可用模型列表
  const fetchAvailableModels = async () => {
    try {
      setLoading(true)
      const response = await axios.get('/api/model/available')
      if (response.data.success) {
        setAvailableModels(response.data.data)
      } else {
        message.error('获取模型列表失败: ' + response.data.message)
      }
    } catch (error) {
      console.error('获取模型列表失败:', error)
      message.error('获取模型列表失败: ' + (error.response?.data?.detail || error.message || '网络错误'))
    } finally {
      setLoading(false)
    }
  }

  // 获取当前配置的模型
  const fetchCurrentModel = async () => {
    try {
      const response = await axios.get('/api/model/current')
      if (response.data.success) {
        setCurrentModel(response.data.data)
        form.setFieldsValue(response.data.data)
        // 设置参数
        setModelParameters(response.data.data.parameters || {})
        setAdvancedParameters(response.data.data.parameters || {})
      } else if (response.data.message) {
        // 没有配置模型是正常情况
        if (!response.data.message.includes('未配置')) {
          message.error('获取当前模型配置失败: ' + response.data.message)
        }
      }
    } catch (error) {
      // 没有配置模型是正常情况 (404错误)
      if (error.response?.status !== 404) {
        console.error('获取当前模型配置失败:', error)
        message.error('获取当前模型配置失败: ' + (error.response?.data?.detail || error.message || '网络错误'))
      }
    }
  }

  useEffect(() => {
    fetchAvailableModels()
    fetchCurrentModel()
  }, [])

  // 处理提供商选择变化
  const handleProviderChange = async (value) => {
    form.setFieldsValue({ model_name: undefined })
    
    try {
      setLoading(true)
      // 获取表单当前值
      const formValues = form.getFieldsValue()
      
      // 构造配置对象
      const config = {
        provider: value,
        api_key: formValues.api_key || '',
        base_url: formValues.base_url || '',
        model_name: ''
      }
      
      const response = await axios.post('/api/model/list-provider-models', config)
      if (response.data.success) {
        setProviderModels(response.data.data)
      } else {
        // 如果获取失败，使用默认模型列表
        const filtered = availableModels.filter(model => model.provider === value)
        setProviderModels(filtered)
      }
    } catch (error) {
      console.error('获取提供商模型列表失败:', error)
      // 出错时使用默认模型列表
      const filtered = availableModels.filter(model => model.provider === value)
      setProviderModels(filtered)
      message.error('获取提供商模型列表失败: ' + (error.response?.data?.detail || error.message || '网络错误'))
    } finally {
      setLoading(false)
    }
  }

  // 处理API密钥变化
  const handleApiKeyChange = async (e) => {
    const apiKey = e.target.value
    const provider = form.getFieldValue('provider')
    
    // 如果已经选择了提供商，获取模型列表
    if (provider) {
      try {
        setLoading(true)
        const config = {
          provider: provider,
          api_key: apiKey || '',
          base_url: form.getFieldValue('base_url') || '',
          model_name: ''
        }
        
        const response = await axios.post('/api/model/list-provider-models', config)
        if (response.data.success) {
          setProviderModels(response.data.data)
        }
      } catch (error) {
        console.error('获取提供商模型列表失败:', error)
        message.error('获取提供商模型列表失败: ' + (error.response?.data?.detail || error.message || '网络错误'))
      } finally {
        setLoading(false)
      }
    }
  }

  const onFinish = async (values) => {
    try {
      setLoading(true)
      const modelConfig = {
        model_name: values.model_name,
        provider: values.provider,
        api_key: values.api_key,
        base_url: values.base_url,
        parameters: advancedParameters
      }

      const response = await axios.post('/api/model/configure', modelConfig)
      if (response.data.success) {
        message.success('模型配置成功')
        setCurrentModel(response.data.data)
        setModelParameters(response.data.data.parameters || {})
      } else {
        message.error('模型配置失败: ' + response.data.message)
      }
    } catch (error) {
      console.error('模型配置失败:', error)
      message.error('模型配置失败: ' + (error.response?.data?.detail || error.message || '网络错误'))
    } finally {
      setLoading(false)
    }
  }

  // 测试模型连接
  const testModelConnection = async () => {
    try {
      setTestLoading(true)
      const values = await form.validateFields()
      
      const modelConfig = {
        model_name: values.model_name,
        provider: values.provider,
        api_key: values.api_key,
        base_url: values.base_url,
        parameters: advancedParameters
      }
      
      const response = await axios.post('/api/model/test-connection', modelConfig)
      if (response.data.success) {
        message.success(response.data.message)
      } else {
        message.error(response.data.message)
      }
    } catch (error) {
      console.error('模型连接测试失败:', error)
      message.error('模型连接测试失败: ' + (error.response?.data?.detail || error.message || '网络错误'))
    } finally {
      setTestLoading(false)
    }
  }

  const handleParameterTemplate = async (provider) => {
    try {
      const response = await axios.get(`/api/model/parameters/template/${provider}`)
      if (response.data.success) {
        setModelParameters(response.data.data)
        setAdvancedParameters(response.data.data)
        message.success(`已加载 ${provider} 参数模板`)
      } else {
        message.error('获取参数模板失败: ' + response.data.message)
      }
    } catch (error) {
      console.error('获取参数模板失败:', error)
      message.error('获取参数模板失败: ' + (error.response?.data?.detail || error.message || '网络错误'))
    }
  }

  // 更新参数值
  const updateParameter = (key, value) => {
    setAdvancedParameters(prev => ({
      ...prev,
      [key]: value
    }))
  }

  // 渲染带帮助标记的标签
  const renderLabelWithTooltip = (label, tooltip) => (
    <span>
      {label}
      <Tooltip title={tooltip}>
        <QuestionCircleOutlined style={{ marginLeft: 4, color: '#1890ff' }} />
      </Tooltip>
    </span>
  )

  // 渲染参数配置面板
  const renderParameterPanel = () => {
    const provider = form.getFieldValue('provider')
    
    if (provider === 'openai') {
      return (
        <div>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item label={renderLabelWithTooltip("Temperature", PARAMETER_DESCRIPTIONS.temperature)}>
                <InputNumber
                  min={0}
                  max={2}
                  step={0.1}
                  value={advancedParameters.temperature !== undefined ? advancedParameters.temperature : 0.7}
                  onChange={(value) => updateParameter('temperature', value)}
                  style={{ width: '100%' }}
                />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item label={renderLabelWithTooltip("Max Tokens", PARAMETER_DESCRIPTIONS.max_tokens)}>
                <InputNumber
                  min={1}
                  max={4096}
                  value={advancedParameters.max_tokens !== undefined ? advancedParameters.max_tokens : 1000}
                  onChange={(value) => updateParameter('max_tokens', value)}
                  style={{ width: '100%' }}
                />
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item label={renderLabelWithTooltip("Top P", PARAMETER_DESCRIPTIONS.top_p)}>
                <InputNumber
                  min={0}
                  max={1}
                  step={0.1}
                  value={advancedParameters.top_p !== undefined ? advancedParameters.top_p : 1.0}
                  onChange={(value) => updateParameter('top_p', value)}
                  style={{ width: '100%' }}
                />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item label={renderLabelWithTooltip("Frequency Penalty", PARAMETER_DESCRIPTIONS.frequency_penalty)}>
                <InputNumber
                  min={-2}
                  max={2}
                  step={0.1}
                  value={advancedParameters.frequency_penalty !== undefined ? advancedParameters.frequency_penalty : 0.0}
                  onChange={(value) => updateParameter('frequency_penalty', value)}
                  style={{ width: '100%' }}
                />
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item label={renderLabelWithTooltip("Presence Penalty", PARAMETER_DESCRIPTIONS.presence_penalty)}>
                <InputNumber
                  min={-2}
                  max={2}
                  step={0.1}
                  value={advancedParameters.presence_penalty !== undefined ? advancedParameters.presence_penalty : 0.0}
                  onChange={(value) => updateParameter('presence_penalty', value)}
                  style={{ width: '100%' }}
                />
              </Form.Item>
            </Col>
          </Row>
        </div>
      )
    } else if (provider === 'sdv') {
      return (
        <div>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item label={renderLabelWithTooltip("Default Distribution", PARAMETER_DESCRIPTIONS.default_distribution)}>
                <Select
                  value={advancedParameters.default_distribution !== undefined ? advancedParameters.default_distribution : "beta"}
                  onChange={(value) => updateParameter('default_distribution', value)}
                  style={{ width: '100%' }}
                >
                  <Select.Option value="beta">Beta</Select.Option>
                  <Select.Option value="gamma">Gamma</Select.Option>
                  <Select.Option value="gaussian">Gaussian</Select.Option>
                  <Select.Option value="uniform">Uniform</Select.Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item label={renderLabelWithTooltip("Enforce Min/Max Values", PARAMETER_DESCRIPTIONS.enforce_min_max_values)}>
                <Switch
                  checked={advancedParameters.enforce_min_max_values !== undefined ? advancedParameters.enforce_min_max_values : true}
                  onChange={(checked) => updateParameter('enforce_min_max_values', checked)}
                />
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item label={renderLabelWithTooltip("Enforce Rounding", PARAMETER_DESCRIPTIONS.enforce_rounding)}>
                <Switch
                  checked={advancedParameters.enforce_rounding !== undefined ? advancedParameters.enforce_rounding : true}
                  onChange={(checked) => updateParameter('enforce_rounding', checked)}
                />
              </Form.Item>
            </Col>
          </Row>
        </div>
      )
    } else if (provider === 'sdgx_statistics') {
      return (
        <div>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item label={renderLabelWithTooltip("Model Type", "统计模型类型")}>
                <Select
                  value={advancedParameters.model_type || "gaussian_copula"}
                  onChange={(value) => updateParameter('model_type', value)}
                  style={{ width: '100%' }}
                >
                  <Select.Option value="gaussian_multivariate">Gaussian Multivariate</Select.Option>
                  <Select.Option value="gaussian_copula">Gaussian Copula</Select.Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item label={renderLabelWithTooltip("Default Distribution", PARAMETER_DESCRIPTIONS.default_distribution)}>
                <Select
                  value={advancedParameters.default_distribution !== undefined ? advancedParameters.default_distribution : "beta"}
                  onChange={(value) => updateParameter('default_distribution', value)}
                  style={{ width: '100%' }}
                >
                  <Select.Option value="beta">Beta</Select.Option>
                  <Select.Option value="gamma">Gamma</Select.Option>
                  <Select.Option value="gaussian">Gaussian</Select.Option>
                  <Select.Option value="uniform">Uniform</Select.Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item label={renderLabelWithTooltip("Enforce Min/Max Values", PARAMETER_DESCRIPTIONS.enforce_min_max_values)}>
                <Switch
                  checked={advancedParameters.enforce_min_max_values !== undefined ? advancedParameters.enforce_min_max_values : true}
                  onChange={(checked) => updateParameter('enforce_min_max_values', checked)}
                />
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item label={renderLabelWithTooltip("Enforce Rounding", PARAMETER_DESCRIPTIONS.enforce_rounding)}>
                <Switch
                  checked={advancedParameters.enforce_rounding !== undefined ? advancedParameters.enforce_rounding : true}
                  onChange={(checked) => updateParameter('enforce_rounding', checked)}
                />
              </Form.Item>
            </Col>
          </Row>
        </div>
      )
    } else if (provider === 'sdgx_ml') {
      return (
        <div>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item label={renderLabelWithTooltip("Model Type", "机器学习模型类型")}>
                <Select
                  value={advancedParameters.model_type || "ctgan"}
                  onChange={(value) => updateParameter('model_type', value)}
                  style={{ width: '100%' }}
                >
                  <Select.Option value="ctgan">CTGAN</Select.Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item label={renderLabelWithTooltip("Embedding Dimension", "嵌入维度")}>
                <InputNumber
                  min={1}
                  value={advancedParameters.embedding_dim || 128}
                  onChange={(value) => updateParameter('embedding_dim', value)}
                  style={{ width: '100%' }}
                />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item label={renderLabelWithTooltip("Generator Dimensions", "生成器维度")}>
                <Input
                  value={JSON.stringify(advancedParameters.generator_dim || [256, 256])}
                  onChange={(e) => {
                    try {
                      const value = JSON.parse(e.target.value);
                      updateParameter('generator_dim', value);
                    } catch (e) {
                      // Ignore invalid JSON
                    }
                  }}
                  style={{ width: '100%' }}
                />
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item label={renderLabelWithTooltip("Discriminator Dimensions", "判别器维度")}>
                <Input
                  value={JSON.stringify(advancedParameters.discriminator_dim || [256, 256])}
                  onChange={(e) => {
                    try {
                      const value = JSON.parse(e.target.value);
                      updateParameter('discriminator_dim', value);
                    } catch (e) {
                      // Ignore invalid JSON
                    }
                  }}
                  style={{ width: '100%' }}
                />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item label={renderLabelWithTooltip("Batch Size", "批次大小")}>
                <InputNumber
                  min={1}
                  value={advancedParameters.batch_size || 500}
                  onChange={(value) => updateParameter('batch_size', value)}
                  style={{ width: '100%' }}
                />
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item label={renderLabelWithTooltip("Epochs", "训练轮数")}>
                <InputNumber
                  min={1}
                  value={advancedParameters.epochs || 300}
                  onChange={(value) => updateParameter('epochs', value)}
                  style={{ width: '100%' }}
                />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item label={renderLabelWithTooltip("Learning Rate", "学习率")}>
                <InputNumber
                  min={0}
                  step={0.0001}
                  value={advancedParameters.generator_lr || 0.0002}
                  onChange={(value) => updateParameter('generator_lr', value)}
                  style={{ width: '100%' }}
                />
              </Form.Item>
            </Col>
          </Row>
        </div>
      )
    } else if (provider === 'sdgx_llm') {
      return (
        <div>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item label={renderLabelWithTooltip("Model Type", "LLM模型类型")}>
                <Select
                  value={advancedParameters.model_type || "gpt"}
                  onChange={(value) => updateParameter('model_type', value)}
                  style={{ width: '100%' }}
                >
                  <Select.Option value="gpt">GPT</Select.Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item label={renderLabelWithTooltip("OpenAI API Key", "OpenAI API密钥")}>
                <Input.Password
                  value={advancedParameters.openai_API_key || ""}
                  onChange={(e) => updateParameter('openai_API_key', e.target.value)}
                  style={{ width: '100%' }}
                />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item label={renderLabelWithTooltip("OpenAI API URL", "OpenAI API地址")}>
                <Input
                  value={advancedParameters.openai_API_url || "https://api.openai.com/v1/"}
                  onChange={(e) => updateParameter('openai_API_url', e.target.value)}
                  style={{ width: '100%' }}
                />
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item label={renderLabelWithTooltip("Max Tokens", "最大Token数")}>
                <InputNumber
                  min={1}
                  value={advancedParameters.max_tokens || 4000}
                  onChange={(value) => updateParameter('max_tokens', value)}
                  style={{ width: '100%' }}
                />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item label={renderLabelWithTooltip("Temperature", "温度参数")}>
                <InputNumber
                  min={0}
                  max={2}
                  step={0.1}
                  value={advancedParameters.temperature || 0.1}
                  onChange={(value) => updateParameter('temperature', value)}
                  style={{ width: '100%' }}
                />
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item label={renderLabelWithTooltip("Timeout", "超时时间(秒)")}>
                <InputNumber
                  min={1}
                  value={advancedParameters.timeout || 90}
                  onChange={(value) => updateParameter('timeout', value)}
                  style={{ width: '100%' }}
                />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item label={renderLabelWithTooltip("GPT Model", "GPT模型")}>
                <Input
                  value={advancedParameters.gpt_model || "gpt-3.5-turbo"}
                  onChange={(e) => updateParameter('gpt_model', e.target.value)}
                  style={{ width: '100%' }}
                />
              </Form.Item>
            </Col>
          </Row>
        </div>
      )
    } else if (provider === 'huggingface') {
      return (
        <div>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item label={renderLabelWithTooltip("Temperature", PARAMETER_DESCRIPTIONS.temperature)}>
                <InputNumber
                  min={0}
                  max={2}
                  step={0.1}
                  value={advancedParameters.temperature !== undefined ? advancedParameters.temperature : 0.7}
                  onChange={(value) => updateParameter('temperature', value)}
                  style={{ width: '100%' }}
                />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item label={renderLabelWithTooltip("Max New Tokens", PARAMETER_DESCRIPTIONS.max_new_tokens)}>
                <InputNumber
                  min={1}
                  max={4096}
                  value={advancedParameters.max_new_tokens !== undefined ? advancedParameters.max_new_tokens : 1000}
                  onChange={(value) => updateParameter('max_new_tokens', value)}
                  style={{ width: '100%' }}
                />
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item label={renderLabelWithTooltip("Top K", PARAMETER_DESCRIPTIONS.top_k)}>
                <InputNumber
                  min={1}
                  max={100}
                  value={advancedParameters.top_k !== undefined ? advancedParameters.top_k : 50}
                  onChange={(value) => updateParameter('top_k', value)}
                  style={{ width: '100%' }}
                />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item label={renderLabelWithTooltip("Top P", PARAMETER_DESCRIPTIONS.top_p)}>
                <InputNumber
                  min={0}
                  max={1}
                  step={0.1}
                  value={advancedParameters.top_p !== undefined ? advancedParameters.top_p : 0.95}
                  onChange={(value) => updateParameter('top_p', value)}
                  style={{ width: '100%' }}
                />
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item label={renderLabelWithTooltip("Repetition Penalty", PARAMETER_DESCRIPTIONS.repetition_penalty)}>
                <InputNumber
                  min={0}
                  max={2}
                  step={0.1}
                  value={advancedParameters.repetition_penalty !== undefined ? advancedParameters.repetition_penalty : 1.0}
                  onChange={(value) => updateParameter('repetition_penalty', value)}
                  style={{ width: '100%' }}
                />
              </Form.Item>
            </Col>
          </Row>
        </div>
      )
    } else if (provider === 'siliconflow' || provider === 'aliyun') {
      return (
        <div>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item label={renderLabelWithTooltip("Temperature", PARAMETER_DESCRIPTIONS.temperature)}>
                <InputNumber
                  min={0}
                  max={2}
                  step={0.1}
                  value={advancedParameters.temperature !== undefined ? advancedParameters.temperature : 0.7}
                  onChange={(value) => updateParameter('temperature', value)}
                  style={{ width: '100%' }}
                />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item label={renderLabelWithTooltip("Max Tokens", PARAMETER_DESCRIPTIONS.max_tokens)}>
                <InputNumber
                  min={1}
                  max={4096}
                  value={advancedParameters.max_tokens !== undefined ? advancedParameters.max_tokens : 1000}
                  onChange={(value) => updateParameter('max_tokens', value)}
                  style={{ width: '100%' }}
                />
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item label={renderLabelWithTooltip("Top P", PARAMETER_DESCRIPTIONS.top_p)}>
                <InputNumber
                  min={0}
                  max={1}
                  step={0.1}
                  value={advancedParameters.top_p !== undefined ? advancedParameters.top_p : 0.95}
                  onChange={(value) => updateParameter('top_p', value)}
                  style={{ width: '100%' }}
                />
              </Form.Item>
            </Col>
          </Row>
        </div>
      )
    } else if (provider === 'opendp') {
      return (
        <div>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item label={renderLabelWithTooltip("Epsilon (隐私预算)", "差分隐私的隐私预算参数，值越小隐私保护越强")}>
                <InputNumber
                  min={0.1}
                  max={10}
                  step={0.1}
                  value={advancedParameters.epsilon !== undefined ? advancedParameters.epsilon : 1.0}
                  onChange={(value) => updateParameter('epsilon', value)}
                  style={{ width: '100%' }}
                />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item label={renderLabelWithTooltip("Delta", "差分隐私的δ参数，通常设置为1/n^1.5")}>
                <InputNumber
                  min={1e-10}
                  max={1e-5}
                  step={1e-7}
                  value={advancedParameters.delta !== undefined ? advancedParameters.delta : 1e-7}
                  onChange={(value) => updateParameter('delta', value)}
                  style={{ width: '100%' }}
                />
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item label={renderLabelWithTooltip("算法类型", "选择使用的差分隐私算法")}>
                <Select
                  value={advancedParameters.algorithm || "AIM"}
                  onChange={(value) => updateParameter('algorithm', value)}
                  style={{ width: '100%' }}
                >
                  <Select.Option value="AIM">AIM算法</Select.Option>
                  <Select.Option value="MST">MST算法</Select.Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>
        </div>
      )
    }
    
    return (
      <div>
        <p>当前提供商暂无特定参数配置</p>
      </div>
    )
  }

  const modelColumns = [
    {
      title: '模型名称',
      dataIndex: 'name',
      key: 'name',
    },
    {
      title: '提供商',
      dataIndex: 'provider',
      key: 'provider',
      render: (provider) => (
        <Tag color={
          provider === 'openai' ? 'blue' : 
          provider === 'huggingface' ? 'green' : 
          provider === 'siliconflow' ? 'purple' : 
          provider === 'aliyun' ? 'orange' : 
          provider === 'sdv' ? 'cyan' : 
          provider === 'opendp' ? 'magenta' : 'default'
        }>
          {provider === 'siliconflow' ? '硅基流动' : provider === 'aliyun' ? '阿里云' : provider === 'sdv' ? 'SDV' : provider === 'opendp' ? 'OpenDP' : provider}
        </Tag>
      ),
    },
    {
      title: '描述',
      dataIndex: 'description',
      key: 'description',
    },
    {
      title: '操作',
      key: 'action',
      render: (_, record) => (
        <Space size="middle">
          <Button 
            type="primary" 
            onClick={() => {
              form.setFieldsValue({
                model_name: record.id,
                provider: record.provider
              })
            }}
          >
            选择
          </Button>
          <Button 
            onClick={() => handleParameterTemplate(record.provider)}
          >
            参数模板
          </Button>
        </Space>
      ),
    },
  ]

  return (
    <div className="model-selection-container">
      <Card title="模型配置" style={{ marginBottom: 20 }}>
        <Form
          form={form}
          layout="vertical"
          onFinish={onFinish}
          initialValues={{
            model_name: '',
            provider: '',
            api_key: '',
            base_url: ''
          }}
        >
          <Form.Item
            name="provider"
            label="模型提供商"
            rules={[{ required: true, message: '请选择模型提供商' }]}
          >
            <Select 
              placeholder="请选择模型提供商"
              onChange={handleProviderChange}
            >
              <Select.Option value="openai">OpenAI</Select.Option>
              <Select.Option value="huggingface">Hugging Face</Select.Option>
              <Select.Option value="siliconflow">硅基流动</Select.Option>
              <Select.Option value="aliyun">阿里云</Select.Option>
              <Select.Option value="sdv">SDV</Select.Option>
              <Select.Option value="sdgx_statistics">SDGX统计模型</Select.Option>
              <Select.Option value="sdgx_ml">SDGX机器学习模型</Select.Option>
              <Select.Option value="sdgx_llm">SDGX LLM模型</Select.Option>
              <Select.Option value="opendp">OpenDP差分隐私模型</Select.Option>
            </Select>
          </Form.Item>

          <Form.Item
            name="api_key"
            label="API密钥"
          >
            <Input.Password placeholder="请输入API密钥" onChange={handleApiKeyChange} />
          </Form.Item>

          <Form.Item
            name="base_url"
            label="API基础URL"
          >
            <Input placeholder="请输入API基础URL（可选）" onChange={handleApiKeyChange} />
          </Form.Item>

          <Form.Item
            name="model_name"
            label="模型名称"
            rules={[{ required: true, message: '请选择模型名称' }]}
          >
            <Select
              showSearch
              placeholder="请选择模型（请先选择提供商并输入API密钥）"
              optionFilterProp="children"
            >
              {providerModels.map(model => (
                <Select.Option key={model.id} value={model.id}>
                  {model.name || model.id}
                </Select.Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit" loading={loading}>
                保存配置
              </Button>
              <Button onClick={testModelConnection} loading={testLoading}>
                测试连接
              </Button>
              <Button onClick={() => setParametersModalVisible(true)}>
                参数配置
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Card>

      <Card title="可用模型">
        <Table
          columns={modelColumns}
          dataSource={availableModels}
          loading={loading}
          rowKey="id"
          pagination={{
            pageSize: 5,
          }}
        />
      </Card>

      {/* 参数配置模态框 */}
      <Modal
        title="模型参数配置"
        visible={parametersModalVisible}
        onCancel={() => setParametersModalVisible(false)}
        onOk={() => setParametersModalVisible(false)}
        width={800}
      >
        <Collapse defaultActiveKey={['1']}>
          <Panel header="当前参数" key="1">
            <Descriptions bordered column={1}>
              {Object.entries(modelParameters).map(([key, value]) => (
                <Descriptions.Item label={renderLabelWithTooltip(key, PARAMETER_DESCRIPTIONS[key] || "无描述")} key={key}>
                  {typeof value === 'object' ? JSON.stringify(value) : String(value)}
                </Descriptions.Item>
              ))}
              {Object.keys(modelParameters).length === 0 && (
                <Descriptions.Item label="提示">暂无参数配置</Descriptions.Item>
              )}
            </Descriptions>
          </Panel>
          <Panel header="高级参数配置" key="2">
            {renderParameterPanel()}
          </Panel>
        </Collapse>
        <p style={{ marginTop: 16 }}>
          参数模板可通过选择模型提供商并点击"参数模板"按钮加载
        </p>
      </Modal>
    </div>
  )
}

export default ModelSelection