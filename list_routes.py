#!/usr/bin/env python3
"""
Simple script to list all registered Flask routes
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app

def list_all_routes():
    """List all registered Flask routes"""
    app = create_app()
    
    print("All registered Flask routes:")
    print("=" * 80)
    
    # Group routes by blueprint
    routes_by_blueprint = {}
    
    for rule in app.url_map.iter_rules():
        endpoint = rule.endpoint
        blueprint = endpoint.split('.')[0] if '.' in endpoint else 'main'
        
        if blueprint not in routes_by_blueprint:
            routes_by_blueprint[blueprint] = []
        
        routes_by_blueprint[blueprint].append({
            'endpoint': endpoint,
            'rule': rule.rule,
            'methods': sorted(rule.methods - {'HEAD', 'OPTIONS'})
        })
    
    # Sort and display
    for blueprint, routes in sorted(routes_by_blueprint.items()):
        print(f"\n📁 {blueprint.upper()} BLUEPRINT:")
        print("-" * 50)
        
        for route in sorted(routes, key=lambda x: x['rule']):
            methods_str = ','.join(route['methods'])
            print(f"  {route['endpoint']:<35} {route['rule']:<30} [{methods_str}]")
    
    print(f"\n{'='*80}")
    total_routes = sum(len(routes) for routes in routes_by_blueprint.values())
    print(f"Total routes: {total_routes}")
    
    return routes_by_blueprint

if __name__ == '__main__':
    list_all_routes()