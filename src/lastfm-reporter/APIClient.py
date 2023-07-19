import requests
from decouple import config
from abc import abstractmethod
import inspect
from dataclasses import dataclass
from datetime import datetime


@dataclass
class BaseAPIClient:
    API_KEY= config('API_KEY', default='')
    BASE_URL = 'https://ws.audioscrobbler.com/2.0/'
    USER_AGENT = 'Dataquest'
    headers = {'user-agent': USER_AGENT}


    def api_call_decorator(func):
        """
        Decoder for processing API calls: 
        fills missing parameters with default values and returns the result in JSON format
        """

        def wrapper(self, **kwargs):
            signature = inspect.signature(func)

            default_parameters = signature.parameters.keys() - {x for x in kwargs.keys()}
            call = {key: value for key, value in kwargs.items()}

            for parameter in default_parameters:
                call[parameter] = signature.parameters.get(parameter).default
            return self.process_api_call(**call).json()
        return wrapper
    
    def process_api_call(self, **kwargs):
        "Performs an API call and returns a JSON file"

        try:
            kwargs['format'] = 'json'
            kwargs['api_key'] = self.API_KEY
            response = requests.get(self.BASE_URL, headers=self.headers, params= kwargs )
        except requests.exceptions.RequestException as e:
            raise SystemExit(e)
        return response

@dataclass
class UserAPI(BaseAPIClient):

    @BaseAPIClient.api_call_decorator
    def getFriends(
            user:str,
            limit: int = 50,
            page: int = 1,
            method: str = "user.getFriends",
    ):
        "Get a list of the user's friends on Last.fm."

        pass
        
    @BaseAPIClient.api_call_decorator
    def getInfo(
        user: str,
        method: str = "user.getInfo",
    ):
        "Get information about a user profile."
        pass
    
    @BaseAPIClient.api_call_decorator
    def getLovedTracks(
        user: str,
        limit: int = 50,
        page: int = 1,
        method: str = "user.getLovedTracks"
    ):
        "Get the last 50 tracks loved by a user."
        pass

    @BaseAPIClient.api_call_decorator
    def getRecentTracks(
        user: str,
        limit: int = 50,
        page: int = 1,
        extended: bool = False,
        from_date: int = 0,
        to_date: int = datetime.now().timestamp(),
        method: str = "user.getRecentTracks"
    ):
        """
        Get a list of the recent tracks listened to by this user. 

        Also includes the currently playing track with the nowplaying="true" attribute 
        if the user is currently listening.
        """
        pass
    
    @BaseAPIClient.api_call_decorator
    def getTopAlbums(
        user: str,
        period: str = "overall", # overall | 7day | 1month | 3month | 6month | 12month
        limit: int = 50,
        page: int = 1,
        method: str = "user.getTopAlbums"
    ):
        """
        Get the top albums listened to by a user. 
        
        You can stipulate a time period. Sends the overall chart by default.
        """
        pass
    
    @BaseAPIClient.api_call_decorator
    def getTopArtists(
        user: str,
        period: str = "overall", # overall | 7day | 1month | 3month | 6month | 12month
        limit: int = 50,
        page: int = 1,
        method: str = "user.getTopArtists"
    ):
        """
        Get the top artists listened to by a user. 
        
        You can stipulate a time period. Sends the overall chart by default.
        """
        pass

    @BaseAPIClient.api_call_decorator
    def getTopTags(
        user: str,
        limit: int = 50,
        method: str = "user.getTopTags"
    ):
        "Get the top tags used by this user."
        pass

    @BaseAPIClient.api_call_decorator
    def getTopTracks(
        user: str,
        period: str = "overall", # overall | 7day | 1month | 3month | 6month | 12month
        limit: int = 50,
        page: int = 1,
        method: str = "user.getTopTracks"
    ):
        """
        Get the top tracks listened to by a user. 
        
        You can stipulate a time period. Sends the overall chart by default.
        """
        pass

