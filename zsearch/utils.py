"""Utility functions for the zsearch."""
import pathlib
from typing import Union, Dict, List, Iterable

import requests

# error description from https://developers.zenodo.org/#http-status-codes
error_description = {200: "Request succeeded. Response included. Usually sent for GET/PUT/PATCH requests.",
                     201: "Request succeeded. Response included. Usually sent for POST requests.",
                     202: "Request succeeded. Response included. Usually sent for POST requests, where background "
                          "processing is needed to fulfill the request.",
                     204: "Request succeeded. No response included. Usually sent for DELETE requests.",
                     400: "Request failed. Error response included.",
                     401: "Request failed, due to an invalid access token. Error response included.",
                     403: "Request failed, due to missing authorization (e.g. deleting an already submitted upload or "
                          "missing scopes for your access token). Error response included.",
                     404: "Request failed, due to the resource not being found. Error response included.",
                     405: "Request failed, due to unsupported HTTP method. Error response included.",
                     409: "Request failed, due to the current state of the resource (e.g. edit a deposition which is "
                          "not fully integrated). Error response included.",
                     415: "Request failed, due to missing or invalid request header Content-Type. Error response "
                          "included.",
                     429: "Request failed, due to rate limiting. Error response included.",
                     500: "Request failed, due to an internal server error. Error response NOT included. Don’t worry, "
                          "Zenodo admins have been notified and will be dealing with the problem ASAP."
                     }

error_reason = {200: "OK",
                201: "Created",
                202: "Accepted",
                204: "No Content",
                400: "Bad Request",
                401: "Unauthorized",
                403: "Forbidden",
                404: "Not Found",
                405: "Method Not Allowed",
                409: "Conflict",
                415: "Unsupported Media Type",
                429: "Too Many Requests",
                500: "Internal Server Error"
                }


def explain_response(response: Union[int, requests.models.Response]) -> str:
    """Return the error description for a given error code."""
    if isinstance(response, requests.models.Response):
        return f'{response.status_code}: {response.reason}: {error_description[response.status_code]}'
    elif isinstance(response, int):
        return f'{response}: {error_reason[response]}: {error_description[response]}'
    raise TypeError(f"response must be of type int or requests.models.Response, not {type(response)}")


def download_file(bucket_dict: Dict, destination_dir: pathlib.Path = None, timeout: int = None) -> pathlib.Path:
    """Download the file from the bucket_dict to the destination directory which is here if 
    set to None"""
    if not isinstance(bucket_dict, Dict):
        raise TypeError('bucket_dict must be a dictionary, not a list. Call download_files instead.')
    if 'key' not in bucket_dict and 'bucket' in bucket_dict:
        raise ValueError(f'Input dictionary does not seem to be a bucket dictionary: {bucket_dict}')
    filename = bucket_dict['key']

    if destination_dir is not None:
        target_filename = destination_dir / filename
    else:
        target_filename = pathlib.Path(filename)

    if target_filename.exists():
        return target_filename

    # Get the record metadata
    response = requests.get(bucket_dict['links']['self'],
                            timeout=timeout)

    with open(target_filename, 'wb') as f:
        f.write(response.content)
    return target_filename


def download_files(file_buckets: Iterable[Dict],
                   destination_dir: pathlib.Path = None,
                   timeout: int = None) -> List[pathlib.Path]:
    """Download the files from the list of bucket dictionaries to the destination directory which is here if
    set to None"""
    return [download_file(bucket_dict, destination_dir, timeout) for bucket_dict in file_buckets]