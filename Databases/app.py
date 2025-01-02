from flask import Flask, send_from_directory
from flask_swagger_ui import get_swaggerui_blueprint

# Import blueprints
from routes.user_routes import user_bp
from routes.message_routes import message_bp
from routes.event_tag_routes import event_tag_bp
from routes.event_routes import event_bp
from routes.group_routes import group_bp
from routes.membership_routes import membership_bp

app = Flask(__name__)


# -----------------------------------------------------------------------------
# Swagger UI Setup
# -----------------------------------------------------------------------------
SWAGGER_URL = '/docs'
SWAGGER_API_SPEC_PATH = '/static/swagger.yaml'

swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL, 
    SWAGGER_API_SPEC_PATH,
    config={'app_name': "Event Management API"}
)

app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)

@app.route('/static/swagger.yaml')
def send_swagger_yaml():
    return send_from_directory('static', 'swagger.yaml')

# -----------------------------------------------------------------------------
# Register Blueprints
# -----------------------------------------------------------------------------
app.register_blueprint(user_bp, url_prefix='/users')
app.register_blueprint(message_bp, url_prefix='/messages')
app.register_blueprint(event_tag_bp, url_prefix='/event_tags')
app.register_blueprint(event_bp, url_prefix='/events')
app.register_blueprint(group_bp, url_prefix='/groups')
app.register_blueprint(membership_bp, url_prefix='/membership')

# -----------------------------------------------------------------------------
# Run Application
# -----------------------------------------------------------------------------
if __name__ == '__main__':
    app.run(debug=True)
     