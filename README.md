# Emmi

An app designed for women who are training for marathons or looking to get exercise and stay fit, with a focus on injury prevention.

## About the Code

There are three main components in this project:

- **Backend API server**: Django REST framework. Running in port 8001.
- **Frontend**: Next.js. Running in port 3001.
- **Database**: PostgreSQL

## Environment Variables

To run the application, you need to configure both backend and frontend environment variables. These variables are essential for defining the behavior and connectivity of the application in different environments (development and production).

### Backend Environment Variables

The backend environment variables are organized under the `.envs` folder. Inside this folder, you will find a `.local` directory, which contains the following two files:

1. **django**: This file contains environment variables specific to the Django application.
2. **postgres**: This file contains environment variables required for configuring the PostgreSQL database.

Each file includes variables for development purposes and should be updated as needed for your environment. As you prepare for production, you will also have to add certain variables to the `django` environment file.

### Frontend Environment Variables

The frontend environment variables are stored in a file named `env.local` located in the root of the project directory. This file defines variables necessary for the Next.js frontend application.

### Notes on Security

- **Do not push production environment files containing sensitive information (e.g., `env.production`) to Git.**
- Always ensure these files are included in `.gitignore` to prevent accidental exposure of credentials.
- Use secure methods to share environment variables, such as encrypted channels or secret management tools.

## How to Run Development Mode

### Setup the necessary environment variables

To run the application in development mode, you need to set up the environment variables for both the backend and frontend applications.

On `backend/.envs/.local/.django`, set the following variables:

```env
# General
# ------------------------------------------------------------------------------
USE_DOCKER=yes
IPYTHONDIR=/app/.ipython


# Frontend
# ------------------------------------------------------------------------------
FRONTEND_BASE_URL=http://localhost:3001

# Twilio
# ------------------------------------------------------------------------------
TWILIO_ACCOUNT_SID=<your twilio account sid>
TWILIO_AUTH_TOKEN=<your twilio auth token>
TWILIO_PHONE_NUMBER=<your twilio phone number>
TWILIO_VERIFY_SERVICE_SID=<your twilio verify service sid>
ENABLE_TWILIO_VERIFY=true

# Anthropic
# ------------------------------------------------------------------------------
ANTHROPIC_API_KEY=<your anthropic api key>

# Langfuse
# ------------------------------------------------------------------------------
LANGFUSE_SECRET_KEY=<your langfuse secret key>
LANGFUSE_PUBLIC_KEY=<your langfuse public key>
LANGFUSE_HOST=https://us.cloud.langfuse.com

# Mixpanel
MIXPANEL_PROJECT_TOKEN=<your mixpanel project token>
MIXPANEL_ENABLED=true
```

On `frontend/.env.local`, set the following variables:

```env
# Api base url
# ------------------------------------------------------------------------------
NEXT_PUBLIC_API_BASE_URL=http://localhost:8001

# Mixpanel
# ------------------------------------------------------------------------------
NEXT_PUBLIC_MIXPANEL_PROJECT_TOKEN=<your-mixpanel-project-token>
NEXT_PUBLIC_MIXPANEL_ENABLED=true
```

### Build and Run

```bash
docker-compose build
docker-compose up
```

## Create a Superuser

### **Why Create a Superuser?**

A superuser account is necessary to access and manage the Django Admin panel. It provides full control over:

- User accounts and permissions.
- Data stored in the database.
- Admin-specific configurations.

### **Steps to Create a Superuser**

1.  **Navigate to the Project Directory**
    Open a terminal and move to the directory where the project is located:
    ```bash
    cd path/to/your/project
    ```
2.  **Run the Superuser Creation Command**
    Use the following command to create a superuser:

    ```bash
    docker-compose run --rm backend python manage.py createsuperuser
    ```

3.  **Provide Superuser Details**
    - **Email:** Enter the email address for the superuser (e.g., `admin@example.com`).
    - **Username:** Choose a username for the superuser (e.g., `admin`).
    - **Password:** Enter a strong password and confirm it.
4.  **Verify Success**
    After entering the details, you will see a confirmation message in the terminal indicating the superuser has been successfully created.

---

### **Access Django Admin**

1.  **Run the Application**
    Ensure the project is running:

    ```bash
    docker-compose up
    ```

2.  **Open Django Admin in a Browser**
    Navigate to the admin panel: http://localhost:8001/admin

3.  **Log In**
    Use the credentials (email/username and password) you set during superuser creation.

### **Best Practices**

- **Local Development:** The superuser created locally only applies to your development environment. You’ll need to repeat the process for production.
- **Password Security:** Use a strong password and avoid reusing production credentials in development.
- **Managing Permissions:** Once inside the admin panel, you can assign roles and permissions to other users to restrict access as needed.
