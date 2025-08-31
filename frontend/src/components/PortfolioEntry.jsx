import React, { useState } from 'react';

const PortfolioEntry = () => {
  const [holdings, setHoldings] = useState([{ ticker: '', quantity: '', avg_cost: '' }]);

  const handleChange = (index, e) => {
    const newHoldings = [...holdings];
    newHoldings[index][e.target.name] = e.target.value;
    setHoldings(newHoldings);
  };

  const handleAddRow = () => {
    setHoldings([...holdings, { ticker: '', quantity: '', avg_cost: '' }]);
  };

  const handleRemoveRow = (index) => {
    const newHoldings = [...holdings];
    newHoldings.splice(index, 1);
    setHoldings(newHoldings);
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    // Here you would typically send the holdings to the backend
    console.log(holdings);
  };

  return (
    <div className="container mt-5">
      <h2>Portfolio Entry</h2>
      <form onSubmit={handleSubmit}>
        {holdings.map((holding, index) => (
          <div className="row mb-3" key={index}>
            <div className="col-md-3">
              <input type="text" className="form-control" name="ticker" placeholder="Ticker" value={holding.ticker} onChange={(e) => handleChange(index, e)} required />
            </div>
            <div className="col-md-3">
              <input type="number" className="form-control" name="quantity" placeholder="Quantity" value={holding.quantity} onChange={(e) => handleChange(index, e)} required />
            </div>
            <div className="col-md-3">
              <input type="number" className="form-control" name="avg_cost" placeholder="Average Cost" value={holding.avg_cost} onChange={(e) => handleChange(index, e)} required />
            </div>
            <div className="col-md-3">
              <button type="button" className="btn btn-danger" onClick={() => handleRemoveRow(index)}>Remove</button>
            </div>
          </div>
        ))}
        <button type="button" className="btn btn-secondary me-2" onClick={handleAddRow}>Add Row</button>
        <button type="submit" className="btn btn-primary">Submit</button>
      </form>
    </div>
  );
};

export default PortfolioEntry;