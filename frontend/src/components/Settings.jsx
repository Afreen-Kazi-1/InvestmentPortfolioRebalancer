import React, { useState, useEffect } from 'react';

const Settings = () => {
  const [settings, setSettings] = useState({
    equities: 0,
    bonds: 0,
    cash: 0,
    rebalanceThreshold: 5,
    minCash: 0,
  });

  useEffect(() => {
    // Fetch current settings from the backend
    const fetchSettings = async () => {
      try {
        const response = await fetch('http://127.0.0.1:5000/api/settings');
        const data = await response.json();
        setSettings(data);
      } catch (error) {
        console.error('Error fetching settings:', error);
      }
    };

    fetchSettings();
  }, []);

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setSettings(prevSettings => ({
      ...prevSettings,
      [name]: type === 'checkbox' ? checked : parseFloat(value),
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const response = await fetch('http://127.0.0.1:5000/api/settings', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(settings),
      });
      const result = await response.json();
      alert(result.message);
    } catch (error) {
      console.error('Error saving settings:', error);
      alert('Failed to save settings.');
    }
  };

  return (
    <div className="container mt-5">
      <h2>Settings</h2>
      <form onSubmit={handleSubmit}>
        <div className="mb-3">
          <label htmlFor="equities" className="form-label">Target Equities (%)</label>
          <input
            type="range"
            className="form-range"
            id="equities"
            name="equities"
            min="0"
            max="100"
            value={settings.equities}
            onChange={handleChange}
          />
          <p className="text-muted">{settings.equities}%</p>
        </div>

        <div className="mb-3">
          <label htmlFor="bonds" className="form-label">Target Bonds (%)</label>
          <input
            type="range"
            className="form-range"
            id="bonds"
            name="bonds"
            min="0"
            max="100"
            value={settings.bonds}
            onChange={handleChange}
          />
          <p className="text-muted">{settings.bonds}%</p>
        </div>

        <div className="mb-3">
          <label htmlFor="cash" className="form-label">Target Cash (%)</label>
          <input
            type="range"
            className="form-range"
            id="cash"
            name="cash"
            min="0"
            max="100"
            value={settings.cash}
            onChange={handleChange}
          />
          <p className="text-muted">{settings.cash}%</p>
        </div>

        <div className="mb-3">
          <label htmlFor="rebalanceThreshold" className="form-label">Rebalance Threshold (%)</label>
          <input
            type="number"
            className="form-control"
            id="rebalanceThreshold"
            name="rebalanceThreshold"
            value={settings.rebalanceThreshold}
            onChange={handleChange}
            min="0"
            max="100"
          />
        </div>

        <div className="mb-3">
          <label htmlFor="minCash" className="form-label">Minimum Cash ($)</label>
          <input
            type="number"
            className="form-control"
            id="minCash"
            name="minCash"
            value={settings.minCash}
            onChange={handleChange}
            min="0"
          />
        </div>

        <button type="submit" className="btn btn-primary">Save Settings</button>
      </form>
    </div>
  );
};

export default Settings;