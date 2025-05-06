
# Blue Spark Sales Force Automation

Backend code written using python and fastapi framework<br>
Local install of Supabase to manage Postgres database and authentication

## First steps

After cloning the repo create a `.gitignore` file and add the following<br>
```sh
    .env
    .venv/
    alembic.ini
    alembic/

    __pycache__/
    models/__pycache__/
    routes/__pycache__/
    utils/__pycache__/

```



## Setup FastAPI

If you are not going to use docker follow these instructions:<br>

*[Start by installing the Virtual Environment from the official documentation](https://fastapi.tiangolo.com/virtual-environments/#create-a-virtual-environment)*

Then create a .env file and add all your environment variables. ie,<br>
`POSTGRES='postgresql://username:password@localhost:5432/postgres'`<br>
`SECRET_KEY='your-secret-key'`<br>
`ENV='production'` (for production build, removes seed route)

### Activate the virtual environment

Make sure you are in the directory that the project is in by your terminal

#### For Windows
`.venv/Scripts/activate`
#### For Linux
`source .venv/bin/activate`

### Instal dependencies

`pip install -r requirements.txt`

### Run fastAPI 

Firstly make sure that the virtual environment is activated 
then run the following command to run it using development mode
`fastapi dev main.py`

For production `fastapi run main.py`



### Migrations

URL for postgres server is set in the `alembic.ini` file,
change the value of `sqlalchemy.url =` for a new server migration.<br>

Migrations are done using [alembic](https://alembic.sqlalchemy.org/en/latest/)
To create a migration script:<br>

`alembic revision --autogenerate -m "your message"`<br>
Then Open alembic/versions/eeccaebd4e10_initial_migration.py and add this at the top:
`import sqlmodel` <br>

To run the script on the database server:<br>

`alembic upgrade head`

## Seed the Database



## Docker

First change the environment variable for supabase inside the dockerfile

Then run the following commands<br>

`docker build -t sfaimage .`<br>
`docker run --network host sfaimage`<br>

For Production<br>

`docker run -d --network host sfaimage`<br>

To enter a container that is running<br>

`docker exec -it <container_id> bash`<br>
