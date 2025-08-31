import React, { useState, useEffect } from 'react';

const Portfolio = () => {
  const [holdings, setHoldings] = useState([]);

  useEffect(() => {
    fetch('http://127.0.0.1:5000/api/portfolio')
      .then(response => response.json())
      .then(data => setHoldings(data))
      .catch(error => console.error('Error fetching portfolio:', error));
  }, []);

  return (
    <div className="container mt-5">
      <h2>Portfolio</h2>
      <table className="table">
        <thead>
          <tr>
            <th scope="col">Ticker</th>
            <th scope="col">Quantity</th>
            <th scope="col">Average Cost</th>
          </tr>
        </thead>
        <tbody>
          {holdings.map(holding => (
            <tr key={holding.id}>
              <td>{holding.ticker}</td>
              <td>{holding.quantity}</td>
              <td>{holding.avg_cost}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default Portfolio;