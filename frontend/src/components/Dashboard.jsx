import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';

const Dashboard = () => {
  const [portfolioSummary, setPortfolioSummary] = useState({
    totalValue: 0,
    profitLoss: 0,
    riskBadge: 'N/A'
  });

  useEffect(() => {
    // Fetch portfolio summary data from the backend
    // This is a placeholder, replace with actual API call
    const fetchPortfolioSummary = async () => {
      try {
        const userId = 1; // Hardcoded for now
        const token = localStorage.getItem('token');

        if (!token) {
          console.error('Authentication token not found. Please log in.');
          setPortfolioSummary({
            totalValue: 0,
            profitLoss: 0,
            riskBadge: 'N/A'
          });
          return;
        }

        const response = await fetch(`http://127.0.0.1:5000/portfolio/snapshot?user_id=${userId}`, {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });
        const data = await response.json();
        console.log('API Response Data:', data); // Log the data received
        setPortfolioSummary(data);
      } catch (error) {
        console.error('Error fetching portfolio summary:', error);
        // Set default or error values if API call fails
        setPortfolioSummary({
          totalValue: 0, // Initialize as number
          profitLoss: 0, // Initialize as number
          riskBadge: 'N/A'
        });
      }
    };

    fetchPortfolioSummary();
  }, []);

  return (
    <div className="container mt-5">
      <h2>Dashboard</h2>
      <div className="row">
        <div className="col-md-4">
          <div className="card text-center bg-light mb-3">
            <div className="card-body">
              <h5 className="card-title text-primary">Total Portfolio Value</h5>
              <p className="card-text display-4 text-dark">${portfolioSummary.totalValue.toFixed(2)}</p>
            </div>
          </div>
        </div>
        <div className="col-md-4">
          <div className="card text-center bg-light mb-3">
            <div className="card-body">
              <h5 className="card-title text-primary">Profit/Loss</h5>
              <p className={`card-text display-4 ${typeof portfolioSummary.profitLoss === 'number' && portfolioSummary.profitLoss >= 0 ? 'text-success' : 'text-danger'}`}>
                ${typeof portfolioSummary.profitLoss === 'number' ? portfolioSummary.profitLoss.toFixed(2) : 'N/A'}
              </p>
            </div>
          </div>
        </div>
        <div className="col-md-4">
          <div className="card text-center bg-light mb-3">
            <div className="card-body">
              <h5 className="card-title text-primary">Risk Badge</h5>
              <p className="card-text display-4 text-dark">{portfolioSummary.riskBadge}</p>
            </div>
          </div>
        </div>
      </div>

      <div className="mt-5">
        <h3>Portfolio Insights</h3>
        <div id="portfolioCarousel" className="carousel slide" data-bs-ride="carousel">
          <div className="carousel-inner">
            <div className="carousel-item active">
              <img src="/images/growth_chart.png" className="d-block w-100" alt="Stock Growth" />
              <div className="carousel-caption d-none d-md-block">
                <h5>Stock Performance</h5>
                <p>Visualize the growth of your equity investments over time.</p>
              </div>
            </div>
            <div className="carousel-item">
              <img src="https://via.placeholder.com/800x400/87CEEB/000000?text=Bond+Performance+Chart" className="d-block w-100" alt="Bond Performance" />
              <div className="carousel-caption d-none d-md-block">
                <h5>Bond Performance</h5>
                <p>Track the stability and returns of your bond holdings.</p>
              </div>
            </div>
            <div className="carousel-item">
              <img src="https://via.placeholder.com/800x400/6495ED/000000?text=Diversified+Asset+Growth" className="d-block w-100" alt="Diversified Growth" />
              <div className="carousel-caption d-none d-md-block">
                <h5>Diversified Asset Growth</h5>
                <p>See how different asset classes contribute to your overall portfolio.</p>
              </div>
            </div>
          </div>
          <button className="carousel-control-prev" type="button" data-bs-target="#portfolioCarousel" data-bs-slide="prev">
            <span className="carousel-control-prev-icon" aria-hidden="true"></span>
            <span className="visually-hidden">Previous</span>
          </button>
          <button className="carousel-control-next" type="button" data-bs-target="#portfolioCarousel" data-bs-slide="next">
            <span className="carousel-control-next-icon" aria-hidden="true"></span>
            <span className="visually-hidden">Next</span>
          </button>
        </div>
      </div>

      <div className="mt-4">
        <h3>Features</h3>
        <div className="row row-cols-1 row-cols-md-3 g-4">
          <div className="col">
            <div className="card h-100 text-center">
              {/* Removed image for Portfolio tile */}
              <div className="card-body">
                <h5 className="card-title">View/Edit Portfolio</h5>
                <p className="card-text">Manage your current investment holdings.</p>
                <Link to="/portfolio" className="btn btn-primary">Go to Portfolio</Link>
              </div>
            </div>
          </div>
          <div className="col">
            <div className="card h-100 text-center">
              {/* Removed image for Target Allocation tile */}
              <div className="card-body">
                <h5 className="card-title">Set Target Allocation</h5>
                <p className="card-text">Define your desired asset allocation strategy.</p>
                <Link to="/target-allocation" className="btn btn-primary">Set Allocation</Link>
              </div>
            </div>
          </div>
          <div className="col">
            <div className="card h-100 text-center">
              {/* Removed image for Risk Quiz tile */}
              <div className="card-body">
                <h5 className="card-title">Take Risk Quiz</h5>
                <p className="card-text">Assess your risk tolerance with a quick quiz.</p>
                <Link to="/risk-quiz" className="btn btn-primary">Start Quiz</Link>
              </div>
            </div>
          </div>
          <div className="col">
            <div className="card h-100 text-center">
              {/* Removed image for Rebalance tile */}
              <div className="card-body">
                <h5 className="card-title">Rebalance Portfolio</h5>
                <p className="card-text">Get recommendations to bring your portfolio back to target.</p>
                <Link to="/rebalance" className="btn btn-primary">Rebalance Now</Link>
              </div>
            </div>
          </div>
          <div className="col">
            <div className="card h-100 text-center">
              {/* Removed image for Recommendations tile */}
              <div className="card-body">
                <h5 className="card-title">Get Recommendations</h5>
                <p className="card-text">Receive personalized asset recommendations.</p>
                <Link to="/recommendations" className="btn btn-primary">Get Recommendations</Link>
              </div>
            </div>
          </div>
          <div className="col">
            <div className="card h-100 text-center">
              {/* Removed image for Backtest tile */}
              <div className="card-body">
                <h5 className="card-title">Run Backtest</h5>
                <p className="card-text">Test your strategies against historical data.</p>
                <Link to="/backtest" className="btn btn-primary">Run Backtest</Link>
              </div>
            </div>
          </div>
          <div className="col">
            <div className="card h-100 text-center">
              {/* Removed image for Settings tile */}
              <div className="card-body">
                <h5 className="card-title">Settings</h5>
                <p className="card-text">Adjust application settings and preferences.</p>
                <Link to="/settings" className="btn btn-primary">Go to Settings</Link>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;