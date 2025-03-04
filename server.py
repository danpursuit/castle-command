from flask import Flask, request, jsonify
from flask_cors import CORS
import socket
import uvicorn
from asgiref.wsgi import WsgiToAsgi

from castle.client_adapter import create_game_object
from castle.utils import pretty_list
from custom_agent.castle_agent import CastleAgent, get_model

app = Flask(__name__)
CORS(app, resources={r"/*": {
    "origins": "*",
    "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    "allow_headers": ["Content-Type", "Authorization"]
}})
model = None

# Helper function to get local IP address
def get_local_ip():
    try:
        # Create a socket that connects to an external server
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Doesn't actually connect, just sets up the socket
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"  # Fallback to localhost

# A simple status endpoint for debugging
@app.route('/api/status', methods=['GET'])
def get_status():
    print('getting status')
    response = jsonify({
        "status": "online",
        "message": "API server is running"
    })
    
    # Print the response headers for debugging
    print("\n--- DEBUG: Response Headers ---")
    print(f"Status: {response.status_code}")
    for header, value in response.headers.items():
        print(f"{header}: {value}")
    print("-----------------------------\n")
    
    return response

# POST submit command
@app.route('/api/command', methods=['POST'])
def submit_command():
    if not request.json or 'command' not in request.json or 'gameObjects' not in request.json:
        return jsonify({"error": "Invalid data"}), 400
    
    # load unsloth model just once
    global model
    if model is None:
        print('loading castle model first')
        model = get_model()
    else:
        print('found existing model')
    
    # print the data we received
    print('new command request:', request)
    game_objects_data = request.json['gameObjects']
    game_objects = [create_game_object(o) for o in game_objects_data]
    game_str = pretty_list(game_objects)
    print('got game_objects', game_str)
    
    # create the agent and fulfill request
    user_request = request.json['command']
    print(f'running command "{user_request}"')
    agent = CastleAgent(model)
    agent_answer = agent.run_battle_command(game_objects, user_request)

    response = {
        'command': user_request,
        'result': agent_answer
    }
    return jsonify(response), 200

# Convert Flask WSGI app to ASGI
asgi_app = WsgiToAsgi(app)

if __name__ == '__main__':
    local_ip = get_local_ip()
    port = 5000
    print(f"Server starting on http://{local_ip}:{port}")
    print(f"Local network access URL: http://{local_ip}:{port}")
    
    # Use uvicorn with auto-reload
    uvicorn.run(
        "server:asgi_app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info",
         # unsloth modifies a cache on startup
         # uvicorn restarts when detecting file change
         # below is necessary to prevent uvicorn from infinitely rebooting
        reload_excludes=["unsloth_compiled_cache/*"] 
    )