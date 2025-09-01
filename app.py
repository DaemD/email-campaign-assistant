from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import sys
import json
import re

# Import the chatbot functions from b.py
sys.path.append('.')
from b import (
    session_state, 
    stage1_collect_info, 
    generate_json_via_llm, 
    generate_html_from_json,
    memory
)

app = Flask(__name__)
CORS(app)

# Serve static files
@app.route('/')
def index():
    with open('index.html', 'r', encoding='utf-8') as f:
        return f.read()

@app.route('/chat', methods=['POST'])
def chat_endpoint():
    try:
        data = request.get_json()
        user_message = data.get('message', '').strip()
        
        if not user_message:
            return jsonify({'error': 'No message provided'}), 400
        
        print(f"DEBUG: Received message: '{user_message}'")
        print(f"DEBUG: Current session state: {session_state}")
        
        
        bot_reply = stage1_collect_info(user_message)
        
        
        if session_state["campaign_info_complete"]:
            print("🎯 Campaign info complete! Generating JSON...")
            
            # Stage 2: Generate JSON
            summary = "\n".join([msg.content for msg in memory.chat_memory.messages])
            campaign_json = generate_json_via_llm(summary, session_state["products"])
            
            if campaign_json:
                print("✅ JSON generated successfully!")
                
                # Stage 3: Generate HTML with streaming
                print("🚀 Starting HTML generation...")
                html_email = generate_html_from_json(campaign_json)
                
                if html_email and not html_email.startswith("Error"):
                    return jsonify({
                        'reply': bot_reply,
                        'html_output': html_email,
                        'campaign_json': campaign_json,
                        'status': 'HTML email generated successfully'
                    })
                else:
                    return jsonify({
                        'reply': bot_reply,
                        'error': 'Failed to generate HTML',
                        'campaign_json': campaign_json,
                        'status': 'Error generating HTML'
                    })
            else:
                return jsonify({
                    'reply': bot_reply,
                    'error': 'Failed to generate campaign JSON',
                    'status': 'Error generating JSON'
                })
        
       
        return jsonify({
            'reply': bot_reply,
            'status': get_status_message()
        })
            
    except Exception as e:
        print(f"Error in chat endpoint: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

def get_status_message():
    """Get current status based on session state"""
    product_count = len(session_state.get('products', []))
    
    if product_count == 0:
        return 'Ready to start! Paste a product link to begin.'
    elif not session_state.get('campaign_info_complete'):
        return f'Collected {product_count} product(s). Continue providing campaign details.'
    else:
        return 'Campaign complete! Generating HTML email...'

@app.route('/reset', methods=['POST'])
def reset_session():
    """Reset the chatbot session"""
    global session_state, memory
    session_state = {
        "products": [],
        "campaign_info_complete": False,
        "campaign_json": None
    }
    memory.chat_memory.clear()
    return jsonify({'message': 'Session reset successfully'})

if __name__ == '__main__':
    print("🚀 Starting Email Campaign Bot Server...")
    print("📧 Open http://localhost:5000 in your browser")
    app.run(debug=True, host='0.0.0.0', port=5000)
