import requests
from datetime import datetime, timezone
from flask import current_app, jsonify
from .airflow_auth import get_airflow_auth_token


def get_airflow_config():
    """Get Airflow configuration from app config."""
    return {
        'url': current_app.config.get("AWS_AIRFLOW_ENDPOINT"),
        'username': current_app.config.get("AWS_AIRFLOW_USERNAME"),
        'password': current_app.config.get("AWS_AIRFLOW_PASSWORD"),
        'auth_url': current_app.config.get("AWS_AIRFLOW_AUTH_ENDPOINT")
    }


def validate_airflow_config(config):
    """Validate required Airflow configuration."""
    if not config['url']:
        return "Could not start pipeline, url not defined!"
    if not config['username'] or not config['password']:
        return "Airflow credentials not configured!"
    return None


def create_airflow_payload(url):
    """Create payload based on Airflow version."""
    logical_date = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
    
    if "/api/v2/" in url:
        # Airflow 3.0+
        return {"logical_date": logical_date, "conf": {}}
    else:
        # Airflow 2.8
        return {"execution_date": logical_date, "conf": {}}


def make_airflow_api_call(url, payload, token, username, password):
    """Make Airflow API call with token auth, falling back to basic auth for legacy environments."""
    if token:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.post(url, json=payload, headers=headers, verify=False, timeout=20)
        
        # Retry with fresh token if expired
        if response.status_code in [401, 403]:
            current_app.logger.warning("Token expired, attempting to refresh...")
            current_app.cache.delete("airflow_auth_token")
            fresh_token = get_airflow_auth_token(username, password)
            
            if fresh_token:
                headers = {"Authorization": f"Bearer {fresh_token}"}
                response = requests.post(url, json=payload, headers=headers, verify=False, timeout=20)
                current_app.logger.info("Retried with fresh token")
            else:
                current_app.logger.warning("Token refresh failed, falling back to basic auth")
                response = requests.post(url, json=payload, auth=(username, password), verify=False, timeout=20)
        
        return response
    else:
        # Fallback to basic auth for legacy QA/PRD environments
        current_app.logger.warning("No token available, using basic auth (legacy mode)")
        return requests.post(url, json=payload, auth=(username, password), verify=False, timeout=20)


def handle_airflow_response(response):
    """Handle Airflow API response and return appropriate Flask response."""
    if response.status_code == 200:
        return jsonify({
            "message": "Pipeline started successfully",
            "response": response.json()
        }), 200
    else:
        current_app.logger.error(f"Airflow API failed: {response.status_code} - {response.text}")
        return jsonify({
            "error": "Failed to start pipeline",
            "status_code": response.status_code,
            "response": str(response.text)
        }), 500


def start_pipeline_workflow(config):
    """Execute the complete ETL pipeline start workflow."""
    # Validate configuration
    validation_error = validate_airflow_config(config)
    if validation_error:
        return jsonify({"message": validation_error}), 400

    # Try to get auth token (may be None for legacy environments using basic auth)
    auth_token = get_airflow_auth_token(config['username'], config['password'])
    if not auth_token:
        current_app.logger.warning("No auth token obtained, will use basic auth fallback")

    # Create payload and make API call
    payload = create_airflow_payload(config['url'])
    response = make_airflow_api_call(
        config['url'], 
        payload, 
        auth_token, 
        config['username'], 
        config['password']
    )

    # Handle response
    return handle_airflow_response(response)


def validate_status_request():
    """Validate and extract run_id from the request."""
    from flask import request, current_app
    
    # Debug logging
    current_app.logger.info(f"check_status called with content_type: {request.content_type}")
    current_app.logger.debug(f"Raw request data: {request.get_data()}")
    
    if not request.json:
        current_app.logger.warning("No JSON payload received")
        raise ValueError("No JSON payload provided")
        
    current_app.logger.debug(f"Parsed JSON: {request.json}")
    run_id = request.json.get('run_id')
    if not run_id:
        raise ValueError(f"Missing 'run_id' in request body. Received data: {request.json}")
        
    return run_id


def get_status_endpoint(run_id):
    """Construct the Airflow status endpoint URL."""
    from flask import current_app
    
    aws_airflow_url = current_app.config["AWS_AIRFLOW_ENDPOINT"]
    return f"{aws_airflow_url}/{run_id}"


def make_status_api_call(endpoint, run_id):
    """Make API call to check DAG run status with token retry logic."""
    import requests
    from datetime import datetime
    from flask import current_app
    from .airflow_auth import get_airflow_auth_token
    
    username = current_app.config["AWS_AIRFLOW_USERNAME"]
    password = current_app.config["AWS_AIRFLOW_PASSWORD"]
    
    # Try to get auth token first
    airflow_auth_token = get_airflow_auth_token(username, password)
    
    try:
        # Poll the Airflow API using token-based auth if available, otherwise basic auth
        if airflow_auth_token:
            headers = {"Authorization": f"Bearer {airflow_auth_token}"}
            response = requests.get(endpoint, headers=headers, verify=False, timeout=20)
            
            # If token expired during API call (401/403), try once more with fresh token
            if response.status_code in [401, 403]:
                current_app.logger.warning("Airflow status API returned 401/403, token may have expired. Retrying with fresh token...")
                current_app.cache.delete("airflow_auth_token")
                fresh_token = get_airflow_auth_token(username, password)
                
                if fresh_token:
                    headers = {"Authorization": f"Bearer {fresh_token}"}
                    response = requests.get(endpoint, headers=headers, verify=False, timeout=20)
                    current_app.logger.info("Retried Airflow status API call with fresh token")
                else:
                    current_app.logger.warning("Failed to obtain fresh token, falling back to basic auth")
                    response = requests.get(endpoint, auth=(username, password), verify=False, timeout=20)
        else:
            # Fallback to basic authentication
            response = requests.get(endpoint, auth=(username, password), verify=False, timeout=20)
            
        response.raise_for_status()
        return response
        
    except requests.exceptions.RequestException as e:
        current_app.logger.error(f"Status API request failed: {e}")
        raise


def parse_status_response(response, run_id):
    """Parse the Airflow API response and format the status information."""
    from datetime import datetime
    
    # Extract status and timestamp
    status = response.json().get('state', 'UNKNOWN')
    
    # Try to get Airflow's timestamp, fallback to now
    ts = response.json().get('end_date') or response.json().get('execution_date')
    if ts:
        # Airflow timestamps are usually ISO8601, e.g. '2023-10-06T12:34:56.789Z'
        try:
            dt = datetime.fromisoformat(ts.replace('Z', '+00:00'))
        except Exception:
            dt = datetime.utcnow()
    else:
        dt = datetime.utcnow()
        
    timestamp = dt.strftime('%Y-%m-%d %H:%M:%S UTC')
    
    # Compose a human-readable statement
    if status == 'success':
        statement = f"Run ID '{run_id}' was successful at {timestamp}."
    elif status == 'failed':
        statement = f"Run ID '{run_id}' failed at {timestamp}."
    elif status == 'running':
        statement = f"Run ID '{run_id}' is still running as of {timestamp}."
    else:
        statement = f"Run ID '{run_id}' is in state '{status}' as of {timestamp}."
        
    return {
        'run_id': run_id,
        'status': status,
        'timestamp': timestamp,
        'statement': statement
    }


def handle_status_api_error(run_id):
    """Handle API errors when checking status."""
    from datetime import datetime
    
    timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
    statement = f"Run ID '{run_id}' could not be checked due to API error at {timestamp}."
    
    return {
        'run_id': run_id,
        'status': 'API_ERROR',
        'timestamp': timestamp,
        'statement': statement
    }


def check_pipeline_status_workflow():
    """Orchestrate the complete status check workflow."""
    from flask import jsonify, current_app
    
    try:
        # Validate request and extract run_id
        run_id = validate_status_request()
        
        # Get endpoint and make API call
        endpoint = get_status_endpoint(run_id)
        
        try:
            response = make_status_api_call(endpoint, run_id)
            result = parse_status_response(response, run_id)
            return jsonify(result), 200
            
        except Exception as api_error:
            result = handle_status_api_error(run_id)
            return jsonify(result), 500
            
    except ValueError as ve:
        current_app.logger.error(f"Status request validation error: {ve}")
        return jsonify({
            "error": "Invalid request", 
            "message": str(ve)
        }), 400
        
    except Exception as e:
        current_app.logger.error(f"Status check workflow error: {e}")
        return jsonify({
            "error": "Status check failed", 
            "message": str(e)
        }), 500