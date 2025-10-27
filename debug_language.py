#!/usr/bin/env python3
"""
Debug script to test language switching functionality
"""

import requests
import json

def test_language_switch():
    url = "http://127.0.0.1:5000/api/language/switch"
    
    # Test with JSON data
    print("Testing with JSON data...")
    try:
        response = requests.post(url, json={'language': 'af'})
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error: {e}")
    
    print("\n" + "="*50 + "\n")
    
    # Test with form data
    print("Testing with form data...")
    try:
        response = requests.post(url, data={'language': 'af'})
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error: {e}")
    
    print("\n" + "="*50 + "\n")
    
    # Test get current language
    print("Testing get current language...")
    try:
        response = requests.get("http://127.0.0.1:5000/api/language/current")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_language_switch()