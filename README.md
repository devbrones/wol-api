# WOL-API
## Watch-on-LBRY API proxy that saves data from LBRY to a database

Current version: **1.1.81**

**Requirements:**
- pipenv
- flask (pipenv install flask)
- postgresql
- libpq-dev

**Installation instructions:**

Clone the repository from Github: 

```git clone https://github.com/devbrones/wol-api```

Change working directory to the recently cloned folder: 

```cd wol-api```

Install dependencies:

```pipenv install```

Fetch submodules:

```git submodules update && cd docs/wol-docs && git pull```

Configure api settings in /src/apimod/apcnf.py

Run the API:

```pipenv run python src/apimod/index.py```

See docs for more info.

**Common issues:**
P: Infinite loading after running the command.

F: 
- Make sure you have configured /src/apimod/apcnf.py properly.

