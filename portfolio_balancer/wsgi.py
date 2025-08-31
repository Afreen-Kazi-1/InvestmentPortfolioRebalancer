from portfolio_balancer.src.api.app import create_app
from portfolio_balancer.src.data.database import db
from portfolio_balancer.src.tasks.celery_app import make_celery

app = create_app()
celery = make_celery(app)

# This is needed for Flask-Migrate to discover models
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)