import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Route, Routes, Link, useLocation } from 'react-router-dom';
import RiskQuiz from './components/RiskQuiz';
import TargetAllocation from './components/TargetAllocation';
import Portfolio from './components/Portfolio';
import Login from './components/Login';
import Register from './components/Register';
import Dashboard from './components/Dashboard';
import AllocationView from './components/AllocationView';
import RebalanceTab from './components/RebalanceTab';
import PortfolioEntry from './components/PortfolioEntry';
import RecommendationsTab from './components/RecommendationsTab';
import CsvUpload from './components/CsvUpload';
import BacktestTab from './components/BacktestTab';
import Settings from './components/Settings';


function App() {
  const location = useLocation();
  const [isLoggedIn, setIsLoggedIn] = useState(!!localStorage.getItem('token'));

  useEffect(() => {
    const handleStorageChange = () => {
      setIsLoggedIn(!!localStorage.getItem('token'));
    };
    window.addEventListener('storage', handleStorageChange);
    return () => {
      window.removeEventListener('storage', handleStorageChange);
    };
  }, []);

  return (
    <>
      <div className="jumbotron jumbotron-fluid bg-primary text-white text-center py-3">
        <div className="container">
          <h1 className="display-4">Portfolio Balancer</h1>
        </div>
      </div>

      <nav className="navbar navbar-expand-lg navbar-light bg-light">
        <div className="container-fluid">
          <button className="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav" aria-controls="navbarNav" aria-expanded="false" aria-label="Toggle navigation">
            <span className="navbar-toggler-icon"></span>
          </button>
          <div className="collapse navbar-collapse justify-content-center" id="navbarNav">
            <ul className="navbar-nav">
              {!isLoggedIn && (
                <>
                  <li className="nav-item">
                    <Link className={`nav-link ${location.pathname === '/login' ? 'active-link' : ''}`} to="/login">Login</Link>
                  </li>
                  <li className="nav-item">
                    <Link className={`nav-link ${location.pathname === '/register' ? 'active-link' : ''}`} to="/register">Register</Link>
                  </li>
                </>
              )}
              {isLoggedIn && (
                <>
                  <li className="nav-item">
                    <Link className={`nav-link ${location.pathname === '/' ? 'active-link' : ''}`} to="/">Dashboard</Link>
                  </li>
                  <li className="nav-item">
                    <Link className={`nav-link ${location.pathname === '/portfolio' ? 'active-link' : ''}`} to="/portfolio">Portfolio</Link>
                  </li>
                  <li className="nav-item">
                    <Link className={`nav-link ${location.pathname === '/target-allocation' ? 'active-link' : ''}`} to="/target-allocation">Target Allocation</Link>
                  </li>
                  <li className="nav-item">
                    <Link className={`nav-link ${location.pathname === '/risk-quiz' ? 'active-link' : ''}`} to="/risk-quiz">Risk Quiz</Link>
                  </li>
                  <li className="nav-item">
                    <Link className={`nav-link ${location.pathname === '/rebalance' ? 'active-link' : ''}`} to="/rebalance">Rebalance</Link>
                  </li>
                  <li className="nav-item">
                    <Link className={`nav-link ${location.pathname === '/recommendations' ? 'active-link' : ''}`} to="/recommendations">Recommendations</Link>
                  </li>
                  <li className="nav-item">
                    <Link className={`nav-link ${location.pathname === '/backtest' ? 'active-link' : ''}`} to="/backtest">Backtest</Link>
                  </li>
                  <li className="nav-item">
                    <Link className={`nav-link ${location.pathname === '/settings' ? 'active-link' : ''}`} to="/settings">Settings</Link>
                  </li>
                  <li className="nav-item">
                    <button className="nav-link btn btn-link" onClick={() => { localStorage.removeItem('token'); setIsLoggedIn(false); }}>Logout</button>
                  </li>
                </>
              )}
            </ul>
          </div>
        </div>
      </nav>

      <div className="container mt-4">
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/risk-quiz" element={<RiskQuiz />} />
          <Route path="/target-allocation" element={<TargetAllocation />} />
          <Route path="/portfolio" element={<Portfolio />} />
          <Route path="/portfolio-entry" element={<PortfolioEntry />} />
          <Route path="/csv-upload" element={<CsvUpload />} />
          <Route path="/" element={<Dashboard />} />
          <Route path="/allocation" element={<AllocationView />} />
          <Route path="/rebalance" element={<RebalanceTab />} />
          <Route path="/recommendations" element={<RecommendationsTab />} />
          <Route path="/backtest" element={<BacktestTab />} />
          <Route path="/settings" element={<Settings />} />
        </Routes>
      </div>
      <Disclaimer />
    </>
  );
}

function Disclaimer() {
  return (
    <div style={{
      position: 'fixed',
      bottom: 0,
      left: 0,
      width: '100%',
      backgroundColor: '#f8d7da',
      color: '#721c24',
      padding: '10px',
      textAlign: 'center',
      fontSize: '0.8em',
      borderTop: '1px solid #f5c6cb'
    }}>
      <strong>Disclaimer:</strong> This application is for educational purposes only and does NOT execute real trades. All rebalancing and recommendations are hypothetical.
    </div>
  );
}

export default App;