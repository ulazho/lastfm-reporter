import sqlalchemy.orm as orm
import sqlalchemy
from sqlalchemy import exc
from datetime import datetime, timedelta
from dataclasses import dataclass
from APIClient import UserAPI
from dateutil.relativedelta import relativedelta
import os
from intervals import Intervals
from ast import literal_eval
from typing import Dict, List, Tuple


SECONDS_IN_MONTHS = 2678400

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



def create_connection(db_name: str) -> orm.Session:
    """
    Create a database connection to a SQLite database and return a current Session
    """

    try:

        #Create dir if does not exist
        if not os.path.exists(f".\\backup\\{db_name}"):
            os.mkdir(f".\\backup\{db_name}")

        engine = sqlalchemy.create_engine(f"sqlite+pysqlite:///backup\{db_name}\{db_name}.db", echo=True)
        
        Session = sqlalchemy.orm.sessionmaker(bind=engine)
        Base.metadata.create_all(engine)
        session = Session()

        return session
        
    except exc.SQLAlchemyError as e:
        print(e)

def get_user_listened_tracks(
        username: str,
        period: str = "", # overall | 7day | 1month | 3month | 6month | 12month
        from_date: datetime = datetime(2001, 1, 1),
        to_date: datetime = datetime.now(),
        limit: int = 50
) -> list:
    """
    Get a list of tracks from a given time interval
    """
    user = UserAPI()
    LIST_OF_PERIODS = ["overall", "7day", "1month", "3month", "6month", "12month"]
    if period:
        if period not in LIST_OF_PERIODS: print("Incorrect period")
        elif period == "7day": from_date = datetime.now() - relativedelta(days=7)
        elif period == "1month": from_date = datetime.now() - relativedelta(months=1)
        elif period == "3month": from_date = datetime.now() - relativedelta(months=3)
        elif period == "6month": from_date = datetime.now() - relativedelta(months=6)
        elif period == "12month": from_date = datetime.now() - relativedelta(months=12)
        elif period == "overall": from_date = datetime(2001, 1, 1)
        to_date = datetime.now().replace(microsecond=0)
    
    #Resetting the time clock, to get the whole day's tracks
    from_date = from_date.replace(hour=0, minute=0, second= 0, microsecond=0)

    #Find the missing intervals 
    downloaded_internals = Intervals(get_user_downloaded_intervals(username))
    missing_intervals = downloaded_internals.complement((from_date.timestamp(), to_date.timestamp()))
    

    #Process each missing interval separately
    for interval in missing_intervals:

        from_date = datetime.fromtimestamp(interval[0])
        to_date = datetime.fromtimestamp(interval[1])

        #Select limit depending on the length of the interval
        limit = min(1000, max((to_date - from_date).total_seconds() / SECONDS_IN_MONTHS, 1) * 100)

        #print(f"From {from_date} to {to_date}")    

        #Getting the count of pages to call api 
        response = user.getRecentTracks(
            user= username, 
            limit= limit,
            from_date= from_date,
            to_date= to_date)
        total_pages = int(response["recenttracks"]["@attr"]["totalPages"])

        #Case of no tracks
        #if total_pages == 0: continue
        
        #Getting list of tracks
        tracklist = []
        for page in range(1, total_pages + 1):
            print(f"Tracklist size - {len(tracklist)}")
            response = user.getRecentTracks(
                user= username,
                limit= limit,
                page= page,
                from_date= from_date,
                to_date= to_date,
            )

            #Add tracks to tracklist and skip now playing track
            tracklist +=  [track for track in response["recenttracks"]["track"] 
                        if not track.get("@attr") and int(track["date"]["uts"]) >= from_date.timestamp()]
        
        #Update intervals
        update_user_downloaded_intervals(username, (from_date.timestamp(), to_date.timestamp()))
            

    return tracklist

def get_track_info(track: dict) -> Track:
    """
    Get all the necessary information about the track 
    """
        
    #Track parameters
    track_info = Track(
        id= int(track["date"]["uts"]),
        name= track["name"],
        loved= False if track["loved"] == '0' else True,
        date= datetime.fromtimestamp(float(track["date"]["uts"])),
        url= track["url"]
    )
    return track_info


def get_user_downloaded_intervals(username: str) -> List[Tuple]:
    """
    Get user downloaded intervals
    """
    intervals_file = open(f".\\backup\\{username}\\downloaded_tracks_intervals", "r+")

    intervals_list_str = intervals_file.readline()
    if intervals_list_str == "": intervals_list_str = "[]"
    
    intervals_list = literal_eval(intervals_list_str)

    return intervals_list

def update_user_downloaded_intervals(
        username: str,
        interval: Tuple
):
    """
    Create or update information about user downloaded tracks, using download intervals
    """
    intervals = Intervals(get_user_downloaded_intervals(username))

    intervals_file = open(f".\\backup\\{username}\\downloaded_tracks_intervals", "r+")

    #Get information about new interval
    from_date = int(interval[0])
    to_date = int(interval[1])

    #Add new interval and rewrite file
    intervals.add([(from_date, to_date)])
    intervals_file.seek(0)
    intervals_file.write(str(intervals))
    intervals_file.close()


def upload_tracks(
        username: str,
        tracklist: list
):
    """
    Loads the selected tracks into the database
    """

    session = create_connection(db_name= username)
    

    id = 0
    #Insert or replace tracks to database
    for track in tracklist:

        if(id == int(track["date"]["uts"])):
            continue
               
        session.merge(get_track_info(track))
        id = int(track["date"]["uts"])


    #Update user intervals
    from_date = int(tracklist[-1]["date"]["uts"])
    to_date = int(tracklist[0]["date"]["uts"])
    interval = (from_date, to_date)
    update_user_downloaded_intervals(username, interval)

    session.commit()

    session.close()
    


