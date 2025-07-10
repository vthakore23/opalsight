"""OpalSight Application Entry Point"""
import os
from flask import jsonify
from app import create_app

# Create the application
app = create_app(os.environ.get('FLASK_ENV'))

# Add a simple health check endpoint
@app.route('/health')
def health():
    """Simple health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'opalsight-backend'
    })

if __name__ == '__main__':
    # Run the application
    app.run(
        host='0.0.0.0',
        port=int(os.environ.get('PORT', 8000)),
        debug=app.config['DEBUG']
    ) 