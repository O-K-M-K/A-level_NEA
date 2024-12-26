# Description

This repo contains the report and source files for my A-level NEA project for my A-level AQA Computer Science course.

This project achived a mark of 74/75




![github_demo](https://github.com/user-attachments/assets/3c0491c9-afb0-4be4-b7be-e878863dd0c2)





# Running the project youself

Running the project youself will reuqire numerous changes to the code and adding a credential to windows credential manager. If you just want to get an understanding of what this project does read at the above description or watch the youtube videos displaying the project through testing. If you, for some strange reason, are desperate to run this project follow the instructions below. 

## Prerequisites
Before you can run this project, you need to have the following installed on your machine:
1. **Python (version 3.11.3)** - This is the version I have most recently tested the project on. It will probably work on newer versions too.
2. **Tkinter** - This is used for the GUI 


## Running the project

In the instructions below I have done my best to cover all the steps you will need to take to run the project on your computer however they may be steps I have missed.

1. Set up a new generic credential using windows credential manager and configure it such that it works with keyring. Adjust line 200 in `neat_server.py` replacing the service_name and username of the `.get_password` function with the service_name and username for the credential you just made.
2. Adjust the following file paths to desired filepaths:
    - `neat_server.py` line 30 - This should be a path to an sqlite3 database. A database will be created if one does not exist already
    - `neat_gui_oop.py` line 21 - This should be a path to the assets folder

3. Run neat_server.py using command prompt. 
```
python neat_server.py
```
Upon running it will print some debug information. Make note of the IPv4 address and the port number the server is listening on. You can change the port number by changing the value of the constant "PORT" on line 20 in neat_server.py. 

4. Edit the port and Ipv4 address in neat_secure_client.py to be the same as those the server is listening on
5. Run neat_gui_oop.py using command prompt.
```
python neat_gui_oop.py
```
