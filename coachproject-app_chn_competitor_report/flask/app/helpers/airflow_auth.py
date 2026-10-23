"""
Airflow Authentication Helper Module

This module handles Airflow JWT token management with proper caching and expiry handling.
"""

import json
import base64
import time
from datetime import datetime, timezone
from flask import current_app
import requests


def decode_jwt_payload(token):
    """
    Decode JWT token payload to extract expiry information.
    
    Args:
        token (str): JWT token string
        
    Returns:
        dict: Decoded payload or None if invalid
    """
    try:
        # JWT tokens have 3 parts separated by dots: header.payload.signature
        parts = token.split('.')
        if len(parts) != 3:
            return None
            
        # Decode the payload (second part)
        payload = parts[1]
        # Add padding if needed for base64 decoding
        payload += '=' * (4 - len(payload) % 4)
        decoded_bytes = base64.urlsafe_b64decode(payload)
        payload_dict = json.loads(decoded_bytes.decode('utf-8'))
        
        return payload_dict
    except Exception as e:
        current_app.logger.warning(f"Failed to decode JWT token: {str(e)}")
        return None


def is_token_expired(token, buffer_minutes=5):
    """
    Check if JWT token is expired or will expire within buffer time.
    
    Args:
        token (str): JWT token string
        buffer_minutes (int): Minutes before expiry to consider token as expired
        
    Returns:
        bool: True if token is expired or will expire soon
    """
    payload = decode_jwt_payload(token)
    if not payload:
        return True
        
    # Check for 'exp' (expiration) claim
    exp_timestamp = payload.get('exp')
    if not exp_timestamp:
        # If no expiry, assume token is valid for 1 hour (conservative approach)
        current_app.logger.warning("JWT token has no expiry claim, assuming 1-hour validity")
        return False
        
    # Convert to datetime and add buffer
    exp_datetime = datetime.fromtimestamp(exp_timestamp, tz=timezone.utc)
    current_time = datetime.now(timezone.utc)
    buffer_time = current_time.timestamp() + (buffer_minutes * 60)
    
    is_expired = exp_timestamp <= buffer_time
    
    if is_expired:
        current_app.logger.info(f"Airflow token expired or expires soon. Expiry: {exp_datetime}, Current: {current_time}")
    else:
        current_app.logger.debug(f"Airflow token is valid until: {exp_datetime}")
        
    return is_expired


def get_cached_airflow_token():
    """
    Get cached Airflow token if it exists and is still valid.
    
    Returns:
        str or None: Valid token or None if not cached/expired
    """
    try:
        cache = current_app.cache
        cached_token = cache.get("airflow_auth_token")
        
        if cached_token and not is_token_expired(cached_token):
            current_app.logger.debug("Using cached Airflow token")
            return cached_token
        elif cached_token:
            current_app.logger.info("Cached Airflow token is expired, will fetch new one")
            cache.delete("airflow_auth_token")
            
        return None
    except Exception as e:
        current_app.logger.warning(f"Error accessing cached token: {str(e)}")
        return None


def cache_airflow_token(token):
    """
    Cache Airflow token with appropriate TTL based on token expiry.
    
    Args:
        token (str): JWT token to cache
    """
    try:
        payload = decode_jwt_payload(token)
        if not payload:
            current_app.logger.warning("Cannot cache invalid token")
            return
            
        # Calculate TTL based on token expiry
        exp_timestamp = payload.get('exp')
        if exp_timestamp:
            current_time = int(time.time())
            ttl = max(0, exp_timestamp - current_time - 300)  # Cache until 5 minutes before expiry
        else:
            ttl = 3600  # Default 1 hour if no expiry info
            
        cache = current_app.cache
        cache.set("airflow_auth_token", token, timeout=ttl)
        
        exp_time = datetime.fromtimestamp(exp_timestamp, tz=timezone.utc) if exp_timestamp else "Unknown"
        current_app.logger.info(f"Cached Airflow token (TTL: {ttl}s, Expires: {exp_time})")
        
    except Exception as e:
        current_app.logger.warning(f"Failed to cache Airflow token: {str(e)}")


def get_airflow_auth_token(username, password, force_refresh=False):
    """
    Get Airflow authentication token with proper caching and expiry handling.
    
    Args:
        username (str): Airflow username
        password (str): Airflow password
        force_refresh (bool): If True, bypass cache and fetch fresh token
        
    Returns:
        str or None: Valid JWT token or None if authentication failed
    """
    # First try to get cached token (unless force refresh is requested)
    if not force_refresh:
        cached_token = get_cached_airflow_token()
        if cached_token:
            return cached_token
    
    # If no valid cached token or force refresh requested, fetch new one
    try:
        airflow_auth_url = current_app.config.get("AWS_AIRFLOW_AUTH_ENDPOINT")
        if not airflow_auth_url:
            current_app.logger.warning("Airflow auth URL not configured")
            return None
            
        current_app.logger.info("Fetching new Airflow auth token")
        
        # Prepare JSON payload for POST request (as per Airflow auth API spec)
        auth_payload = {
            "username": username,
            "password": password
        }
        headers = {"Content-Type": "application/json"}
        
        response = requests.post(airflow_auth_url, json=auth_payload, headers=headers, verify=False, timeout=20)
        
        if response.status_code in [200, 201]:  # Accept both 200 OK and 201 Created
            token_data = response.json()
            access_token = token_data.get("access_token")
            
            if access_token:
                # Cache the new token
                cache_airflow_token(access_token)
                current_app.logger.info(f"Successfully obtained and cached new Airflow token (status {response.status_code})")
                return access_token
            else:
                current_app.logger.error("No access_token in Airflow auth response")
                current_app.logger.debug(f"Full auth response: {token_data}")
                
        else:
            current_app.logger.error(f"Airflow auth failed with status {response.status_code}: {response.text}")
            # Log the request details for debugging
            current_app.logger.debug(f"Auth request URL: {airflow_auth_url}")
            current_app.logger.debug(f"Auth request payload: {auth_payload}")
            
    except Exception as e:
        current_app.logger.error(f"Exception during Airflow auth: {str(e)}")
        
    return None