import pandas as pd
import matplotlib as plt
from APIClient import UserAPI
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
    

    user = UserAPI()

    tracklist = database.get_user_listened_tracks(
        username= username,
        from_date=datetime(2022, 1, 14),
        to_date=datetime(2022, 2, 1),
        #period="7day",
        limit=200
    )

    database.upload_tracks(username, tracklist)
