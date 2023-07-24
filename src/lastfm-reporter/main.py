from APIClient import UserAPI
import json
import database

if __name__ == "__main__":

    username = ""

    database.update_user_listened_tracks(username, period="7day")
