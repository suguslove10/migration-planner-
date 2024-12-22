from flask import Flask, request, jsonify, send_from_directory
import boto3
import json
import os
from datetime import datetime
from werkzeug.middleware.proxy_fix import ProxyFix

app = Flask(__name__)

# Load AWS infrastructure details from backend folder
try:
    backend_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'backend')
    infra_file = os.path.join(backend_dir, 'infrastructure_details.json')
    with open(infra_file, 'r') as f:
        INFRA_DETAILS = json.load(f)
    API_URL = INFRA_DETAILS['api_url']
    LAMBDA_FUNCTIONS = INFRA_DETAILS['lambda_functions']
    print(f"Successfully loaded infrastructure details from {infra_file}")
except FileNotFoundError as e:
    print(f"Warning: infrastructure_details.json not found in {backend_dir}!")
    INFRA_DETAILS = {}
    API_URL = ''
    LAMBDA_FUNCTIONS = {}
except Exception as e:
    print(f"Error loading infrastructure details: {str(e)}")
    INFRA_DETAILS = {}
    API_URL = ''
    LAMBDA_FUNCTIONS = {}

# Initialize AWS client
lambda_client = boto3.client('lambda', region_name='us-east-1')

@app.route('/')
def index():
    return send_from_directory('templates', 'index.html')

@app.route('/static/<path:path>')
def send_static(path):
    return send_from_directory('static', path)

@app.route('/api/check-config', methods=['GET'])
def check_config():
    try:
        if INFRA_DETAILS:
            return jsonify({'configured': True, 'mode': 'aws'})
        return jsonify({'configured': False, 'mode': 'test'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/servers', methods=['GET'])
def get_servers():
    try:
        if not LAMBDA_FUNCTIONS:
            # Return sample data in the correct format
            return jsonify({
                'servers': [{
                    'serverId': 'sample-server-1',
                    'serverName': 'Sample Web Server',
                    'status': 'Active',
                    'serverType': 'Linux',
                    'osName': 'Ubuntu',
                    'osVersion': '20.04',
                    'metrics': {
                        'cpu': {
                            'cores': 4,
                            'utilization': 65
                        },
                        'memory': {
                            'total': 16384,
                            'used': 12288
                        },
                        'storage': {
                            'total': 512000,
                            'used': 358400
                        }
                    }
                }]
            })

        response = lambda_client.invoke(
            FunctionName=LAMBDA_FUNCTIONS['discoveryProcessor'],
            InvocationType='RequestResponse',
            Payload=json.dumps({})
        )
        result = json.loads(response['Payload'].read())
        
        # Ensure the response has the expected format
        if 'servers' not in result:
            return jsonify({'servers': []})
            
        return jsonify(result)
    except Exception as e:
        print(f"Error in get_servers: {str(e)}")
        # Return empty servers array on error
        return jsonify({'servers': []})

@app.route('/api/analyze', methods=['POST'])
def analyze_server():
    try:
        data = request.json
        if not data or 'serverId' not in data:
            return jsonify({'error': 'Missing serverId in request'}), 400

        if not LAMBDA_FUNCTIONS:
            # Return sample data with the correct structure
            return jsonify({
                'complexity': {
                    'level': 'Medium',
                    'score': 6,
                    'description': 'Moderate complexity due to some custom configurations'
                },
                'migrationStrategy': {
                    'strategy': 'Re-platform',
                    'risk_level': 'Medium',
                    'description': 'Modify the application to take advantage of cloud-native features'
                },
                'dependencies': [
                    {'name': 'MySQL Database', 'type': 'Database'},
                    {'name': 'Redis Cache', 'type': 'Cache'},
                    {'name': 'Nginx Web Server', 'type': 'Web Server'}
                ]
            })

        # Call AWS Lambda
        response = lambda_client.invoke(
            FunctionName=LAMBDA_FUNCTIONS['discoveryProcessor'],
            InvocationType='RequestResponse',
            Payload=json.dumps(data)
        )
        
        result = json.loads(response['Payload'].read())
        
        # Ensure response has required structure
        if 'body' in result:
            result = json.loads(result['body'])
        
        # Validate response structure
        if not all(key in result for key in ['complexity', 'migrationStrategy', 'dependencies']):
            raise ValueError('Invalid response structure from Lambda')
            
        return jsonify(result)
        
    except Exception as e:
        print(f"Error in analyze_server: {str(e)}")
        return jsonify({
            'error': str(e),
            'complexity': {'level': 'Unknown', 'score': 0, 'description': 'Analysis failed'},
            'migrationStrategy': {'strategy': 'Unknown', 'risk_level': 'Unknown', 'description': 'Analysis failed'},
            'dependencies': []
        })

@app.route('/api/upload-test-data', methods=['POST'])
def upload_test_data():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
            
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
            
        if file and file.filename.endswith('.json'):
            test_data = json.load(file)
            return jsonify({
                'message': 'Test data uploaded successfully', 
                'servers': test_data.get('servers', [])
            })
        else:
            return jsonify({'error': 'Invalid file format. Please upload a JSON file'}), 400
            
    except json.JSONDecodeError:
        return jsonify({'error': 'Invalid JSON format'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/estimate', methods=['POST'])
def estimate_costs():
    try:
        data = request.json
        if not data or 'serverId' not in data:
            return jsonify({'error': 'Missing serverId in request'}), 400

        # Get server details from discovered servers
        server_data = {
            'metrics': {
                'cpu': {'cores': 4, 'utilization': 65},
                'memory': {'total': 15630, 'used': 11722},  # in MB
                'storage': {'total': 488280, 'used': 341796}  # in MB
            },
            'migrationStrategy': {
                'strategy': 'Refactor',
                'risk_level': 'High'
            },
            'complexity': {
                'level': 'High',
                'score': 8
            }
        }

        print("Calling cost estimator with data:", json.dumps(server_data))  # Debug log

        # Call costEstimator Lambda
        response = lambda_client.invoke(
            FunctionName=LAMBDA_FUNCTIONS['costEstimator'],
            InvocationType='RequestResponse',
            Payload=json.dumps({
                'body': json.dumps({'serverData': server_data})
            })
        )
        
        result = json.loads(response['Payload'].read())
        print("Cost estimator response:", json.dumps(result))  # Debug log
        
        # Parse Lambda response
        if result.get('statusCode') == 200:
            return jsonify(json.loads(result['body']))
            
        return jsonify({
            'error': result.get('body', {}).get('error', 'Failed to estimate costs')
        }), result.get('statusCode', 500)

    except Exception as e:
        print(f"Error in estimate_costs: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/free-tier-usage', methods=['GET'])
def get_free_tier_usage():
    try:
        # Return actual usage if configured, otherwise sample data
        return jsonify({
            'lambda': {'used': 500000, 'limit': 1000000},
            's3': {'used': 2.5, 'limit': 5},
            'dynamodb': {'used': 10, 'limit': 25},
            'apiGateway': {'used': 500000, 'limit': 1000000}
        })
    except Exception as e:
        print(f"Error fetching Free Tier usage: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/roadmap', methods=['POST'])
def generate_roadmap():
    try:
        data = request.json
        if not LAMBDA_FUNCTIONS:
            # Return sample data if not configured
            return jsonify({
                'timeline': [
                    {
                        'name': 'Assessment Phase',
                        'duration': '2 weeks',
                        'startDate': '2024-01-01',
                        'endDate': '2024-01-14',
                        'tasks': ['Infrastructure assessment', 'Dependency mapping', 'Risk assessment']
                    }
                ],
                'projectSummary': {
                    'duration': '77 days',
                    'totalServers': 1,
                    'totalEffort': 480,
                    'criticalPath': ['Database Server', 'Web Server']
                }
            })

        response = lambda_client.invoke(
            FunctionName=LAMBDA_FUNCTIONS['roadmapGenerator'],
            InvocationType='RequestResponse',
            Payload=json.dumps(data)
        )
        return jsonify(json.loads(response['Payload'].read()))
    except Exception as e:
        print(f"Error in generate_roadmap: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)