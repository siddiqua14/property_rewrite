# Django-CLI Application with LLM Model for Property Information Rewriting

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

## Run the Scrapy Project
Ensure the `Scraper_Project` is cloned, set up, and running as it serves as the data source for this project. following the git repository [Scraper_project](https://github.com/siddiqua14/Scraper_Project)

### Clone the Scrapy Repository

```bash
git clone https://github.com/siddiqua14/Scraper_Project.git
cd Scraper_Project
```

## Setting Up the LLM Project
### Step 1: Clone the Repository
```bash
git clone https://github.com/siddiqua14/property_rewrite.git
cd property_rewrite
```
### Step 2: Set Up a Virtual Environment
```bash
python3 -m venv venv  # or python -m venv venv 
source venv/bin/activate # for windows: venv\Scripts\activate
```
### Step 3: Install required Python dependencies:
The Docker build process installs dependencies from the requirements.txt file.
```bash 
pip install -r requirements.txt
```
## Step 4: Docker Setup
Ensure Docker Desktop is running. Then, execute the following commands:
1. Build and Run the Application:

```bash
docker-compose up --build
```
- For stopping  the Application(if need):
`Ctrl + C` or `docker-compose down`

## Ollama Model

### Interacting with the Ollama Service

- Access the Ollama Container:
```bash
docker-compose exec ollama /bin/bash
```
- Pull a Model:
```bash
ollama pull phi  # or use tinyllama for a lightweight model
```
- List Available Models:
```bash
ollama list
```
### Recommended Model
Use the `Phi` model for this project. It balances performance and capability.

## Database Configuration
The project uses two PostgreSQL databases:
1. ollama_data: For storing rewritten titles, summaries, ratings, and reviews.
2. scraper_db: From the Scrapy project, storing scraped hotel data.

## Django CLI Commands

### Command 1: Rewrite Property Titles and Descriptions
Automates rewriting property titles and descriptions using the Ollama LLM.
Command:
```bash
docker exec -it django python manage.py rewrite_hotels
```
### Command 2: Generate Property Summaries, Ratings and Reviews
Generates concise summaries for properties and stores them in a new table. Creates AI-powered ratings and reviews for properties.
Command:
```bash
docker exec -it django python manage.py rewrite_property_info
 ```
## Testing
### Run Unit Tests with Coverage:
```bash
docker-compose exec django bash
coverage run manage.py test
coverage report
```

## Accessing Admin Interface

- Steps:

1. Start the Django server:
```bash
docker-compose up
```
2. Open your browser and navigate to `http://localhost:8000/admin.`

3. Log in using the superuser credentials you created.
- by using this command:
```bash
docker exec -it django python manage.py createsuperuser
```
- Follow the prompts to set up a username, email, and password for the superuser.
You can then log in to the Django admin panel at `http://localhost:8000/admin` using the credentials you just created.
4. Access the `PropertySummary`, `PropertyRatingReview`, and `Hotel` tables.

## Notes

- GitHub Repository: Ensure all updates are pushed to a public GitHub repository.
- Documentation: Include any additional instructions or insights in the README.md file.
- Memory Limit: Adjust the memory limit for the Ollama container in docker-compose.yml if needed.
#### Running the CLI Command for Multiple Properties
By default, the CLI command is set to process only 2 properties for testing purposes (to speed up execution). If you wish to run the command for more properties or hotels (up to 5), you can make a small modification in the code.
To adjust the number of properties being processed:

1. Open the management/commands directory.
2. Locate the line 16 in the relevant file.
3. You will see the following line:
```bash
properties = properties[:2]  # Limit to 2 properties for testing (can adjust as needed)
```
4. Modify the number 2 to any desired number (e.g., 5 for five properties):
```bash
properties = properties[:5]  # Limit to 5 properties (adjust as needed)
```
This change will allow the CLI command to process the specified number of properties or hotels.

