# Salon Manager

**Salon Manager** is a full-featured web application for beauty salons. It provides both customers and salon owners with essential tools to manage appointments, services, and staff in an intuitive and efficient way.

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

- Python
- Django
- Celery + Celery Beat
- Redis
- PostgreSQL
- Docker + Docker Compose

## 🚀 Getting Started

To run the project locally using Docker:

1.  Clone the repository:
   ```bash
   git clone https://github.com/your-username/salon-manager.git
   cd salon-manager
   ```
2.	Create an .env file based on .env.example and configure environment variables.
3.  Build and start the containers:
  ```docker-compose up --build```
4.  Apply migrations and create a superuser:
  ``` docker-compose exec web python manage.py migrate
      docker-compose exec web python manage.py createsuperuser
  ```
5.	Access the app at: http://localhost:8010


## 🧪 Running Tests

To run available tests:
```docker-compose exec web pytest```

## 📌 Roadmap / TODO
