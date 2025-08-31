import React, { useState, useEffect } from 'react';

const RecommendationsTab = () => {
  const [recommendations, setRecommendations] = useState([]);

  useEffect(() => {
    // Fetch recommendations from the backend
    const fetchRecommendations = async () => {
      try {
        const response = await fetch('http://127.0.0.1:5000/api/recommendations');
        const data = await response.json();
        setRecommendations(data);
      } catch (error) {
        console.error('Error fetching recommendations:', error);
      }
    };

    fetchRecommendations();
  }, []);

  const handleApplyToTarget = async (recommendationId) => {
    try {
      const response = await fetch('http://127.0.0.1:5000/api/apply-recommendation', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ recommendationId }),
      });
      const result = await response.json();
      alert(result.message);
      // Optionally, refresh recommendations or navigate to allocation view
    } catch (error) {
      console.error('Error applying recommendation:', error);
      alert('Failed to apply recommendation.');
    }
  };

  return (
    <div className="container mt-5">
      <h2>Recommendations</h2>
      {recommendations.length > 0 ? (
        <div className="row">
          {recommendations.map(rec => (
            <div className="col-md-4 mb-4" key={rec.id}>
              <div className="card">
                <div className="card-body">
                  <h5 className="card-title">{rec.title}</h5>
                  <p className="card-text">{rec.reason}</p>
                  <button
                    className="btn btn-primary"
                    onClick={() => handleApplyToTarget(rec.id)}
                  >
                    Apply to Target
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <p>No recommendations available at this time.</p>
      )}
    </div>
  );
};

export default RecommendationsTab;