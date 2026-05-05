import { useState, useEffect } from 'react';
import { Activity, HardDrive, Cpu, Network, AlertTriangle, CheckCircle, Server } from 'lucide-react';

function App() {
  const [servers, setServers] = useState([]);
  const [connected, setConnected] = useState(false);
  const [selectedServer, setSelectedServer] = useState(null);

  useEffect(() => {
    // Connect to FastAPI WebSocket
    const wsUrl = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws/stream';
    const ws = new WebSocket(wsUrl);
    
    ws.onopen = () => {
      console.log('Connected to ML Stream');
      setConnected(true);
    };

    ws.onmessage = (event) => {
      const msg = JSON.parse(event.data);
      if (msg.type === 'metrics_update') {
        setServers(msg.data);
        // Update selected server if one is selected
        if (selectedServer) {
          const updated = msg.data.find(s => s.server_id === selectedServer.server_id);
          if (updated) setSelectedServer(updated);
        }
      } else if (msg.error) {
        console.error("Backend Error:", msg.error);
      }
    };

    ws.onclose = () => {
      console.log('Disconnected');
      setConnected(false);
    };

    return () => {
      ws.close();
    };
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // Get alerts (Critical servers)
  const criticalServers = servers.filter(s => s.status === 'Critical');

  return (
    <div className="dashboard-container">
      <header className="header">
        <h1>Global Data Center Health</h1>
        <div className="pulse-indicator">
          <div className="pulse-dot" style={{ backgroundColor: connected ? 'var(--accent-cyan)' : 'var(--status-critical)' }}></div>
          {connected ? 'LIVE STREAM ACTIVE' : 'DISCONNECTED'}
        </div>
      </header>

      <div className="grid-layout">
        <div className="left-column" style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          
          {/* Server Grid Panel */}
          <div className="panel">
            <h2 className="panel-title"><Server size={18} /> Infrastructure Fleet</h2>
            <div className="server-grid">
              {servers.length === 0 ? (
                <div style={{ color: 'var(--text-secondary)' }}>Waiting for telemetry data...</div>
              ) : (
                servers.map((srv) => (
                  <div 
                    key={srv.server_id} 
                    className={`server-node ${srv.status.toLowerCase()}`}
                    onClick={() => setSelectedServer(srv)}
                  >
                    <div className="node-icon">
                      {srv.status === 'Healthy' ? <CheckCircle size={24} /> : 
                       srv.status === 'Warning' ? <Activity size={24} /> : 
                       <AlertTriangle size={24} />}
                    </div>
                    <div className="node-name">{srv.server_id}</div>
                    <div className="node-dc">{srv.data_center}</div>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Selected Server Details Panel */}
          {selectedServer && (
            <div className="panel" style={{ animation: 'slide-in 0.3s ease-out' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <h2 className="panel-title">
                  <Activity size={18} /> Server Diagnostics: {selectedServer.server_id}
                </h2>
                <span className="alert-prob" style={{ 
                  background: selectedServer.status === 'Healthy' ? 'rgba(0,230,118,0.2)' : 
                              selectedServer.status === 'Warning' ? 'rgba(255,234,0,0.2)' : 'rgba(255,23,68,0.2)',
                  color: selectedServer.status === 'Healthy' ? 'var(--status-healthy)' : 
                         selectedServer.status === 'Warning' ? 'var(--status-warning)' : 'var(--status-critical)'
                }}>
                  Fail Prob: {((selectedServer.failure_probability || 0) * 100).toFixed(1)}%
                </span>
              </div>
              
              <div className="metrics-row">
                <div className="metric-box">
                  <Cpu size={24} color="var(--accent-cyan)" style={{ margin: '0 auto' }}/>
                  <div className="metric-val">{selectedServer.cpu_usage ? selectedServer.cpu_usage.toFixed(1) : 'NaN'}%</div>
                  <div className="metric-label">CPU</div>
                </div>
                <div className="metric-box">
                  <HardDrive size={24} color="var(--accent-cyan)" style={{ margin: '0 auto' }}/>
                  <div className="metric-val">{selectedServer.memory_usage ? selectedServer.memory_usage.toFixed(1) : 'NaN'}%</div>
                  <div className="metric-label">Memory</div>
                </div>
                <div className="metric-box">
                  <Activity size={24} color="var(--accent-cyan)" style={{ margin: '0 auto' }}/>
                  <div className="metric-val">{selectedServer.disk_io ? selectedServer.disk_io.toFixed(1) : 'NaN'}</div>
                  <div className="metric-label">Disk I/O</div>
                </div>
                <div className="metric-box">
                  <Network size={24} color="var(--accent-cyan)" style={{ margin: '0 auto' }}/>
                  <div className="metric-val">{selectedServer.network_latency ? selectedServer.network_latency.toFixed(1) : 'NaN'}ms</div>
                  <div className="metric-label">Latency</div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Right Column: Alerts Feed */}
        <div className="right-column">
          <div className="panel" style={{ height: '100%' }}>
            <h2 className="panel-title" style={{ color: 'var(--status-critical)' }}>
              <AlertTriangle size={18} /> Proactive Alerts
            </h2>
            <div className="alerts-list">
              {criticalServers.length === 0 ? (
                <div style={{ color: 'var(--text-secondary)', fontSize: '0.8rem' }}>
                  No active critical alerts. All systems healthy.
                </div>
              ) : (
                criticalServers.map(srv => (
                  <div key={srv.server_id} className="alert-item">
                    <div className="alert-header">
                      <span className="alert-title">{srv.server_id} ({srv.data_center})</span>
                      <span className="alert-prob">{(srv.failure_probability * 100).toFixed(1)}% Prob</span>
                    </div>
                    <div className="alert-body">
                      Imminent failure predicted based on telemetry anomalies.
                    </div>
                    <button className="action-btn">
                      Auto-Migrate Workloads
                    </button>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;
