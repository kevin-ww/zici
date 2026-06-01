from flask import Flask

from legacy_flask.blueprints.words import words_bp
from legacy_flask.blueprints.progress import progress_bp
from legacy_flask.blueprints.review import review_bp

app = Flask(__name__)
app.register_blueprint(words_bp)
app.register_blueprint(progress_bp)
app.register_blueprint(review_bp)

if __name__ == "__main__":
    app.run(port=5000, debug=True)
