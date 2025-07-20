# Salon Manager

**Salon Manager**
A comprehensive web application for beauty salon management, built with Django. This system provides a complete solution for salon owners to manage their business operations and allows clients to book appointments online.

## ✨ Features

- Public website with salon description, services, staff list, and contact form
- Registration and login system
- Book appointments online
- Logged-in users can:
  - View and manage their reservations
- Salon owners can:
  - Manage employees and their working days
  - Add, edit, and remove services and service categories
  - View all reservations
- Asynchronous email notifications using Celery and Redis
- Dockerized deployment with Docker Compose
- PostgreSQL as the database engine

## 🛠️ Technologies Used

Backend
- Python
- Django
- Celery + Celery Beat, Celery Flower
- Redis
- PostgreSQL
- Docker + Docker Compose

Frontend
- HTML5
- CSS3
- JavaScript
- AJAX
- Bootstrap

DevOps
- Docker - Containerization
- Docker Compose - Multi-container application management
- GitHub Actions - Continuous Integration/Continuous Deployment

## 📋 Prerequisites

- Docker and Docker Compose installed on your system
- Git for version control

## 🚀 Getting Started

To run the project locally using Docker:

1.  Clone the repository:
   ```bash
   git clone https://github.com/your-username/salon-manager.git
   cd salon_manager
   ```
2.	Environment Setup
```bash cp.env.example .env```
Edit .env file with your configuration

3.  Build and start the containers:
  ```bash
docker-compose up --build
```

4.  Apply migrations and create a superuser:
  ```bash
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py createsuperuser
  ```
5.	Access the app at: http://localhost:8010

## 🌐 Docker Services

- web: Django application server
- db: PostgreSQL database
- redis: Redis cache and message broker
- celery-worker: Celery worker for background tasks
- celery-beat: Celery beat scheduler for periodic tasks
- flower: Celery monitoring dashboard

## 🧪 Running Tests

To run available tests:
```bash
docker-compose exec web python manage.py test
```

## 🔄 Development Status

This project is currently in active development. Upcoming features and improvements include:

- Complete test coverage
- Full internationalization (Polish and English)
- Enhanced UI/UX improvements
- Additional salon management features
- REST API implementation

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (git checkout -b feature/amazing-feature)
3. Commit your changes (git commit -m 'Add some amazing feature')
4. Push to the branch (git push origin feature/amazing-feature)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 👨‍💻 Author

Paweł Truszkowski
- GitHub: @Pawel-Truszkowski
- Email: pawel.truszkowski14@gmail.com

## 📬 Contact

If you’d like to get in touch, feel free to open an issue or message me via GitHub.
