import pandas as pd
import matplotlib as plt
from APIClient import UserAPI, TrackAPI
from datetime import datetime
import json
import sqlite3
import sqlalchemy.orm as orm
import sqlalchemy
from sqlalchemy import select, insert
from database import Track
import database


if __name__ == "__main__":

    username = ""

    database.update_user_listened_tracks(username, period="overall")