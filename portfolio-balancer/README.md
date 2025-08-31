# Investment Portfolio Rebalancer

This project is a portfolio rebalancing tool that uses machine learning to optimize asset allocation.

## Features

- Fetch historical market data from various sources.
- Preprocess data for feature engineering.
- Train machine learning models for risk and return prediction.
- Optimize portfolio allocation based on various strategies.
- Backtest and evaluate portfolio performance.
- Visualize results through interactive dashboards.
- Deploy the application as a containerized service.

## Setup Guide

1. **Clone the repository:**
   ```bash
   git clone https://github.com/your-username/investment-portfolio-rebalancer.git
   cd investment-portfolio-rebalancer
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application:**
   ```bash
   python src/api/app.py