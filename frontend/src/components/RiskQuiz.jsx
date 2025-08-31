import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';

const RiskQuiz = () => {
  const [answers, setAnswers] = useState({
    age: '',
    horizon: '',
    drawdown: '',
    goal: '',
  });
  const navigate = useNavigate();

  const handleChange = (e) => {
    setAnswers({
      ...answers,
      [e.target.name]: e.target.value,
    });
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    // Here you would typically send the answers to the backend
    // For now, we'll just navigate to the next step
    console.log(answers);
    navigate('/target-allocation');
  };

  return (
    <div className="container mt-5">
      <h2>Risk Profile Quiz</h2>
      <form onSubmit={handleSubmit}>
        <div className="mb-3">
          <label htmlFor="age" className="form-label">What is your age?</label>
          <input type="number" className="form-control" id="age" name="age" value={answers.age} onChange={handleChange} required />
        </div>
        <div className="mb-3">
          <label htmlFor="horizon" className="form-label">What is your investment horizon?</label>
          <select className="form-select" id="horizon" name="horizon" value={answers.horizon} onChange={handleChange} required>
            <option value="">Select...</option>
            <option value="short">Short-term (1-3 years)</option>
            <option value="medium">Medium-term (3-7 years)</option>
            <option value="long">Long-term (7+ years)</option>
          </select>
        </div>
        <div className="mb-3">
          <label htmlFor="drawdown" className="form-label">How much of a portfolio drawdown would you be comfortable with?</label>
          <select className="form-select" id="drawdown" name="drawdown" value={answers.drawdown} onChange={handleChange} required>
            <option value="">Select...</option>
            <option value="low">Low (less than 10%)</option>
            <option value="medium">Medium (10-25%)</option>
            <option value="high">High (more than 25%)</option>
          </select>
        </div>
        <div className="mb-3">
          <label htmlFor="goal" className="form-label">What is your primary investment goal?</label>
          <select className="form-select" id="goal" name="goal" value={answers.goal} onChange={handleChange} required>
            <option value="">Select...</option>
            <option value="capital_preservation">Capital Preservation</option>
            <option value="income">Income Generation</option>
            <option value="growth">Growth</option>
            <option value="speculation">Speculation</option>
          </select>
        </div>
        <button type="submit" className="btn btn-primary">Submit</button>
      </form>
    </div>
  );
};

export default RiskQuiz;