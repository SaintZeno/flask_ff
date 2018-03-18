# flask_ff
Flask App for Football data

Minimal Flask Application intended to show views of aggregate football data using a personal postgres database.
--So far, this app is focused on Airyards data provided by Josh Hermsmeyer at http://airyards.com

--This application stores data in a postgres database that is specified in src/DBconnect.py and runs one simple aggregation on said data to 
display in "sandbox" view (using a JS pivot-table). For the time being, users are required to specify the database connection direcly in the 
DBconnect class in order for the app to run successfully.

## Running the app
To run the app, ensure that all python modules are installed (flask, requests, json, pandas, and psycopg2) and that DBconnect is pointing 
at your personal postgres database instance; you can also adjust applications's port in which it runs on (default is port 8080) in main.py. 
Once the inital connections are setup simply run the main script from the command line (`python main.py`) and navigate to the correct 
IP address and port (ie localhost:8080) in your web-browser. 


## flask_ff 2.0 updates will include
(1) adding database configuration so users don't need to adjust DBconnect class
(2) add requirements file for easy python installs
