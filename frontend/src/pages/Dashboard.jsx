import { useState, useEffect } from 'react'
import { Card, Row, Col, Statistic, Button, Space, Table, Tag, Progress } from 'antd'
import {
    PlayCircleOutlined,
    PauseCircleOutlined,
    ThunderboltOutlined,
    SafetyOutlined,
    CloudOutlined,
    RocketOutlined
} from '@ant-design/icons'
import { LineChart, Line, AreaChart, Area, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'

const Dashboard = () => {
    const [engineRunning, setEngineRunning] = useState(false)
    const [stats, setStats] = useState({
        totalPackets: 0,
        realPackets: 0,
        dummyPackets: 0,
        throughput: 0,
        overhead: 0
    })
    const [trafficData, setTrafficData] = useState([])
    const [recentPackets, setRecentPackets] = useState([])

    // Simulate real-time data updates
    useEffect(() => {
        if (!engineRunning) return

        const interval = setInterval(() => {
            const newPacket = {
                id: Date.now(),
                timestamp: new Date().toLocaleTimeString(),
                type: Math.random() > 0.5 ? 'Real' : 'Dummy',
                size: Math.floor(Math.random() * 1400) + 100,
                iat: (Math.random() * 100).toFixed(2),
                encrypted: true
            }

            setRecentPackets(prev => [newPacket, ...prev].slice(0, 10))

            setStats(prev => ({
                totalPackets: prev.totalPackets + 1,
                realPackets: prev.realPackets + (newPacket.type === 'Real' ? 1 : 0),
                dummyPackets: prev.dummyPackets + (newPacket.type === 'Dummy' ? 1 : 0),
                throughput: Math.floor(Math.random() * 1000) + 500,
                overhead: ((prev.dummyPackets + (newPacket.type === 'Dummy' ? 1 : 0)) / (prev.totalPackets + 1) * 100).toFixed(1)
            }))

            setTrafficData(prev => {
                const newData = [...prev, {
                    time: new Date().toLocaleTimeString(),
                    packets: Math.floor(Math.random() * 50) + 20,
                    size: newPacket.size
                }]
                return newData.slice(-20)
            })
        }, 1000)

        return () => clearInterval(interval)
    }, [engineRunning])

    const columns = [
        {
            title: 'Time',
            dataIndex: 'timestamp',
            key: 'timestamp',
            width: 120
        },
        {
            title: 'Type',
            dataIndex: 'type',
            key: 'type',
            width: 100,
            render: (type) => (
                <Tag color={type === 'Real' ? 'blue' : 'orange'}>
                    {type}
                </Tag>
            )
        },
        {
            title: 'Size (bytes)',
            dataIndex: 'size',
            key: 'size',
            width: 120
        },
        {
            title: 'IAT (ms)',
            dataIndex: 'iat',
            key: 'iat',
            width: 100
        },
        {
            title: 'Encrypted',
            dataIndex: 'encrypted',
            key: 'encrypted',
            width: 100,
            render: (encrypted) => (
                <Tag color={encrypted ? 'green' : 'red'}>
                    {encrypted ? '✓' : '✗'}
                </Tag>
            )
        }
    ]

    return (
        <div style={{ maxWidth: '1600px', margin: '0 auto' }}>
            {/* Control Panel */}
            <Card style={{ marginBottom: 24 }}>
                <Space size="large">
                    <Button
                        type="primary"
                        size="large"
                        icon={engineRunning ? <PauseCircleOutlined /> : <PlayCircleOutlined />}
                        onClick={() => setEngineRunning(!engineRunning)}
                    >
                        {engineRunning ? 'Stop Engine' : 'Start Engine'}
                    </Button>
                    <Button
                        size="large"
                        icon={<ThunderboltOutlined />}
                        disabled={!engineRunning}
                    >
                        Simulate User Action
                    </Button>
                    <div style={{
                        padding: '8px 16px',
                        background: engineRunning ? '#52c41a' : '#d9d9d9',
                        borderRadius: '8px',
                        color: '#fff',
                        fontWeight: 'bold'
                    }}>
                        {engineRunning ? '● RUNNING' : '○ STOPPED'}
                    </div>
                </Space>
            </Card>

            {/* Statistics Cards */}
            <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
                <Col xs={24} sm={12} lg={6}>
                    <Card>
                        <Statistic
                            title="Total Packets"
                            value={stats.totalPackets}
                            prefix={<CloudOutlined />}
                            valueStyle={{ color: '#3f8600' }}
                        />
                    </Card>
                </Col>
                <Col xs={24} sm={12} lg={6}>
                    <Card>
                        <Statistic
                            title="Real Packets"
                            value={stats.realPackets}
                            prefix={<SafetyOutlined />}
                            valueStyle={{ color: '#1890ff' }}
                        />
                    </Card>
                </Col>
                <Col xs={24} sm={12} lg={6}>
                    <Card>
                        <Statistic
                            title="Dummy Packets"
                            value={stats.dummyPackets}
                            prefix={<RocketOutlined />}
                            valueStyle={{ color: '#faad14' }}
                        />
                    </Card>
                </Col>
                <Col xs={24} sm={12} lg={6}>
                    <Card>
                        <Statistic
                            title="Throughput"
                            value={stats.throughput}
                            suffix="pkt/s"
                            valueStyle={{ color: '#cf1322' }}
                        />
                    </Card>
                </Col>
            </Row>

            {/* Overhead Progress */}
            <Card title="Traffic Overhead" style={{ marginBottom: 24 }}>
                <Progress
                    percent={parseFloat(stats.overhead)}
                    status={stats.overhead > 70 ? 'exception' : stats.overhead > 40 ? 'normal' : 'success'}
                    strokeColor={{
                        '0%': '#108ee9',
                        '100%': '#87d068',
                    }}
                />
                <div style={{ marginTop: 8, color: '#888' }}>
                    Dummy packets: {stats.dummyPackets} / Total: {stats.totalPackets} ({stats.overhead}%)
                </div>
            </Card>

            {/* Charts */}
            <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
                <Col xs={24} lg={12}>
                    <Card title="Traffic Flow (Packets/sec)">
                        <ResponsiveContainer width="100%" height={300}>
                            <AreaChart data={trafficData}>
                                <CartesianGrid strokeDasharray="3 3" />
                                <XAxis dataKey="time" />
                                <YAxis />
                                <Tooltip />
                                <Area type="monotone" dataKey="packets" stroke="#1890ff" fill="#1890ff" fillOpacity={0.6} />
                            </AreaChart>
                        </ResponsiveContainer>
                    </Card>
                </Col>
                <Col xs={24} lg={12}>
                    <Card title="Packet Size Distribution">
                        <ResponsiveContainer width="100%" height={300}>
                            <BarChart data={trafficData}>
                                <CartesianGrid strokeDasharray="3 3" />
                                <XAxis dataKey="time" />
                                <YAxis />
                                <Tooltip />
                                <Bar dataKey="size" fill="#52c41a" />
                            </BarChart>
                        </ResponsiveContainer>
                    </Card>
                </Col>
            </Row>

            {/* Recent Packets Table */}
            <Card title="Live Packet Log" extra={<Tag color="green">Real-time</Tag>}>
                <Table
                    columns={columns}
                    dataSource={recentPackets}
                    rowKey="id"
                    pagination={false}
                    size="small"
                />
            </Card>
        </div>
    )
}

export default Dashboard
