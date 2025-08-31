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

  const handleSubmit = async (e) => {
    e.preventDefault();
    // For demonstration, using a hardcoded user_id. In a real app, this would come from auth context.
    const userId = 1;
    const token = localStorage.getItem('token'); // Retrieve token from local storage

    if (!token) {
      alert('Authentication token not found. Please log in.');
      return;
    }

    try {
      const response = await fetch(`http://127.0.0.1:5000/holdings?user_id=${userId}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}` // Include the token in the Authorization header
        },
        body: JSON.stringify(holdings),
      });

      if (response.ok) {
        alert('Holdings submitted successfully!');
        setHoldings([{ ticker: '', quantity: '', avg_cost: '' }]); // Clear form
      } else {
        const errorData = await response.json();
        alert(`Failed to submit holdings: ${errorData.error || response.statusText}`);
      }
    } catch (error) {
      console.error('Error submitting holdings:', error);
      alert('Network error or server is unreachable.');
    }
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