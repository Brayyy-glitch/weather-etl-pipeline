# Weather ETL Pipeline

![Daily weather pipeline](https://github.com/Brayyy-glitch/weather-etl-pipeline/actions/workflows/daily.yml/badge.svg)

A small data pipeline that collects hourly weather data for three South African cities (Johannesburg, Cape Town and Durban), checks that the data is sensible, and saves it into a database. It runs inside Docker, has automated tests, and runs by itself every day using GitHub Actions.

**In plain English:** every day, this project asks a free weather service "what has the weather been like in these cities?", throws away or flags anything that looks wrong, and stores the good data so it builds up over time.

---

## Table of contents

1. [What this project does](#what-this-project-does)
2. [Key words explained](#key-words-explained)
3. [How it works](#how-it-works)
4. [Tech stack](#tech-stack)
5. [Project structure](#project-structure)
6. [Getting started](#getting-started)
7. [Looking at the data](#looking-at-the-data)
8. [Running the tests](#running-the-tests)
9. [Data quality checks](#data-quality-checks)
10. [Daily automation with GitHub Actions](#daily-automation-with-github-actions)
11. [Design decisions](#design-decisions)
12. [Known limitations and future improvements](#known-limitations-and-future-improvements)
13. [Troubleshooting](#troubleshooting)
14. [Data source and credit](#data-source-and-credit)

---

## What this project does

This is an **ETL pipeline**. ETL stands for **Extract, Transform, Load**, which are the three jobs the pipeline does, in order:

| Step | What happens | Example |
|---|---|---|
| **Extract** | Download raw weather data from the internet | Ask the Open-Meteo API for Johannesburg's weather |
| **Transform** | Clean it up and put it in a tidy table | Turn a messy block of JSON text into rows and columns |
| **Validate** | Check that the data is trustworthy | Reject a temperature of 99 degrees Celsius |
| **Load** | Save it into a database | Add the rows to a SQLite file |

Each run collects, for each city, the **last 2 days plus today** of hourly readings (72 rows per city), covering:

- Temperature (degrees Celsius)
- Rainfall (millimetres)
- Wind speed (kilometres per hour)

The pipeline can be run as many times as you like without creating duplicate rows. Running it twice gives the same database as running it once.

---

## Key words explained

If any of these are new to you, don't worry. Here's what they mean in this project.

| Word | Meaning |
|---|---|
| **API** | A way for programs to ask another service for data. Here, we ask Open-Meteo for weather data. |
| **JSON** | A text format that APIs use to send data. It looks like a nested list of names and values. |
| **DataFrame** | A table of rows and columns in the pandas library, like a spreadsheet inside Python. |
| **SQLite** | A simple database stored in a single file (`data/weather.db`). It needs no server. |
| **Primary key** | A column (or combination of columns) that uniquely identifies each row. Here it is `(city, timestamp)`: one row per city per hour. |
| **Validation** | Checking data for problems before saving it, so bad data never reaches the database. |
| **Idempotent** | Running something many times gives the same result as running it once. This pipeline is idempotent. |
| **Docker** | A tool that packages Python and all the libraries into a "container", so the project runs the same way on any computer. |
| **Container / image** | An image is the packaged recipe. A container is a running copy of it. |
| **pytest** | A tool that runs automated tests on the code. |
| **GitHub Actions** | GitHub's built-in automation. It runs the pipeline on a schedule without you touching anything. |
| **Cron** | A way of writing schedules. `0 5 * * *` means "every day at 05:00". |

---

## How it works

```
 Open-Meteo API
       |
       v
  [ extract ]    Download the raw data (retries up to 3 times if it fails)
       |
       v
 [ transform ]   Turn the JSON into a clean table with proper data types
       |
       v
 [ validate ]    Check for missing values, duplicates and impossible values
       |
       v
   [ load ]      Save new rows into SQLite (skips rows that already exist)
       |
       v
 data/weather.db
```

All of this code lives in one file, `pipeline.py`. Here's what each function does:

- **`extract(city, lat, lon)`** calls the Open-Meteo API for one city. If the request fails (for example the network drops), it waits 2 seconds and tries again, up to 3 attempts. If all attempts fail, it stops with a clear error message.
- **`transform(raw, city)`** takes the raw JSON and builds a pandas DataFrame with the columns `city`, `timestamp`, `temperature_c`, `rain_mm` and `wind_kmh`. Timestamps become real dates and the measurements become numbers.
- **`validate(df)`** runs the quality checks (see [Data quality checks](#data-quality-checks)). If anything is wrong, it raises an error and nothing is saved for that city.
- **`load(df)`** inserts the rows into SQLite. The table's primary key on `(city, timestamp)` combined with `INSERT OR IGNORE` means rows that already exist are skipped, so there are no duplicates.
- **`main()`** runs the steps above for each city. If one city fails, the error is logged and the pipeline carries on with the other cities. At the end, if any city failed, the program exits with an error code so the failure is visible.

### What the database looks like

The data is stored in one table called `weather`:

| Column | Type | Meaning |
|---|---|---|
| `city` | text | City name, for example `Johannesburg` |
| `timestamp` | text | Local time (Africa/Johannesburg) for the hourly reading, for example `2026-10-29 14:00:00` |
| `temperature_c` | number | Temperature in degrees Celsius |
| `rain_mm` | number | Rainfall in millimetres |
| `wind_kmh` | number | Wind speed in km/h |

The primary key is `(city, timestamp)`.

---

## Tech stack

| Tool | Used for |
|---|---|
| Python 3.12 | The programming language |
| requests | Calling the weather API |
| pandas | Cleaning and reshaping the data |
| SQLite | Storing the data |
| pytest | Automated tests |
| Docker | Packaging the project so it runs the same everywhere |
| GitHub Actions | Running the pipeline automatically every day |

Everything used here is free.

---

## Project structure

```
weather-etl-pipeline/
  .github/
    workflows/
      daily.yml          # The daily automation (GitHub Actions)
  data/
    weather.db           # The SQLite database (created and updated by the pipeline)
  tests/
    test_pipeline.py     # Automated tests
  .dockerignore          # Files Docker should ignore when building
  .gitignore             # Files Git should ignore
  Dockerfile             # The recipe for building the Docker image
  explore.py             # A scratch script used to study the API's response
  pipeline.py            # The pipeline itself
  pytest.ini             # Tells pytest where to find pipeline.py
  README.md              # This file
  requirements.txt       # The Python libraries the project needs
```

---

## Getting started

### What you need

1. **Git**, to download the project. Check with `git --version`.
2. **Docker**, to run it. Install Docker Desktop (Windows/macOS) or Docker Engine (Linux), then check with `docker --version`.

You do **not** need to install Python or any Python libraries yourself. Docker takes care of that.

> Make sure Docker is running before you use any `docker` command. On Windows and macOS, open Docker Desktop and wait until it says it is running.

### Step 1: Download the project

```bash
git clone https://github.com/Brayyy-glitch/weather-etl-pipeline.git
cd weather-etl-pipeline
```

### Step 2: Build the Docker image

This creates a packaged copy of Python plus the libraries the project needs. The first build takes a minute or two.

```bash
docker build -t weather-etl .
```

### Step 3: Run the pipeline

**Linux / macOS:**

```bash
mkdir -p data
docker run --rm --user "$(id -u):$(id -g)" -v "$(pwd)/data:/app/data" weather-etl
```

**Windows (PowerShell):**

```powershell
mkdir data -Force
docker run --rm -v "${PWD}/data:/app/data" weather-etl
```

What the parts of that command mean:

| Part | Meaning |
|---|---|
| `docker run` | Start a container from an image |
| `--rm` | Delete the container when it finishes |
| `--user "$(id -u):$(id -g)"` | (Linux/macOS) Create files as you instead of as the root user, so you can edit or delete them later |
| `-v "$(pwd)/data:/app/data"` | Share your local `data` folder with the container, so the database is saved on your computer and not lost when the container stops |
| `weather-etl` | The image to run |

### What you should see

The pipeline prints a log of what it is doing. On a first run you'll see something like this:

```
2026-10-29 10:15:06,057 INFO Extracted data for Johannesburg
2026-10-29 10:15:06,070 INFO Validation passed for Johannesburg (72 rows)
2026-10-29 10:15:06,074 INFO Loaded 72 new rows (0 already existed)
2026-10-29 10:15:06,979 INFO Extracted data for Cape Town
2026-10-29 10:15:06,989 INFO Validation passed for Cape Town (72 rows)
2026-10-29 10:15:06,993 INFO Loaded 72 new rows (0 already existed)
2026-10-29 10:15:07,900 INFO Extracted data for Durban
2026-10-29 10:15:07,916 INFO Validation passed for Durban (72 rows)
2026-10-29 10:15:07,923 INFO Loaded 72 new rows (0 already existed)
2026-10-29 10:15:07,924 INFO Finished. 216 new rows inserted.
```

If you run it a second time straight away (or if the repository already contains data), you'll see `Loaded 0 new rows (72 already existed)`. That is correct. It shows the pipeline doesn't create duplicates.

---

## Looking at the data

You can query the database with a short command. This one counts how many rows each city has:

**Linux / macOS:**

```bash
docker run --rm -v "$(pwd)/data:/app/data" weather-etl python -c "import sqlite3; c = sqlite3.connect('data/weather.db'); print(c.execute('SELECT city, COUNT(*) FROM weather GROUP BY city').fetchall())"
```

You should see something like `[('Cape Town', 72), ('Durban', 72), ('Johannesburg', 72)]`. The numbers grow as the daily automation adds more data.

To see the five most recent readings, swap the SQL for this:

```sql
SELECT * FROM weather ORDER BY timestamp DESC LIMIT 5
```

If you'd rather browse the data visually, open `data/weather.db` in a free database viewer such as [DB Browser for SQLite](https://sqlitebrowser.org/) or DBeaver.

---

## Running the tests

The tests check that the data validation catches bad data. Run them with:

```bash
docker run --rm weather-etl pytest
```

You should see `5 passed`. The tests cover:

| Test | What it proves |
|---|---|
| Valid data passes | Good data is accepted |
| Impossible temperature fails | A temperature of 99 degrees Celsius is rejected |
| Missing value fails | A missing rainfall value is rejected |
| Duplicate rows fail | The same city and hour twice is rejected |
| Transform builds expected columns | The data comes out with the right column names |

> If you change `pipeline.py` or the tests, rebuild the image first with `docker build -t weather-etl .`, because the code is copied into the image when it is built.

---

## Data quality checks

Before any data is saved, `validate()` runs these checks. If **any** of them fail, the error lists **all** the problems at once and that city's data is not saved.

| Check | Why it matters |
|---|---|
| The data is not empty | An empty response means something went wrong upstream |
| No missing values in temperature, rain or wind | Gaps would silently distort averages and charts |
| No duplicate (city, timestamp) rows | One reading per city per hour is the rule |
| Temperature between -50 and 60 degrees Celsius | Anything outside that range is physically implausible for South Africa |
| Rainfall is not negative | You can't have negative rain |
| Wind speed is not negative | Speed can't be negative |

Failing loudly is better than saving bad data quietly, because people make decisions from the database and assume it is correct.

---

## Daily automation with GitHub Actions

The file `.github/workflows/daily.yml` tells GitHub to run the pipeline automatically. It runs:

- **Every day at 05:00 UTC** (07:00 in South Africa), and
- **On demand**, from the **Actions** tab on GitHub, using the **Run workflow** button.

Each run does the following:

1. Downloads the project code.
2. Builds the Docker image.
3. Runs the tests. If they fail, the run stops.
4. Runs the pipeline.
5. Commits the updated `data/weather.db` back to the repository, with the message `Update weather data`.

Step 5 is needed because GitHub's runners are temporary computers. Everything on them is deleted when the job ends, including the database. Committing the database back to the repo is how the data builds up from one day to the next. The commit step uses `if: always()`, so good data from the cities that worked is still saved even if one city failed.

**If a city fails:** the pipeline carries on with the other cities, but the run is marked as **failed** (red cross in the Actions tab). This is on purpose, so a problem can't go unnoticed for weeks.

### Running it manually

1. Open the repository on GitHub and click the **Actions** tab.
2. Click **Daily weather pipeline** in the left sidebar.
3. Click **Run workflow**, then the green **Run workflow** button.
4. Click the new run to watch each step. Green ticks mean success.

> GitHub may pause scheduled workflows in public repositories after about 60 days with no repository activity. If the daily runs stop, run the workflow manually once to wake it up.

---

## Design decisions

**Why SQLite?**
It is free, needs no server, and stores everything in one file. This makes it ideal for a learning project and easy to run anywhere. For a bigger system I would move to PostgreSQL or a cloud data warehouse.

**Why is `(city, timestamp)` the primary key?**
Each city should have exactly one reading per hour. Making that a database rule means duplicates are impossible, and it is what allows the pipeline to be safely re-run.

**Why validate before loading?**
Bad data that reaches the database spreads into reports and decisions. Stopping it at the door is much cheaper than cleaning it up later.

**Why does one failing city not stop the others?**
If Durban's data fails, Johannesburg and Cape Town are still good and are saved. But the run is still reported as failed, so the problem is visible.

**Why retry failed requests?**
Networks drop and servers have slow moments. A short wait and a second attempt fixes most temporary problems, and after 3 attempts the pipeline gives up with a clear error.

**Why Docker?**
It packages Python and every library, so the project runs the same on any computer and in GitHub Actions, with no "it works on my machine" problems and no need to install anything except Docker.

**Why commit the database back to the repo?**
It is the simplest way to keep data between daily runs on temporary GitHub machines. It works well for a small database like this one. A larger project would use a hosted database instead.

---

## Known limitations and future improvements

Being honest about the limits is part of good engineering. Here are the main ones, with ideas for improving each.

| Limitation | Possible improvement |
|---|---|
| Each run includes the rest of today, which is **forecast** data and not yet measured. Rows that already exist are never updated (`INSERT OR IGNORE`), so a forecast value stays in the database even after the real value is known. | Only load hours that have already passed, or update existing rows when new values arrive. |
| Failed requests are retried even for errors that retrying can't fix (such as a 400 Bad Request). | Retry only on temporary problems such as timeouts, 429 and 5xx errors. |
| Adding a city means editing the `CITIES` dictionary in `pipeline.py`. | Move the city list into a config file. |
| No alert is sent when the pipeline fails (other than the red cross in GitHub). | Send an email or Discord message on failure. |
| Everything is in one file. | Split into separate modules (`extract.py`, `transform.py`, `load.py`). |
| SQLite in the repo is fine for small data but won't scale. | Move to PostgreSQL or a cloud warehouse, and model the data as a star schema (fact and dimension tables). |
| The checks are written by hand. | Use a data-quality library such as pandera or Great Expectations. |

---

## Troubleshooting

| Problem | Likely cause and fix |
|---|---|
| `Cannot connect to the Docker daemon` | Docker isn't running. Start Docker Desktop and wait until it says it is running. |
| `ModuleNotFoundError: No module named 'pandas'` | You ran the script with your own Python instead of Docker. Use the `docker run` commands above. |
| My code changes have no effect | The image contains the old code. Rebuild with `docker build -t weather-etl .`. |
| The database is empty or missing after a run | The `-v` (volume) part of the command is missing, so the database was saved inside the container and deleted. Include `-v "$(pwd)/data:/app/data"`. |
| `Permission denied` on `data/weather.db` (Linux) | The file was created by root. Fix it with `sudo chown -R $USER:$USER data`, and use `--user "$(id -u):$(id -g)"` in future runs. |
| `no such table: weather` | The pipeline hasn't run yet, so the table doesn't exist. Run the pipeline first. |
| `Failed cities: ...` in the log, and the exit code is 1 | That city's data failed to download or failed validation. Read the error above it in the log. |
| API errors such as `400 Bad Request` | A request setting is wrong, for example invalid coordinates. |
| `git push` rejected after the automation ran | The workflow added a commit on GitHub. Run `git pull` first, then push again. |

---

## Data source and credit

Weather data provided by [Open-Meteo.com](https://open-meteo.com/) under the [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) license. The free API is for non-commercial use, which suits this learning project.

---

## About this project

Built as a learning project to practise core data engineering skills: extracting data from an API, cleaning and validating it, loading it into a database without duplicates, logging, testing, containerising with Docker, and scheduling with GitHub Actions.

Author: [Ntswaki Mohale](https://github.com/Brayyy-glitch)

WTC-A46UTD3W
