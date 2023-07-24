from intervals import Intervals
from ast import literal_eval
from datetime import datetime
from database import get_user_downloaded_intervals, update_user_downloaded_intervals
from APIClient import UserAPI, TrackAPI
import json
import database
from database import Track
import sqlalchemy

username = "GodofDevilll"

userapi = UserAPI()
tracklist = database.get_user_listened_tracks(username)

for track in tracklist:
    print(track.name)