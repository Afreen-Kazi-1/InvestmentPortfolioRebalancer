import React, { useState, useEffect } from 'react';

const RebalanceSuggestions = ({ userId = 1 }) => { // Default userId to 1 for now
  const [suggestions, setSuggestions] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchRebalanceSuggestions = async () => {
      try {
        const response = await fetch(`http://localhost:5000/api/rebalance/suggest/${userId}`);
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        setSuggestions(data);
      } catch (e) {
        setError(e);
      } finally {
        setLoading(false);
      }
    };

    fetchRebalanceSuggestions();
  }, [userId]);

  if (loading) {
    return <div className="container mt-5">Loading rebalance suggestions...</div>;
  }

  if (error) {
    return <div className="container mt-5">Error: {error.message}</div>;
  }

  if (!suggestions || !suggestions.trades || suggestions.trades.length === 0) {
    return <div className="container mt-5">No rebalance suggestions available.</div>;
  }

  return (
    <div className="container mt-5">
      <h2>Rebalance Suggestions</h2>
      <h3>Trades:</h3>
      <table className="table table-striped">
        <thead>
          <tr>
            <th scope="col">Action</th>
            <th scope="col">Ticker</th>
            <th scope="col">Amount ($)</th>
          </tr>
        </thead>
        <tbody>
          {suggestions.trades.map((trade, index) => (
            <tr key={index}>
              <td>{trade.action}</td>
              <td>{trade.ticker}</td>
              <td>${trade.amount.toFixed(2)}</td>
            </tr>
          ))}
        </tbody>
      </table>

      <h3>Estimated Post-Trade Weights:</h3>
      <ul className="list-group">
        {Object.entries(suggestions.post_trade_weights_est).map(([asset, weight]) => (
          <li key={asset} className="list-group-item">
            {asset.charAt(0).toUpperCase() + asset.slice(1)}: {(weight * 100).toFixed(2)}%
          </li>
        ))}
      </ul>
    </div>
  );
};

export default RebalanceSuggestions;