import os
import sys
import random

from flask import Flask, jsonify, request
from flask.ext.sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = 'sqlite:///%s/sample.db' % os.path.dirname(os.path.realpath(__file__))
app.config["SQLALCHEMY_ECHO"] = False
app.config["SECRET_KEY"] = os.urandom(24)
app.config["DEBUG"] = True
db = SQLAlchemy(app)


class Game(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    actual_word = db.Column(db.String(120))
    guessed_word = db.Column(db.String(120))
    tries_left = db.Column(db.Integer, default=11)
    status = db.Column(db.Enum('busy', 'success', 'fail'), default='busy')

    def __init__(self, word):
        self.actual_word = word

    def __repr__(self):
        return '%r' % self.id


def init_db():
    db.drop_all()
    db.create_all()
    db.session.commit()


def random_word():
    filename = os.path.dirname(os.path.realpath(__file__)) + '/words.english'
    max_line = file_len(filename)
    random_number = random.randrange(0, max_line)
    return get_line_n(filename, random_number)


def get_line_n(filename, n):
    word = None
    with open(filename) as fp:
        for i, line in enumerate(fp):
            if i == n:
                # line n
                word = line
            elif i > n:
                # reading further lines is not needed
                break
    return word.strip()


def file_len(fname):
    i = -1
    with open(fname) as f:
        for i, l in enumerate(f):
            pass
    return i + 1



def error_response(message, code):
    resp = jsonify(error=message)
    resp.status_code = code
    return resp


@app.errorhandler(404)
def page_not_found(e):
    return error_response('path is invalid', 404)


@app.route('/games/<id>', methods=['GET', 'POST'])
@app.route('/games', methods=['GET', 'POST'])
def games(id=None):
    if id:
        if request.method == 'POST':
            guessed_char = request.form["char"]
            if guessed_char < 'a' or guessed_char > 'z':
                return error_response('invalid char.', 400)
            game = Game.query.filter(Game.id == id).first()
            if game.status == 'busy':
                chars = list(game.guessed_word)
                hit = False
                for i, c in enumerate(game.actual_word):
                    if guessed_char == c:
                        chars[i] = guessed_char
                        hit = True

                if hit:
                    game.guessed_word = ''.join(chars)
                    #if there is no (.), then game is a success
                    if game.guessed_word.count('.') == 0:
                        game.status = 'success'
                    db.session.commit()
                    return jsonify(status='hit')
                else:
                    game.tries_left -= 1
                    #if there is not any tries left, the game will fail
                    if game.tries_left < 1:
                        game.status = 'fail'
                    db.session.commit()
                    return jsonify(status='no hit')
            else:
                return jsonify(status="failure: game has ended")

        else:
            game = Game.query.filter(Game.id == id).first()
            if game:
                game_dict = {
                    "status": game.status,
                    "word": game.guessed_word,
                    "tries_left": game.tries_left
                }
                return jsonify(game_dict)
            else:
                return error_response('game is not found.', 404)
    else:
        if request.method == 'POST':
            #for testing purpose creates game with a chosen word
            if app.config['TESTING'] and 'word' in request.form:
                word = request.form['word']
            else:
                word = random_word()
            new_game = Game(word)
            new_game.guessed_word = '.' * len(new_game.actual_word)
            db.session.add(new_game)
            db.session.commit()
            return jsonify(created='success', id=new_game.id)
        else:
            games_obj = Game.query.limit(5)
            games_dict = dict()
            for game in games_obj:
                games_dict[game.id] = {
                    "id": game.id,
                    "status": game.status
                }
            return jsonify(status='ok', games=games_dict)

if __name__ == '__main__':
    if len(sys.argv) > 2:
        print("Too much arguments")
    elif len(sys.argv) < 2:
        print("You must choose a command. "
              "init_db and runserver are available commands ")
    elif sys.argv[1] == 'init_db':
        init_db()
    elif sys.argv[1] == 'runserver':
        app.run(host='0.0.0.0')
    else:
        print("Invalid command. "
              "init_db and runserver are available commands ")
