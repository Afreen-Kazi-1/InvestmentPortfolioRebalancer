import React, { useState, useEffect } from 'react';

const RebalanceTab = () => {
  const [trades, setTrades] = useState([]);
  const [skipTinyTrades, setSkipTinyTrades] = useState(true);

  useEffect(() => {
    // Fetch trade list from the backend
    const fetchTrades = async () => {
      try {
        const response = await fetch('http://127.0.0.1:5000/api/rebalance-trades');
        const data = await response.json();
        setTrades(data);
      } catch (error) {
        console.error('Error fetching trades:', error);
      }
    };

    fetchTrades();
  }, []);

  const handleToggleSkipTinyTrades = () => {
    setSkipTinyTrades(!skipTinyTrades);
    // Optionally, re-fetch trades or filter them based on the new setting
  };

  const handleToggleTrade = (tradeId) => {
    setTrades(prevTrades =>
      prevTrades.map(trade =>
        trade.id === tradeId ? { ...trade, skipped: !trade.skipped } : trade
      )
    );
  };

  const filteredTrades = trades.filter(trade =>
    !(skipTinyTrades && trade.isTiny && !trade.skipped)
  );

  const handleExecuteRebalance = async () => {
    try {
      const tradesToExecute = filteredTrades.filter(trade => !trade.skipped);
      const response = await fetch('http://127.0.0.1:5000/api/execute-rebalance', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ trades: tradesToExecute }),
      });
      const result = await response.json();
      alert(result.message);
      // Optionally, refresh trade list or navigate to dashboard
    } catch (error) {
      console.error('Error executing rebalance:', error);
      alert('Failed to execute rebalance.');
    }
  };

  return (
    <div className="container mt-5">
      <h2>Rebalance Portfolio</h2>

      <div className="form-check mb-3">
        <input
          className="form-check-input"
          type="checkbox"
          id="skipTinyTrades"
          checked={skipTinyTrades}
          onChange={handleToggleSkipTinyTrades}
        />
        <label className="form-check-label" htmlFor="skipTinyTrades">
          Skip tiny trades
        </label>
      </div>

      {filteredTrades.length > 0 ? (
        <table className="table">
          <thead>
            <tr>
              <th scope="col">Action</th>
              <th scope="col">Ticker</th>
              <th scope="col">Quantity</th>
              <th scope="col">Value</th>
              <th scope="col">Skip</th>
            </tr>
          </thead>
          <tbody>
            {filteredTrades.map(trade => (
              <tr key={trade.id} className={trade.skipped ? 'table-secondary' : ''}>
                <td>{trade.action}</td>
                <td>{trade.ticker}</td>
                <td>{trade.quantity}</td>
                <td>${trade.value.toFixed(2)}</td>
                <td>
                  <input
                    type="checkbox"
                    checked={trade.skipped}
                    onChange={() => handleToggleTrade(trade.id)}
                  />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : (
        <p>No rebalance trades recommended at this time.</p>
      )}

      <button className="btn btn-primary mt-3" onClick={handleExecuteRebalance}>
        Execute Rebalance
      </button>
    </div>
  );
};

export default RebalanceTab;