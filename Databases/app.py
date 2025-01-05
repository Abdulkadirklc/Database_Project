# TODO
# grup kurunca membership tablosuna ekle yeni ilişkileri
# membership - kendini gruba admin olarak ekleyebiliyorsun
# internal server error'u düzgün printle
#






from flask import Flask, send_from_directory
from flask_swagger_ui import get_swaggerui_blueprint
import webbrowser
import os

# Import blueprints
from routes.user_routes import user_bp
from routes.message_routes import message_bp
from routes.event_tag_routes import event_tag_bp
from routes.event_routes import event_bp
from routes.group_routes import group_bp
from routes.membership_routes import membership_bp
from routes.tag_routes import tag_bp
from routes.event_attendance_routes import event_attendance_bp
from routes.feedback_routes import feedback_bp

app = Flask(__name__)

# -----------------------------------------------------------------------------
# Open Browser Automatically
# -----------------------------------------------------------------------------
def open_browser():
    if os.environ.get("WERKZEUG_RUN_MAIN") != "true":
        webbrowser.open_new('http://127.0.0.1:5000/docs')

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
app.register_blueprint(tag_bp, url_prefix='/tags')
app.register_blueprint(event_attendance_bp)
app.register_blueprint(feedback_bp, url_prefix='/feedback')

# -----------------------------------------------------------------------------
# Run Application
# -----------------------------------------------------------------------------
if __name__ == '__main__':
    open_browser()
    app.run(debug=True)
     