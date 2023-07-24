import sqlalchemy.orm as orm
import sqlalchemy
from sqlalchemy import exc
from datetime import datetime, timedelta
from dataclasses import dataclass
from APIClient import UserAPI, TrackAPI
from dateutil.relativedelta import relativedelta
import os
from intervals import Intervals
from ast import literal_eval
from typing import Dict, List, Tuple


SECONDS_IN_MONTHS = 2678400
LIST_OF_PERIODS = ["overall", "7day", "1month", "3month", "6month", "12month"]

class Base(orm.DeclarativeBase):
    pass

@dataclass
class Track(Base):
    __tablename__ = "track"

    id: orm.Mapped[int] = orm.mapped_column(primary_key=True)
    name: orm.Mapped[str]
    loved: orm.Mapped[bool]
    url: orm.Mapped[str]
    date: orm.Mapped[datetime]
    artist_name: orm.Mapped[str]
    album_name: orm.Mapped[str]



def create_connection(db_name: str) -> orm.Session:
    """
    Create a database connection to a SQLite database and return a current Session
    """

    try:
        #Create dir if does not exist
        check_user_files(db_name)

        engine = sqlalchemy.create_engine(f"sqlite+pysqlite:///backup\{db_name}\{db_name}.db", echo=True)
        
        Session = sqlalchemy.orm.sessionmaker(bind=engine)
        Base.metadata.create_all(engine)
        session = Session()

        return session
        
    except exc.SQLAlchemyError as e:
        print(e)

def update_user_listened_tracks(
        username: str,
        to_date: datetime = None,
        from_date: datetime = None,
        period: str = "", # overall | 7day | 1month | 3month | 6month | 12month
        limit: int = 50
) -> list:
    """
    Get a list of tracks from a given time interval. Default interval - 7 days
    """

    userAPI = UserAPI()
    

    if period:
        if period not in LIST_OF_PERIODS: 
            print("Incorrect period")
            return None
        elif period == "7day": from_date = datetime.now() - relativedelta(days=7)
        elif period == "1month": from_date = datetime.now() - relativedelta(months=1)
        elif period == "3month": from_date = datetime.now() - relativedelta(months=3)
        elif period == "6month": from_date = datetime.now() - relativedelta(months=6)
        elif period == "12month": from_date = datetime.now() - relativedelta(months=12)
        elif period == "overall": from_date = datetime(2001, 1, 1)
        to_date = datetime.now().replace(microsecond=0)
    
        #Resetting the time clock, to get the whole day's tracks
        from_date = from_date.replace(hour=0, minute=0, second= 0, microsecond=0)

    #Set the default 7 days time span if one of the ends is not set
    if to_date == None or from_date == None:
        to_date = datetime.now().replace(microsecond=0)
        from_date = (to_date - relativedelta(days=7)).replace(hour=0, minute=0, second= 0, microsecond=0)

    #Find the missing intervals 
    downloaded_internals = Intervals(get_user_downloaded_intervals(username))
    missing_intervals = downloaded_internals.complement((from_date.timestamp(), to_date.timestamp()))
    
    #List of tracklist intervals
    tracklist_intervals = []
    tracklist = []

    #Process each missing interval separately
    for interval in missing_intervals:

        from_date = datetime.fromtimestamp(interval[0])
        to_date = datetime.fromtimestamp(interval[1])

        #Select limit depending on the length of the interval
        limit = int(min(1000, max((to_date - from_date).total_seconds() / SECONDS_IN_MONTHS, 1) * 100))


        #Getting the count of pages to call api 
        response = userAPI.getRecentTracks(
            user= username, 
            limit= limit,
            from_date= from_date,
            to_date= to_date)
        total_pages = int(response["recenttracks"]["@attr"]["totalPages"])       

        #Getting list of tracks
        tracklist = []


        for page in range(1, total_pages + 1):
            print(f"Tracklist size - {len(tracklist)}")
            response = userAPI.getRecentTracks(
                user= username,
                limit= limit,
                page= page,
                from_date= from_date,
                to_date= to_date,
            )

            #Add tracks to tracklist and skip now playing track
            tracklist +=  [track for track in response["recenttracks"]["track"] 
                        if not track.get("@attr") and int(track["date"]["uts"]) >= from_date.timestamp()]
        
        #Update intervals for current tracklist
        tracklist_intervals.append((from_date.timestamp(), to_date.timestamp()))
        
    #Push the intervals to the last position of the tracklist     

    upload_tracks(username= username, tracklist=tracklist)
    update_user_downloaded_intervals(username= username,new_interval= tracklist_intervals)

    return tracklist

def parse_track_json(track: dict) -> Track:
    """
    Get all the necessary information about the track 
    """
        
    trackAPI = TrackAPI()

    # search_response = trackAPI.getInfo(
    #     track= track["name"],
    #     artist= track["artist"]["name"]
    # )        
    # track["duration"] = int(search_response["track"]["duration"])
    # if track["duration"] == 0: track["duration"] = None



    #Track parameters
    track_info = Track(
        id= int(track["date"]["uts"]),
        name= track["name"],
        loved= False if track["loved"] == '0' else True,
        date= datetime.fromtimestamp(float(track["date"]["uts"])),
        url= track["url"],
        artist_name= track["artist"]["name"],
        album_name= track["album"]["#text"],
        

    )
    return track_info

def get_user_downloaded_intervals(username: str) -> List[Tuple]:
    """
    Get user downloaded intervals
    """
    check_user_files(username)


    intervals_file_path = f".\\backup\\{username}\\downloaded_tracks_intervals"
    intervals_file = open(intervals_file_path, "r+")

    intervals_list_str = intervals_file.readline()
    if intervals_list_str == "": intervals_list_str = "[]"
    
    intervals_list = literal_eval(intervals_list_str)

    intervals_file.close()
    return intervals_list

def update_user_downloaded_intervals(
        username: str,
        new_interval: Tuple
):
    """
    Create or update information about user downloaded tracks, using download intervals
    """
    downloaded_intervals = Intervals(get_user_downloaded_intervals(username))
    
    check_user_files(username)

    intervals_file_path = f".\\backup\\{username}\\downloaded_tracks_intervals"
    intervals_file = open(intervals_file_path, "r+")

    #Get information about new interval
    from_date = int(new_interval[0][0])
    to_date = int(new_interval[0][1])

    #Add new interval and rewrite file
    downloaded_intervals.add([(from_date, to_date)])
    intervals_file.truncate(0)
    intervals_file.write(str(downloaded_intervals))
    intervals_file.close()

def upload_tracks(
        username: str,
        tracklist: list
):
    """
    Loads the selected tracks into the database
    """

    #If tracklist is empthy
    if len(tracklist) == 0:
        return

    session = create_connection(db_name= username)
    

    id = 0
    #Insert or replace tracks to database
    for track in tracklist:

        if(id == int(track["date"]["uts"])):
            continue
               
        session.merge(parse_track_json(track))
        id = int(track["date"]["uts"])




    session.commit()
    session.close()

def get_user_listened_tracks(
        username:str,
        from_date: datetime = None,
        to_date: datetime= None,
) -> List[Track]:
    """
    Select and return a list of tracks from a time interval

    Standard time span - 7 days from the current time
    """

    session = create_connection(username)

    #Set the default 7 days time span if one of the ends is not set
    if to_date == None or from_date == None:
        to_date = datetime.now().replace(microsecond=0)
        from_date = (to_date - relativedelta(days=7)).replace(hour=0, minute=0, second= 0, microsecond=0)

    query = sqlalchemy.select(Track).where(Track.date > from_date, Track.date < to_date)

    result = session.execute(query)

    tracklist = []

    for track in result.fetchall():
        tracklist.append(track[0])

    return tracklist
        

def check_user_files(username: str):
    """
    Checking and creating user files if they do not exist
    """
    user_files_path = f".\\backup\\{username}"

    if not os.path.exists(user_files_path):
        os.mkdir(user_files_path)
    
    if (not os.path.exists(user_files_path + "\\downloaded_tracks_intervals") or 
        not os.path.exists(user_files_path + f"\\{username}.db")):

        open(user_files_path + "\\downloaded_tracks_intervals", "w")
        open(user_files_path + f"\\{username}.db", "w")
