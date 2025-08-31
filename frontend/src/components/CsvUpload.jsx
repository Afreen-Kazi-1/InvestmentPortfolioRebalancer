import React, { useState } from 'react';

const CsvUpload = () => {
  const [file, setFile] = useState(null);

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!file) {
      alert('Please select a file');
      return;
    }

    const userId = 1; // Hardcoded for demonstration
    const token = localStorage.getItem('token');

    if (!token) {
      alert('Authentication token not found. Please log in.');
      return;
    }

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch(`http://127.0.0.1:5000/portfolio/import?user_id=${userId}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}` // Include the token
        },
        body: formData,
      });

      if (response.ok) {
        alert('CSV uploaded successfully!');
        setFile(null); // Clear the selected file
      } else {
        const errorData = await response.json();
        alert(`Failed to upload CSV: ${errorData.error || response.statusText}`);
      }
    } catch (error) {
      console.error('Error uploading CSV:', error);
      alert('Network error or server is unreachable.');
    }
  };

  return (
    <div className="container mt-5">
      <h2>CSV Upload</h2>
      <p>Upload a CSV file with the following columns: ticker, quantity, avg_cost</p>
      <form onSubmit={handleSubmit}>
        <div className="mb-3">
          <input className="form-control" type="file" id="formFile" onChange={handleFileChange} accept=".csv" />
        </div>
        <button type="submit" className="btn btn-primary">Upload</button>
      </form>
    </div>
  );
};

export default CsvUpload;