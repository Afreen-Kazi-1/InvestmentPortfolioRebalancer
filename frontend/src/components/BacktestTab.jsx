import React, { useState, useEffect } from 'react';
import { Line, Bar, Scatter } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Tooltip,
  Legend,
} from 'chart.js';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Tooltip,
  Legend
);

const BacktestTab = () => {
  const [equityCurveData, setEquityCurveData] = useState({});
  const [drawdownData, setDrawdownData] = useState({});
  const [efficientFrontierData, setEfficientFrontierData] = useState({});

  useEffect(() => {
    // Fetch backtest data from the backend
    const fetchBacktestData = async () => {
      try {
        const response = await fetch('http://127.0.0.1:5000/api/backtest-results');
        const data = await response.json();

        // Equity Curve
        setEquityCurveData({
          labels: data.equityCurve.dates,
          datasets: [
            {
              label: 'Equity Curve',
              data: data.equityCurve.values,
              borderColor: 'rgb(75, 192, 192)',
              tension: 0.1,
            },
          ],
        });

        // Drawdowns
        setDrawdownData({
          labels: data.drawdowns.dates,
          datasets: [
            {
              label: 'Drawdown',
              data: data.drawdowns.values,
              backgroundColor: 'rgba(255, 99, 132, 0.5)',
            },
          ],
        });

        // Efficient Frontier (if MVO)
        setEfficientFrontierData({
          datasets: [
            {
              label: 'Efficient Frontier',
              data: data.efficientFrontier.points.map(p => ({ x: p.risk, y: p.return })),
              backgroundColor: 'rgba(53, 162, 235, 0.5)',
            },
            {
              label: 'Your Portfolio',
              data: [{ x: data.efficientFrontier.yourPortfolio.risk, y: data.efficientFrontier.yourPortfolio.return }],
              backgroundColor: 'red',
              pointRadius: 8,
              pointHoverRadius: 10,
            }
          ],
        });

      } catch (error) {
        console.error('Error fetching backtest data:', error);
      }
    };

    fetchBacktestData();
  }, []);

  const chartOptions = {
    responsive: true,
    plugins: {
      legend: {
        position: 'top',
      },
      title: {
        display: true,
        text: 'Chart Title', // This will be overridden by individual chart titles
      },
    },
  };

  return (
    <div className="container mt-5">
      <h2>Backtest Results</h2>

      <div className="row mb-4">
        <div className="col-md-12">
          <h3>Equity Curve</h3>
          {equityCurveData.labels ? (
            <Line data={equityCurveData} options={{ ...chartOptions, plugins: { ...chartOptions.plugins, title: { display: true, text: 'Equity Curve' } } }} />
          ) : (
            <p>No equity curve data available.</p>
          )}
        </div>
      </div>

      <div className="row mb-4">
        <div className="col-md-12">
          <h3>Drawdowns</h3>
          {drawdownData.labels ? (
            <Bar data={drawdownData} options={{ ...chartOptions, plugins: { ...chartOptions.plugins, title: { display: true, text: 'Drawdowns' } } }} />
          ) : (
            <p>No drawdown data available.</p>
          )}
        </div>
      </div>

      <div className="row mb-4">
        <div className="col-md-12">
          <h3>Efficient Frontier</h3>
          {efficientFrontierData.datasets ? (
            <Scatter data={efficientFrontierData} options={{ ...chartOptions, plugins: { ...chartOptions.plugins, title: { display: true, text: 'Efficient Frontier' } }, scales: { x: { type: 'linear', position: 'bottom', title: { display: true, text: 'Risk (Standard Deviation)' } }, y: { type: 'linear', position: 'left', title: { display: true, text: 'Return' } } } }} />
          ) : (
            <p>No efficient frontier data available.</p>
          )}
        </div>
      </div>
    </div>
  );
};

export default BacktestTab;