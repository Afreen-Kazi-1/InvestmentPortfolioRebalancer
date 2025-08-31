import React from 'react';
import { BrowserRouter as Router, Route, Routes } from 'react-router-dom';
import RiskQuiz from './components/RiskQuiz';
import TargetAllocation from './components/TargetAllocation';
import Portfolio from './components/Portfolio';
import Login from './components/Login';
import Register from './components/Register';
import Dashboard from './components/Dashboard';
import PortfolioEntry from './components/PortfolioEntry';
import CsvUpload from './components/CsvUpload';


function App() {
  return (
    <Router>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/risk-quiz" element={<RiskQuiz />} />
        <Route path="/target-allocation" element={<TargetAllocation />} />
        <Route path="/portfolio" element={<Portfolio />} />
        <Route path="/portfolio-entry" element={<PortfolioEntry />} />
        <Route path="/csv-upload" element={<CsvUpload />} />
        <Route path="/" element={<Dashboard />} />
      </Routes>
    </Router>
  );
}

export default App;