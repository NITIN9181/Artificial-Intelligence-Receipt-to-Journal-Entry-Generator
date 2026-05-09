# Local Setup with Docker Compose

This guide provides detailed, step-by-step instructions to get the Artificial Intelligence Receipt to Journal Entry Generator running locally using Docker Compose. 

By using Docker Compose, you spin up the entire stack—Frontend, Backend API, PostgreSQL database, and MinIO storage—in a consistent and isolated environment without needing to install Node.js or Python locally.

## Prerequisites

1. **Docker & Docker Compose:** Ensure you have [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running.
2. **Ports:** Ensure the following ports are free on your machine:
   - `3000` (Frontend)
   - `8000` (Backend FastAPI)
   - `5432` (PostgreSQL Database)
   - `9000` / `9001` (MinIO Object Storage)

---

## Step 1: Build and Start the Containers

1. Open a terminal or command prompt.
2. Navigate to the root directory of the project:
   ```bash
   cd d:\PROGRAMS\Artificial-Intelligence-Receipt-to-Journal-Entry-Generator
   ```
3. Run the following command to build the Docker images and start the services in the background (`-d` flag):
   ```bash
   docker-compose up --build -d
   ```
   *Note: The first time you run this, it may take a few minutes to download the base images and install the required dependencies.*

---

## Step 2: Initialize the Database (Run Migrations)

Because the project uses a fresh local PostgreSQL database inside a Docker container, you must run the database migrations to create the necessary tables before you can use the app.

1. Keep your terminal in the root directory.
2. Execute the Alembic migrations inside the `fastapi` container:
   ```bash
   docker-compose exec fastapi alembic upgrade head
   ```
   *You should see output indicating that various tables (users, receipts, journal entries, etc.) have been created.*

---

## Step 3: Access the Application

Your full stack is now running locally. You can access the different services via your web browser:

- **🖥️ Web Application (Frontend):** [http://localhost:3000](http://localhost:3000)
- **⚙️ Backend API Swagger Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **🗄️ MinIO Object Storage Console:** [http://localhost:9001](http://localhost:9001)
  - *Username:* `minioadmin`
  - *Password:* `minioadmin`

---

## Step 4: Managing the Environment

### Viewing Logs
If you encounter errors or want to monitor the application's activity in real-time, you can view the logs for all containers:
```bash
docker-compose logs -f
```
*(Press `Ctrl+C` to stop watching the logs).*

### Stopping the Application
When you are finished testing, you can stop the containers. 
```bash
docker-compose down
```
> **Note:** Running `docker-compose down` shuts down the containers but preserves your database and storage data in Docker volumes (`postgres_data` and `minio_data`). The next time you run `docker-compose up -d`, your previously created users and uploaded receipts will still be there.

### Complete Reset (Optional)
If you want to completely wipe your local database and storage to start completely fresh, you can remove the containers **and** the associated volumes:
```bash
docker-compose down -v
```
*Warning: This will delete all your local data.*
