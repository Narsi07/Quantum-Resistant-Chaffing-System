import { useState } from 'react'
import { ConfigProvider, theme, Layout } from 'antd'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import Dashboard from './pages/Dashboard'
import './App.css'

const { Header, Content } = Layout

function App() {
    const [darkMode, setDarkMode] = useState(true)

    return (
        <ConfigProvider
            theme={{
                algorithm: darkMode ? theme.darkAlgorithm : theme.defaultAlgorithm,
                token: {
                    colorPrimary: '#1890ff',
                    borderRadius: 8,
                },
            }}
        >
            <Router>
                <Layout style={{ minHeight: '100vh' }}>
                    <Header style={{
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        padding: '0 24px',
                        background: darkMode ? '#001529' : '#fff',
                        borderBottom: `1px solid ${darkMode ? '#303030' : '#f0f0f0'}`
                    }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                            <div style={{
                                fontSize: '24px',
                                fontWeight: 'bold',
                                background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                                WebkitBackgroundClip: 'text',
                                WebkitTextFillColor: 'transparent',
                            }}>
                                🛡️ Quantum-Resistant Chaffing
                            </div>
                        </div>
                        <div style={{ color: darkMode ? '#fff' : '#000' }}>
                            Post-Quantum Metadata Obfuscation Layer
                        </div>
                    </Header>
                    <Content style={{ padding: '24px', background: darkMode ? '#141414' : '#f0f2f5' }}>
                        <Routes>
                            <Route path="/" element={<Dashboard />} />
                        </Routes>
                    </Content>
                </Layout>
            </Router>
        </ConfigProvider>
    )
}

export default App
