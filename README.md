# Cashuu
## Lending Money Web Application

![N|Solid](https://cashuu.com/static/frontend/assets/images/logo.png)

[![Build Status](https://travis-ci.org/joemccann/dillinger.svg?branch=master)](https://travis-ci.org/joemccann/dillinger)

The purpose of this document is to present a detailed description of the “MICRO LENDING” Application Only Front-End (Borrowers and Lenders), and Admin (Web panel)” features. It shall explain the purpose and features of the platform, the interfaces of the system, what the system shall do and the constraints under which it must operate.  This document is intended for the stakeholders, designers and the developers of the system. This document shall be the base for confirmation of the delivery of the product as per the original requirements discussed and agreed by both the parties.
This project uses Django as a web framework, Postgres as a database, pgAdmin as a database management tool, Nginx as a reverse proxy, and certbot for SSL certificates, all running inside Docker containers managed by Docker Compose.


## Normal Installation

1. Clone the repository
    git clone git@git.reponame/micro-lending-application.git

2. Create a virtual environment and activate it
    python -m venv env
    source env/bin/activate

3. Install the dependencies
    pip install -r requirements.txt

4. Create a new file .env in the root directory, and set the environment variables
    • SECRET_KEY=key
    • DEBUG=set_value
    • ALLOWED_HOSTS=localhost,127.0.0.1
    • EMAIL_HOST_USER=example@domain.com
    • EMAIL_HOST_PASSWORD=password
    • DEVELOPMENT_URL='http://localhost:8000/'
    • PRODUCTION_URL='https://domain.com/
    • STRIPE_PUBLIC_KEY=key
    • STRIPE_SECRET_KEY=key
    • SUCCESS_URL='http://localhost:8000/payment-success'
    • CANCEL_URL='http://localhost:8000/payment-failed'
    • WEBSITE_URL='http://localhost:8000/'
    • GOOGLE_CLIENT_ID=key
    • GOOGLE_SECRET_KEY=key
    • JWT_SECRET_KEY=key

5. Apply the migrations
    • python manage.py makemigrations
    • python manage.py migrate    

6. Run the development server
    • python manage.py runserver

## Docker Installation
#### Prerequisites
    • Docker
    • Docker Compose

1. Clone the repository
    • git clone git@git.devtechnosys.tech:shamsher_singh/micro-lending-application.git

2. Create a new file .env in the root directory, and set the environment variables
    • SECRET_KEY=key
    • DEBUG=set_value
    • ALLOWED_HOSTS=localhost,127.0.0.1
    • EMAIL_HOST_USER=example@domain.com
    • EMAIL_HOST_PASSWORD=password
    • DEVELOPMENT_URL='http://localhost:8000/'
    • PRODUCTION_URL='https://domain.com/
    • STRIPE_PUBLIC_KEY=key
    • STRIPE_SECRET_KEY=key
    • SUCCESS_URL='http://localhost:8000/payment-success'
    • CANCEL_URL='http://localhost:8000/payment-failed'
    • WEBSITE_URL='http://localhost:8000/'
    • GOOGLE_CLIENT_ID=key
    • GOOGLE_SECRET_KEY=key
    • JWT_SECRET_KEY=key

3. Run the following command to build the containers and start the services
    • docker-compose up --build

4. Create a new superuser for your Django app
    • Create a new superuser for your Django app

5. Obtain SSL certificates for your domain, replace example.com with your domain name
    • docker-compose run --rm certbot certonly --webroot -w /var/www/certbot -d example.com -m admin@example.com --agree-tos --no-eff-email

6. For the database backup
    • docker exec <container_name> pg_dump -Ft -U django -d django_db > backup.tar


Usage
    - Access the Django app at http://localhost or https://localhost
    - Access pgAdmin at http://localhost:5050
    - Access the Postgres database using the credentials set in the .env file

Deployment

    • To deploy the project to a live server, you'll need to build the images and push them to a container registry, then use the images to start the services on the server.

    • You can also use GitLab CI/CD to build the images, push them to a container registry, and deploy them to your server.

    • Please make sure to update the environment variables, domain name and the path to the SSL certificates to match your setup.

Maintenance

    • You can use the following command to renew the SSL certificates
    • docker-compose run --rm certbot renew

You can also schedule renewals using a cron job, as previously mentioned.

### Additional Configuration

    • You may need to configure your DNS settings to point your domain to the server's IP address and configure a reverse proxy on the server to forward requests to the appropriate service.

    • You can also scale the number of web service instances by modifying the docker-compose.yml file, and adding a load balancer for example.

    • Please make sure to read the official documentation of the different services used in this project to get familiar with their configuration options and best practices.



User Types
- Borrower
- Lender
- Lender Store
- ✨Platform Owner as Admin ✨

## Features Borrower
In the front end there shall be the user as borrower who shall be having the following modules:
    • Splash Screen
    • App Guide
    • Sign up
    • Registration
    • Log In
    • Home Screen
    • Bid System
    • History
    • My Account

## Features Lender
In the front end there shall be the user as lender who shall be having the following modules:
    • Splash Screen
    • App Guide
    • Sign up
    • Registration
    • Log In
    • Home Screen
    • Bid System
    • History
    • My Account
    • Wallet

## Features Admin
In the back end there shall be a single user who shall be having the following modules:
    • Log In
    • Users Account Management (Borrower and Lender Management)
    • Earning Management
    • Manage Contents
    • Reports & Statistics
    • Template Management
    • Notifications Management

## Tech
Technologies and database that we used:
    • Backend : Python
    • Framework: Django
    • Frontend: HTML, CSS, JavaScript
    • Database: PostgreSQL
    • Deployment: Docker
    • Server: Gunicorn
    • Proxy-Server: Nginx
    • Code Repo: GitLab
    • Hosted: AWS
