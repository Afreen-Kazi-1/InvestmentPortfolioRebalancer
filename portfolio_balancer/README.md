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

## Setup Guide (using Docker Compose)

This project uses Docker Compose to manage its services, including the Flask backend, React frontend, PostgreSQL database, Redis, and Celery for background tasks.

### Prerequisites

*   Docker Desktop (or Docker Engine and Docker Compose) installed on your system.

### Steps to Run

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-username/investment-portfolio-rebalancer.git
    cd investment-portfolio-rebalancer
    ```

2.  **Build and start the services:**
    Navigate to the root directory of the project (where `docker-compose.yml` is located) and run:
    ```bash
    docker-compose up --build -d
    ```
    *   `--build`: This flag forces Docker Compose to rebuild the images. Use this when you make changes to the `Dockerfile` or `requirements.txt`.
    *   `-d`: This flag runs the services in detached mode (in the background).

3.  **Initialize the database (first time setup):**
    After the services are up, you need to initialize the database schema. You can do this by running a one-off command in the backend container:
    ```bash
    docker-compose exec backend flask db upgrade # If using Flask-Migrate
    # OR, if not using Flask-Migrate and relying on db.create_all() in wsgi.py:
    # docker-compose exec backend python -c "from portfolio_balancer.src.api.app import create_app; from portfolio_balancer.src.data.database import db; app = create_app(); with app.app_context(): db.create_all()"
    ```
    *Note: The `wsgi.py` file already calls `db.create_all()` within an app context, so the second command might be sufficient for initial setup. If you plan to use migrations for schema changes, you'll need Flask-Migrate.*

4.  **Access the application:**
    *   **Frontend:** Open your web browser and go to `http://localhost:3000`
    *   **Backend API:** The backend API will be accessible at `http://localhost:5000`

5.  **Stopping the services:**
    To stop all running services, navigate to the project root and run:
    ```bash
    docker-compose down
    ```
    To stop and remove all containers, networks, and volumes (including database data), use:
    ```bash
    docker-compose down -v
    ```

## Development Notes

*   **Backend (Flask):** Code changes in `portfolio_balancer/` will be reflected automatically due to volume mounting. You might need to restart the `backend` service if changes are not picked up.
*   **Frontend (React):** Code changes in `frontend/` will trigger hot reloading in the browser.
*   **Celery:** If you modify Celery tasks or configurations, you might need to restart the `celery_worker` and `celery_beat` services.