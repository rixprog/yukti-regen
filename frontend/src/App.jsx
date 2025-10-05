import { useState } from 'react'
import './App.css'
import './colors.css'
import RealEnergySitingMap from './components/RealEnergySitingMap'
import SmartAssistant from './components/SmartAssistant'
import AIImageProcessor from './components/AIImageProcessor'

function App() {
  const [count, setCount] = useState(0)
  const [activeTab, setActiveTab] = useState('dashboard')

  return (
    <div className="App">
      {/* Sidebar */}
      <aside className="sidebar">
        <div className="sidebar-header">
          <div className="sidebar-logo">Yukti Regen</div>
        </div>
        <nav className="sidebar-nav">
          <div className="nav-item">
            <a 
              href="#" 
              className={`nav-link ${activeTab === 'dashboard' ? 'active' : ''}`}
              onClick={(e) => { e.preventDefault(); setActiveTab('dashboard'); }}
            >
              <svg className="nav-icon" viewBox="0 0 24 24">
                <path d="M3 13h8V3H3v10zm0 8h8v-6H3v6zm10 0h8V11h-8v10zm0-18v6h8V3h-8z"/>
              </svg>
              Dashboard
            </a>
          </div>
          <div className="nav-item">
            <a 
              href="#" 
              className={`nav-link ${activeTab === 'siting' ? 'active' : ''}`}
              onClick={(e) => { e.preventDefault(); setActiveTab('siting'); }}
            >
              <svg className="nav-icon" viewBox="0 0 24 24">
                <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>
              </svg>
              Energy Siting
            </a>
          </div>
          <div className="nav-item">
            <a 
              href="#" 
              className={`nav-link ${activeTab === 'analytics' ? 'active' : ''}`}
              onClick={(e) => { e.preventDefault(); setActiveTab('analytics'); }}
            >
              <svg className="nav-icon" viewBox="0 0 24 24">
                <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
              </svg>
              Analytics
            </a>
          </div>
          <div className="nav-item">
            <a 
              href="#" 
              className={`nav-link ${activeTab === 'sustainability' ? 'active' : ''}`}
              onClick={(e) => { e.preventDefault(); setActiveTab('sustainability'); }}
            >
              <svg className="nav-icon" viewBox="0 0 24 24">
                <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>
              </svg>
              Sustainability
            </a>
          </div>
          <div className="nav-item">
            <a 
              href="#" 
              className={`nav-link ${activeTab === 'assistant' ? 'active' : ''}`}
              onClick={(e) => { e.preventDefault(); setActiveTab('assistant'); }}
            >
              <svg className="nav-icon" viewBox="0 0 24 24">
                <path d="M12 1c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2zm-2 18c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2zm8-8c1.1 0 2-.9 2-2s-.9-2-2-2-2 .9-2 2 .9 2 2 2zm-8 8c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2zm8-8c1.1 0 2-.9 2-2s-.9-2-2-2-2 .9-2 2 .9 2 2 2z"/>
              </svg>
              Smart Assistant
            </a>
          </div>
          <div className="nav-item">
            <a 
              href="#" 
              className={`nav-link ${activeTab === 'ai-image' ? 'active' : ''}`}
              onClick={(e) => { e.preventDefault(); setActiveTab('ai-image'); }}
            >
              <svg className="nav-icon" viewBox="0 0 24 24">
                <path d="M14,2H6A2,2 0 0,0 4,4V20A2,2 0 0,0 6,22H18A2,2 0 0,0 20,20V8L14,2M18,20H6V4H13V9H18V20Z"/>
              </svg>
              AI Image Processor
            </a>
          </div>
        </nav>
      </aside>

      {/* Main Content */}
      <main className="main-content">
        {activeTab === 'dashboard' && (
          <>
            <div className="dashboard-header">
              <h1 className="dashboard-title">Energy & Sustainability Dashboard</h1>
              <p className="dashboard-subtitle">Monitor and manage your sustainable energy solutions</p>
            </div>

            {/* Metrics Grid */}
            <div className="metrics-grid">
              <div className="metric-card lavender">
                <div className="metric-header">
                  <div className="metric-title">Energy Generated</div>
                  <svg className="metric-icon" viewBox="0 0 24 24">
                    <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/>
                  </svg>
                </div>
                <div className="metric-value">2.4M</div>
                <div className="metric-change positive">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M7 14l5-5 5 5z"/>
                  </svg>
                  +12.5% from last month
                </div>
              </div>

              <div className="metric-card mint">
                <div className="metric-header">
                  <div className="metric-title">Carbon Saved</div>
                  <svg className="metric-icon" viewBox="0 0 24 24">
                    <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>
                  </svg>
                </div>
                <div className="metric-value">847</div>
                <div className="metric-change positive">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M7 14l5-5 5 5z"/>
                  </svg>
                  +8.2% from last month
                </div>
              </div>

              <div className="metric-card sky-blue">
                <div className="metric-header">
                  <div className="metric-title">Efficiency Rate</div>
                  <svg className="metric-icon" viewBox="0 0 24 24">
                    <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
                  </svg>
                </div>
                <div className="metric-value">94.2%</div>
                <div className="metric-change positive">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M7 14l5-5 5 5z"/>
                  </svg>
                  +2.1% from last month
                </div>
              </div>

              <div className="metric-card coral">
                <div className="metric-header">
                  <div className="metric-title">Active Projects</div>
                  <svg className="metric-icon" viewBox="0 0 24 24">
                    <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>
                  </svg>
                </div>
                <div className="metric-value">23</div>
                <div className="metric-change positive">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M7 14l5-5 5 5z"/>
                  </svg>
                  +3 new this week
                </div>
              </div>
            </div>

            {/* Features Grid */}
            <div className="features-grid">
              <div className="feature-card">
                <div className="feature-icon">⚡</div>
                <h3>Clean Energy</h3>
                <p>Harnessing renewable energy sources for a sustainable future with advanced monitoring and optimization.</p>
              </div>
              
              <div className="feature-card">
                <div className="feature-icon">🌱</div>
                <h3>Eco-Friendly</h3>
                <p>Reducing carbon footprint through innovative green technology and sustainable practices.</p>
              </div>
              
              <div className="feature-card">
                <div className="feature-icon">♻️</div>
                <h3>Sustainability</h3>
                <p>Building a circular economy for long-term environmental health and resource efficiency.</p>
              </div>
            </div>

            {/* Counter Section */}
            <div className="counter-section">
              <h2>Join the Movement</h2>
              <div className="counter">
                <span className="counter-number">{count}</span>
                <span className="counter-label">People Committed to Change</span>
              </div>
              <button 
                className="btn-counter"
                onClick={() => setCount(count + 1)}
              >
                Add Your Commitment
              </button>
            </div>
          </>
        )}

        {activeTab === 'siting' && (
          <RealEnergySitingMap />
        )}

        {activeTab === 'analytics' && (
          <div className="tab-content">
            <h2>Analytics</h2>
            <p>Advanced analytics and reporting features coming soon...</p>
          </div>
        )}

        {activeTab === 'sustainability' && (
          <div className="tab-content">
            <h2>Sustainability</h2>
            <p>Sustainability tracking and impact measurement tools coming soon...</p>
          </div>
        )}

        {activeTab === 'assistant' && (
          <SmartAssistant />
        )}

        {activeTab === 'ai-image' && (
          <AIImageProcessor />
        )}
      </main>
    </div>
  )
}

export default App
