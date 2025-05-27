import requests
import base64
import json
import time
import sys
import traceback

# DataForSEO API credentials - Replace with your actual credentials
username = "luke.taylor@l1.com"
password = "99829fe63ceb45d9"

# Function to encode credentials for basic auth
def get_auth_header():
    credentials = f"{username}:{password}"
    encoded_credentials = base64.b64encode(credentials.encode('utf-8')).decode('utf-8')
    return {"Authorization": f"Basic {encoded_credentials}"}

# Make API request and get response
def make_api_request(endpoint, payload):
    url = f"https://api.dataforseo.com/v3/{endpoint}"
    try:
        response = requests.post(url, json=payload, headers=get_auth_header())
        return response.json()
    except Exception as e:
        return {"error": str(e), "traceback": traceback.format_exc()}

# Safe accessor function to handle None values and potential NoneType errors
def safe_access(data, *keys, default=None):
    """Safely access nested dictionary keys without raising KeyError or TypeError."""
    try:
        for key in keys:
            if data is None:
                print(f"WARNING: Attempted to access key '{key}' on None value")
                return default
            if isinstance(key, int) and isinstance(data, list):
                if key < len(data):
                    data = data[key]
                else:
                    print(f"WARNING: Index {key} out of range for list of length {len(data)}")
                    return default
            elif isinstance(data, dict) and key in data:
                data = data[key]
            else:
                print(f"WARNING: Key '{key}' not found in data structure")
                return default
        return data
    except Exception as e:
        print(f"ERROR in safe_access: {str(e)}")
        return default

# Test the exact parameters used in your analyze_title function call
def test_analyze_title():
    # Parameters from your original request
    params = {
        "query": "sweepstakes casinos",
        "user_title": "💵Top Cash App Casinos | Best US Deposit Sites in 2025",
        "user_domain": "www.casino.org",
        "device": "desktop",
        "max_results": 50
    }
    
    print("Testing title analysis with parameters:")
    print(json.dumps(params, indent=2))
    
    # We'll try a few different API endpoints that might be related to title analysis
    endpoints = [
        "on_page/title_analysis",
        "serp/google/organic/live/advanced",
        "content_analysis/title_analysis"  # This might not exist, but worth trying
    ]
    
    for endpoint in endpoints:
        print(f"\nTrying endpoint: {endpoint}")
        
        # Convert the parameters to the format expected by the API
        if endpoint == "on_page/title_analysis":
            payload = [{
                "target": params.get("user_domain", "www.casino.org"),
                "title": params.get("user_title", ""),
                "keyword": params.get("query", "")
            }]
        elif endpoint == "serp/google/organic/live/advanced":
            payload = [{
                "keyword": params.get("query", ""),
                "location_name": "United States",
                "language_name": "English",
                "device": params.get("device", "desktop")
            }]
        else:
            payload = [{
                "title": params.get("user_title", ""),
                "keyword": params.get("query", ""),
                "target": params.get("user_domain", "www.casino.org")
            }]
        
        # Make the API request
        result = make_api_request(endpoint, payload)
        
        # Check the overall API response
        print(f"API Status Code: {result.get('status_code', 'N/A')}")
        print(f"API Status Message: {result.get('status_message', 'N/A')}")
        
        # Try to access tasks data safely
        tasks = safe_access(result, "tasks")
        
        if tasks:
            print(f"Number of tasks: {len(tasks)}")
            
            for i, task in enumerate(tasks):
                print(f"\nTask {i+1} status: {task.get('status_code', 'N/A')}")
                
                # Try to access result data safely
                task_result = safe_access(task, "result")
                
                if task_result:
                    if isinstance(task_result, list):
                        print(f"Result has {len(task_result)} items")
                        
                        # Try to access the first item safely
                        if len(task_result) > 0:
                            first_item = task_result[0]
                            print(f"First result item keys: {list(first_item.keys()) if isinstance(first_item, dict) else 'Not a dict'}")
                            
                            # If this is a SERP result, check the items
                            if endpoint == "serp/google/organic/live/advanced" and isinstance(first_item, dict):
                                items = safe_access(first_item, "items")
                                print(f"SERP items: {len(items) if items else 'None'}")
                    else:
                        print(f"Result is not a list, it's a {type(task_result)}")
                else:
                    print("No result data or result is None")
        else:
            print("No tasks data or tasks is None")
        
        print("-" * 50)

# Simulate the potential error scenario
def simulate_error_scenario():
    print("\nSimulating potential error scenario...")
    
    # Create a structure similar to what might be causing the NoneType error
    data = {
        "status_code": 20000,
        "tasks": [
            {
                "id": "123456",
                "status_code": 20000,
                "result": None  # This might be causing the error
            }
        ]
    }
    
    try:
        # Try to access something in the None result
        items = data["tasks"][0]["result"]["items"]  # This should cause NoneType is not subscriptable
        print(f"Items: {items}")
    except TypeError as e:
        print(f"Caught expected error: {str(e)}")
        print("This matches the error you're seeing: 'NoneType' object is not subscriptable")
        print("The error occurs when trying to access a property on a None value")

if __name__ == "__main__":
    # Test main functionality
    test_analyze_title()
    
    # Simulate the error scenario
    simulate_error_scenario()
    
    print("\nDebugging Tips:")
    print("1. Check if the API is returning result=None for your specific query")
    print("2. Verify your API credentials are correct")
    print("3. Try different parameters (without emoji, with spaces in keyword, etc.)")
    print("4. Check if the domain requires www. prefix")
    print("5. Check if there are rate limits or usage restrictions on your account")