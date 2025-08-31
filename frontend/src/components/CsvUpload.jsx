import React, { useState } from 'react';

const CsvUpload = () => {
  const [file, setFile] = useState(null);

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!file) {
      alert('Please select a file');
      return;
    }
    // Here you would typically send the file to the backend for processing
    console.log(file);
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