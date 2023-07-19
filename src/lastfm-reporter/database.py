import sqlalchemy.orm as orm
import sqlalchemy
from sqlalchemy import exc
from datetime import datetime, timedelta
from dataclasses import dataclass
from APIClient import UserAPI
from dateutil.relativedelta import relativedelta
import time

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
        engine = sqlalchemy.create_engine(f"sqlite+pysqlite:///backup\{db_name}.db", echo=True)
        
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
        to_date = datetime.now()
    
    #Resetting the time clock, to get the whole day's tracks
    from_date = from_date.replace(hour=0, minute=0, second= 0)

    #print(f"From {from_date} to {to_date}")    

    #Getting the count of pages to call api 
    response = user.getRecentTracks(
        user= username, 
        limit= limit,
        from_date= from_date,
        to_date= to_date)
    total_pages = int(response["recenttracks"]["@attr"]["totalPages"])

    
    #Getting list of tracks
    tracklist = []
    for page in range(1, total_pages + 1):
        print(f"Tracklist size - {len(tracklist)}")
        response = user.getRecentTracks(
            user= username,
            limit= limit,
            page= page
        )

            
        tracklist +=  [track for track in response["recenttracks"]["track"] 
                       if track.get("@attr") or int(track["date"]["uts"]) >= from_date.timestamp()]
    return tracklist

def get_track_info(track: dict) -> Track:
    """
    Get all the necessary information about the track 
    """
    #If track playing now
    if track.get("@attr"):
        track["date"]["uts"] = datetime.now().timestamp
        
    #Track parameters
    track_info = Track(
        id= int(track["date"]["uts"]),
        name= track["name"],
        loved= False if track["loved"] == '0' else True,
        date= datetime.fromtimestamp(float(track["date"]["uts"])),
        url= track["url"]
    )
    return track_info


def upload_tracks(
        username: str,
        tracklist: list
) -> bool:
    """
    Loads the selected tracks into the database
    """

    session = create_connection(db_name= username)
    

    id = 0
    for track in tracklist:
        if(id == int(track["date"]["uts"])):
            continue
            
        
        session.merge(get_track_info(track))
        id = int(track["date"]["uts"])

    session.commit()

    session.close()
    


