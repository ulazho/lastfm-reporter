import requests
from decouple import config
from abc import abstractmethod
import inspect
from dataclasses import dataclass
from datetime import datetime
from ast import literal_eval
from time import sleep
from typing import Dict, Any


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

            #Get given parameters
            default_parameters = signature.parameters.keys() - {x for x in kwargs.keys()}
            call = {key: value for key, value in kwargs.items()}
            
            #Change from_date, to_date in from, to
            if call.get("from_date"): call["from"] = call.pop("from_date")
            if call.get("to_date"): call["to"] = call.pop("to_date")
            
            #Convert datetime to unix time
            if call.get("from"): call["from"] = int(call["from"].timestamp())
            if call.get("to"): call["to"] = int(call["to"].timestamp())

            #Get default parametes
            for parameter in default_parameters:
                call[parameter] = signature.parameters.get(parameter).default
            return self.process_api_call(**call).json()
        return wrapper
    
    def process_api_call(self, **kwargs) -> dict:
        "Performs an API call and returns a JSON file"

        kwargs['format'] = 'json'
        kwargs['api_key'] = self.API_KEY

        try:
            response = requests.get(self.BASE_URL, headers=self.headers, params= kwargs)

            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            raise SystemExit(e)
        finally: sleep(0.1)
        return response

@dataclass
class UserAPI(BaseAPIClient):

    @BaseAPIClient.api_call_decorator
    def getFriends(
            user:str,
            limit: int = 50,
            page: int = 1,
            method: str = "user.getFriends",
    ) -> dict:
        "Get a list of the user's friends on Last.fm."

        pass
        
    @BaseAPIClient.api_call_decorator
    def getInfo(
        user: str,
        method: str = "user.getInfo",
    ) -> dict:
        "Get information about a user profile."
        pass
    
    @BaseAPIClient.api_call_decorator
    def getLovedTracks(
        user: str,
        limit: int = 50,
        page: int = 1,
        method: str = "user.getLovedTracks"
    ) -> dict:
        "Get the last 50 tracks loved by a user."
        pass

    @BaseAPIClient.api_call_decorator
    def getRecentTracks(
        user: str,
        limit: int = 50,
        page: int = 1,
        extended: bool = False, 
        from_date: datetime = datetime(2001, 1, 1), #From the beginning
        to_date: datetime = datetime.now(), 
        method: str = "user.getRecentTracks"
    ) -> dict:
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
    ) -> dict:
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
    ) -> dict:
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
    ) -> dict:
        "Get the top tags used by this user."
        pass

    @BaseAPIClient.api_call_decorator
    def getTopTracks(
        user: str,
        period: str = "overall", # overall | 7day | 1month | 3month | 6month | 12month
        limit: int = 50,
        page: int = 1,
        method: str = "user.getTopTracks"
    ) -> dict:
        """
        Get the top tracks listened to by a user. 
        
        You can stipulate a time period. Sends the overall chart by default.
        """
        pass


