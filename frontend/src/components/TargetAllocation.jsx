import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';

const TargetAllocation = () => {
  const [allocation, setAllocation] = useState({
    equities: '',
    bonds: '',
    cash: '',
  });
  const navigate = useNavigate();

  const handleModelPortfolio = (equities, bonds, cash) => {
    setAllocation({ equities, bonds, cash });
  };

  const handleChange = (e) => {
    setAllocation({
      ...allocation,
      [e.target.name]: e.target.value,
    });
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    // Here you would typically send the allocation to the backend
    console.log(allocation);
    navigate('/portfolio');
  };

  return (
    <div className="container mt-5">
      <h2>Target Allocation</h2>
      <p>Choose a model portfolio or enter your custom target allocation.</p>

      <div className="btn-group mb-4" role="group">
        <button type="button" className="btn btn-outline-primary" onClick={() => handleModelPortfolio(30, 60, 10)}>Conservative</button>
        <button type="button" className="btn btn-outline-primary" onClick={() => handleModelPortfolio(60, 30, 10)}>Balanced</button>
        <button type="button" className="btn btn-outline-primary" onClick={() => handleModelPortfolio(80, 10, 10)}>Aggressive</button>
      </div>

      <form onSubmit={handleSubmit}>
        <div className="row">
          <div className="col-md-4 mb-3">
            <label htmlFor="equities" className="form-label">Equities (%)</label>
            <input type="number" className="form-control" id="equities" name="equities" value={allocation.equities} onChange={handleChange} required />
          </div>
          <div className="col-md-4 mb-3">
            <label htmlFor="bonds" className="form-label">Bonds (%)</label>
            <input type="number" className="form-control" id="bonds" name="bonds" value={allocation.bonds} onChange={handleChange} required />
          </div>
          <div className="col-md-4 mb-3">
            <label htmlFor="cash" className="form-label">Cash (%)</label>
            <input type="number" className="form-control" id="cash" name="cash" value={allocation.cash} onChange={handleChange} required />
          </div>
        </div>
        <button type="submit" className="btn btn-primary">Submit</button>
      </form>
    </div>
  );
};

export default TargetAllocation;