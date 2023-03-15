import time
import requests

from .api_endpoints import FilesEndpoint, FamiliesEndpoint, SharedRulesEndpoint
from .api_endpoints import FamiliesEndpoint


class Client(object):
    def __init__(self, base_url="https://app.fetchbim.com/api/", auth=None, retries=3, timeout=10):
        self.base_url = base_url
        self.auth = auth
        self.retries = retries
        self.timeout = timeout

        self.families = FamiliesEndpoint(self)
        self.files = FilesEndpoint(self)
        self.rules = SharedRulesEndpoint(self)
        
    def make_url(self, path):
        if not path:
            return self.base_url.rstrip("/")
        
        path = path.lstrip('/')
        return "{}/{}".format(self.base_url.rstrip("/"), path)
    
    def parse_response(self, response):
        try:
            response.raise_for_status()
            return response.json()
        except requests.exceptions.ConnectionError as e:
            if self.retries > 0:
                self.retries -= 1
                time.sleep(1)
                return self.request(response.url)
        except requests.exceptions.RequestException as e:
            raise Exception(e)
        
    def request(self, path=None, method='GET', params=None, data=None, headers=None):
        """
        Make a request to an endpoint
        """
        # If there is no token, raise an exception
        if not self.auth:
            raise Exception('No authentication token provided')

        # Build the URL for the request
        url = self.make_url(path)

        # Build the headers for the request
        request_headers = headers or {}
        request_headers["Content-Type"] = "application/json"
        if self.auth:
            request_headers['Authorization'] = 'Bearer {}'.format(self.auth)

        # Use the requests library to make the request
        response = requests.request(
            method=method,
            url=url,
            params=params,
            json=data,
            headers=request_headers,
            timeout=self.timeout
        )

        return self.parse_response(response)
        
        # # If the request was successful, return the response
        # if response.status_code == requests.codes.ok:
        #     return response.json()
        # # If the request was unsuccessful, raise an exception
        # else:
        #     raise Exception('[{}] Unable to make request to endpoint: "{}"'.format(response.status_code, url))


