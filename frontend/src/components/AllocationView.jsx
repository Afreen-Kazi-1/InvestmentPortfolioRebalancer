import React, { useState, useEffect } from 'react';
import { Pie, Line } from 'react-chartjs-2';
import { Chart as ChartJS, ArcElement, Tooltip, Legend, CategoryScale, LinearScale, PointElement, LineElement } from 'chart.js';

ChartJS.register(ArcElement, Tooltip, Legend, CategoryScale, LinearScale, PointElement, LineElement);

const AllocationView = () => {
  const [currentAllocation, setCurrentAllocation] = useState([]);
  const [targetAllocation, setTargetAllocation] = useState([]);
  const [historicalAllocation, setHistoricalAllocation] = useState([]);

  useEffect(() => {
    // Fetch current allocation data
    const fetchCurrentAllocation = async () => {
      try {
        const response = await fetch('http://127.0.0.1:5000/api/current-allocation');
        const data = await response.json();
        setCurrentAllocation(data);
      } catch (error) {
        console.error('Error fetching current allocation:', error);
      }
    };

    // Fetch target allocation data
    const fetchTargetAllocation = async () => {
      try {
        const response = await fetch('http://127.0.0.1:5000/api/target-allocation');
        const data = await response.json();
        setTargetAllocation(data);
      } catch (error) {
        console.error('Error fetching target allocation:', error);
      }
    };

    fetchCurrentAllocation();
    fetchTargetAllocation();

    const fetchHistoricalAllocation = async () => {
      try {
        const userId = 1; // Hardcoded for now
        const token = localStorage.getItem('token');
        const response = await fetch(`http://127.0.0.1:5000/api/user/${userId}/historical-allocation`, {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });
        const data = await response.json();
        if (response.ok) {
          setHistoricalAllocation(data);
        } else {
          console.error('Error fetching historical allocation:', data.error);
        }
      } catch (error) {
        console.error('Error fetching historical allocation:', error);
      }
    };
    fetchHistoricalAllocation();
  }, []);

  const prepareChartData = (allocationData, title) => {
    const labels = allocationData.map(item => item.assetClass);
    const data = allocationData.map(item => item.percentage);
    const backgroundColors = [
      '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF', '#FF9F40', '#E7E9ED'
    ];

    return {
      labels: labels,
      datasets: [
        {
          label: title,
          data: data,
          backgroundColor: backgroundColors.slice(0, data.length),
          hoverOffset: 4
        }
      ]
    };
  };

  const calculateDrift = (current, target) => {
    const drift = {};
    const targetMap = new Map(target.map(item => [item.assetClass, item.percentage]));

    current.forEach(currentItem => {
      const targetPercentage = targetMap.get(currentItem.assetClass) || 0;
      drift[currentItem.assetClass] = currentItem.percentage - targetPercentage;
    });

    target.forEach(targetItem => {
      if (!drift.hasOwnProperty(targetItem.assetClass)) {
        const currentPercentage = current.find(item => item.assetClass === targetItem.assetClass)?.percentage || 0;
        drift[targetItem.assetClass] = currentPercentage - targetItem.percentage;
      }
    });

    return drift;
  };

  const driftData = calculateDrift(currentAllocation, targetAllocation);

  const prepareHistoricalChartData = (data) => {
    const labels = data.map(item => item.date);
    const assetClasses = Object.keys(data[0] || {}).filter(key => key !== 'date');
    
    const datasets = assetClasses.map((assetClass, index) => {
      const colors = ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF', '#FF9F40', '#E7E9ED'];
      return {
        label: assetClass.charAt(0).toUpperCase() + assetClass.slice(1), // Capitalize first letter
        data: data.map(item => item[assetClass]),
        borderColor: colors[index % colors.length],
        backgroundColor: colors[index % colors.length],
        fill: false,
        tension: 0.1
      };
    });

    return {
      labels: labels,
      datasets: datasets
    };
  };

  return (
    <div className="container mt-5">
      <h2>Allocation View</h2>
      <div className="row">
        <div className="col-md-6">
          <h3>Current Allocation</h3>
          {currentAllocation.length > 0 ? (
            <Pie data={prepareChartData(currentAllocation, 'Current Allocation')} />
          ) : (
            <p>No current allocation data available.</p>
          )}
        </div>
        <div className="col-md-6">
          <h3>Target Allocation</h3>
          {targetAllocation.length > 0 ? (
            <Pie data={prepareChartData(targetAllocation, 'Target Allocation')} />
          ) : (
            <p>No target allocation data available.</p>
          )}
        </div>
      </div>

      <h3 className="mt-5">Historical Allocation Growth</h3>
      <div className="row">
        <div className="col-md-12">
          {historicalAllocation.length > 0 ? (
            <Line data={prepareHistoricalChartData(historicalAllocation)} />
          ) : (
            <p>No historical allocation data available.</p>
          )}
        </div>
      </div>

      <h3 className="mt-5">Drift from Target</h3>
      <div className="list-group">
        {Object.entries(driftData).map(([assetClass, driftValue]) => (
          <div key={assetClass} className="list-group-item">
            {assetClass}: {driftValue.toFixed(2)}%
            <div className="progress mt-2">
              <div
                className={`progress-bar ${driftValue >= 0 ? 'bg-success' : 'bg-danger'}`}
                role="progressbar"
                style={{ width: `${Math.abs(driftValue)}%` }}
                aria-valuenow={Math.abs(driftValue)}
                aria-valuemin="0"
                aria-valuemax="100"
              >
                {driftValue.toFixed(2)}%
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default AllocationView;