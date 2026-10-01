import os
from dotenv import load_dotenv
from flask import Flask, render_template, request
from database.db import init_db, close_db
from routes.main import main_bp
from routes.qr import qr_bp
from routes.print import print_bp

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-fallback-key')

app.register_blueprint(main_bp)
app.register_blueprint(qr_bp)
app.register_blueprint(print_bp)

app.teardown_appcontext(close_db)


# ---------------------------------------------------------------
# Context processor: exposes canonical base URL to all templates
# Used for Open Graph tags (which need absolute URLs)
# ---------------------------------------------------------------
@app.context_processor
def inject_canonical_url():
    base = os.environ.get('BASE_URL') or request.url_root.rstrip('/')
    return {'canonical_base_url': base}


# ---------------------------------------------------------------
# Custom 404 handler
# ---------------------------------------------------------------
@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404


# Initialize database
with app.app_context():
    init_db()

if __name__ == '__main__':
    host = os.environ.get('FLASK_HOST', '0.0.0.0')
    port = int(os.environ.get('FLASK_PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'
    app.run(debug=debug, host=host, port=port)