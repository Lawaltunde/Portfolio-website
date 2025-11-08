from flask import render_template
from portfolio.app import create_app

app = create_app()

@app.errorhandler(404)
def not_found_error(error):
    return render_template('error404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    # In a real app, you'd want to log this error.
    return render_template('error500.html'), 500