# Django CLI Application for Property Information Rewriting

This project connects a new Django project to a separate Scrapy project for accessing the Scrapy database, which is stored in a PostgreSQL container. The Django project leverages the Ollama model to rewrite property titles and store the updated information back into the property table.

## Key Components

1. **Django Project**: Acts as the main interface for processing and rewriting property titles.
2. **Scrapy Project**: Provides the source data stored in a PostgreSQL database.
3. **PostgreSQL**: Used as a shared database container between Django and Scrapy projects.
4. **Ollama Model**: Utilized to rewrite property titles intelligently.

## Workflow

1. The Django project retrieves property information from the PostgreSQL database populated by the Scrapy project.
2. The property titles are processed using the Ollama model.
3. The rewritten titles are stored back into the `hotels` table in the PostgreSQL database.

## Technologies Used

- **Django**: Backend framework for managing and updating property information.
- **Scrapy**: Web scraping framework for populating the database.
- **PostgreSQL**: Database management system.
- **Ollama**: Model for rewriting property titles.
- **Docker**: Containerization for PostgreSQL and other project components.

## Usage

1. **Set up the PostgreSQL container** using Docker.
2. **Run the Scrapy project** to populate the database with property data.

3. **Launch the Django project** to rewrite property titles.
4. Processed titles are automatically updated in the PostgreSQL database.

## Step 1: Run the Scrapy Project
### Clone the Scrapy Repository
```bash
git clone <scrapy-repository-url>
cd <scrapy-project-directory>
```

## Step 2: Run the Django-Ollama Project
### Clone the Repository
```bash
git clone <django-ollama-repository-url>
cd django-ollama-property-rewriter
```
## Installation and Setup
1. Start Docker Services
Build and start the Docker containers:

```bash
docker-compose up --build
```