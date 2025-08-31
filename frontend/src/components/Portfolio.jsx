import React, { useState, useEffect } from 'react';

const Portfolio = ({ userId = 1 }) => { // Default userId to 1 for now
  const [snapshot, setSnapshot] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchPortfolioSnapshot = async () => {
      try {
        const response = await fetch(`http://localhost:5000/api/portfolio/snapshot/${userId}`);
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        setSnapshot(data);
      } catch (e) {
        setError(e);
      } finally {
        setLoading(false);
      }
    };

    fetchPortfolioSnapshot();
  }, [userId]);

  if (loading) {
    return <div className="container mt-5">Loading portfolio...</div>;
  }

  if (error) {
    return <div className="container mt-5">Error: {error.message}</div>;
  }

  if (!snapshot || !snapshot.breakdown || snapshot.breakdown.length === 0) {
    return <div className="container mt-5">No portfolio data available.</div>;
  }

  return (
    <div className="container mt-5">
      <h2>Current Portfolio Snapshot</h2>
      <p><strong>Total Value:</strong> ${snapshot.total_value.toFixed(2)}</p>
      <table className="table table-striped">
        <thead>
          <tr>
            <th scope="col">Ticker</th>
            <th scope="col">Value</th>
            <th scope="col">Weight</th>
            <th scope="col">Target</th>
            <th scope="col">Drift</th>
          </tr>
        </thead>
        <tbody>
          {snapshot.breakdown.map((item, index) => (
            <tr key={index}>
              <td>{item.ticker}</td>
              <td>${item.value.toFixed(2)}</td>
              <td>{(item.weight * 100).toFixed(2)}%</td>
              <td>{(item.target * 100).toFixed(2)}%</td>
              <td>{(item.drift * 100).toFixed(2)}%</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default Portfolio;