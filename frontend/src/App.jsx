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
import RebalanceSuggestions from './components/RebalanceSuggestions'; // Import the new component


function App() {
  // For now, hardcode a user ID. In a real app, this would come from authentication context.
  const userId = 1;

  return (
    <Router>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/risk-quiz" element={<RiskQuiz userId={userId} />} />
        <Route path="/target-allocation" element={<TargetAllocation userId={userId} />} />
        <Route path="/portfolio" element={<Portfolio userId={userId} />} />
        <Route path="/portfolio-entry" element={<PortfolioEntry userId={userId} />} />
        <Route path="/csv-upload" element={<CsvUpload userId={userId} />} />
        <Route path="/rebalance-suggestions" element={<RebalanceSuggestions userId={userId} />} /> {/* New route */}
        <Route path="/" element={<Dashboard userId={userId} />} />
      </Routes>
    </Router>
  );
}

export default App;