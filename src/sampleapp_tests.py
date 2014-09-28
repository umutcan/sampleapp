import os
import sampleapp
import unittest
import tempfile
import json


class SampleAppTestCase(unittest.TestCase):
    def setUp(self):
        self.db_fd, sampleapp.app.config['DATABASE'] = tempfile.mkstemp()
        sampleapp.app.config['TESTING'] = True
        self.app = sampleapp.app.test_client()
        sampleapp.init_db()

    def tearDown(self):
        os.close(self.db_fd)
        os.unlink(sampleapp.app.config['DATABASE'])

    def test_start_game(self):
        rv = self.app.post('/games')
        assert 200 == rv.status_code
        json_response = json.loads(rv.data)
        assert 'success' in json_response['created']

    def test_game_overview(self):
        rv = self.app.get('/games')
        assert 200 == rv.status_code
        json_response = json.loads(rv.data)
        assert 'games' in json_response

    def test_game_status(self):
        rv = self.app.post('/games')
        assert 200 == rv.status_code
        json_response = json.loads(rv.data)
        assert 'success' in json_response['created']
        assert 'id' in json_response
        id = json_response['id']
        rv = self.app.get('/games/%s' % id)
        assert 200 == rv.status_code

        json_response = json.loads(rv.data)
        assert 'status' in json_response
        assert 'tries_left' in json_response
        assert 'word' in json_response

    def test_game_guess(self):
        rv = self.app.post('/games')
        assert 200 == rv.status_code
        json_response = json.loads(rv.data)
        assert 'success' in json_response['created']
        assert 'id' in json_response
        id = json_response['id']
        rv = self.app.post('/games/%s' % id, data=dict(char='a'))
        assert 200 == rv.status_code
        json_response = json.loads(rv.data)
        assert 'status' in json_response

    def test_game_success(self):
        rv = self.app.post('/games', data=dict(word='hangman'))
        assert 200 == rv.status_code
        json_response = json.loads(rv.data)
        assert 'success' in json_response['created']
        assert 'id' in json_response
        id = json_response['id']

        # guess a
        rv = self.app.post('/games/%s' % id, data=dict(char='a'))
        assert 200 == rv.status_code
        json_response = json.loads(rv.data)
        assert 'status' in json_response
        assert 'hit' == json_response['status']
        rv = self.app.get('/games/%s' % id)
        assert 200 == rv.status_code
        json_response = json.loads(rv.data)
        assert 'status' in json_response
        assert 'busy' == json_response['status']
        assert 'word' in json_response
        assert '.a...a.' == json_response['word']

        #guess h
        rv = self.app.post('/games/%s' % id, data=dict(char='h'))
        assert 200 == rv.status_code
        json_response = json.loads(rv.data)
        assert 'status' in json_response
        assert 'hit' == json_response['status']
        rv = self.app.get('/games/%s' % id)
        assert 200 == rv.status_code
        json_response = json.loads(rv.data)
        assert 'status' in json_response
        assert 'busy' == json_response['status']
        assert 'word' in json_response
        assert 'ha...a.' == json_response['word']

        #guess n
        rv = self.app.post('/games/%s' % id, data=dict(char='n'))
        assert 200 == rv.status_code
        json_response = json.loads(rv.data)
        assert 'status' in json_response
        assert 'hit' == json_response['status']
        rv = self.app.get('/games/%s' % id)
        assert 200 == rv.status_code
        json_response = json.loads(rv.data)
        assert 'status' in json_response
        assert 'busy' == json_response['status']
        assert 'word' in json_response
        assert 'han..an' == json_response['word']

        #guess g
        rv = self.app.post('/games/%s' % id, data=dict(char='g'))
        assert 200 == rv.status_code
        json_response = json.loads(rv.data)
        assert 'status' in json_response
        assert 'hit' == json_response['status']
        rv = self.app.get('/games/%s' % id)
        assert 200 == rv.status_code
        json_response = json.loads(rv.data)
        assert 'status' in json_response
        assert 'busy' == json_response['status']
        assert 'word' in json_response
        assert 'hang.an' == json_response['word']

        #guess m
        rv = self.app.post('/games/%s' % id, data=dict(char='m'))
        assert 200 == rv.status_code
        json_response = json.loads(rv.data)
        assert 'status' in json_response
        assert 'hit' == json_response['status']
        rv = self.app.get('/games/%s' % id)
        assert 200 == rv.status_code
        json_response = json.loads(rv.data)
        assert 'status' in json_response
        assert 'success' == json_response['status']
        assert 'word' in json_response
        assert 'hangman' == json_response['word']

    def test_game_fail(self):
        rv = self.app.post('/games', data=dict(word='hangman'))
        assert 200 == rv.status_code
        json_response = json.loads(rv.data)
        assert 'success' in json_response['created']
        assert 'id' in json_response
        id = json_response['id']

        # guess a
        rv = self.app.post('/games/%s' % id, data=dict(char='a'))
        assert 200 == rv.status_code
        json_response = json.loads(rv.data)
        assert 'status' in json_response
        assert 'hit' == json_response['status']
        rv = self.app.get('/games/%s' % id)
        assert 200 == rv.status_code
        json_response = json.loads(rv.data)
        assert 'status' in json_response
        assert 'busy' == json_response['status']
        assert 'word' in json_response
        assert '.a...a.' == json_response['word']
        guess_chars = list('ilkfszxcqwertyub')
        for i in range(1, 14):
            rv = self.app.post('/games/%s' % id, data=dict(char=guess_chars[i]))
            assert 200 == rv.status_code
            json_response = json.loads(rv.data)
            assert 'status' in json_response
            if 11 - i < 0:
                assert 'failure' in json_response['status']
                rv = self.app.get('/games/%s' % id)
                assert 200 == rv.status_code
                json_response = json.loads(rv.data)
                assert 'status' in json_response
                assert 'fail' == json_response['status']
                assert 'word' in json_response
                assert '.a...a.' == json_response['word']
            else:
                assert 'no hit' == json_response['status']
                rv = self.app.get('/games/%s' % id)
                assert 200 == rv.status_code
                json_response = json.loads(rv.data)
                assert 'status' in json_response
                if 11 - i == 0:
                    assert 'fail' == json_response['status']
                else:
                    assert 'busy' == json_response['status']
                assert 'word' in json_response
                assert '.a...a.' == json_response['word']

    def test_invalid_chars(self):
        rv = self.app.post('/games')
        assert 200 == rv.status_code
        json_response = json.loads(rv.data)
        assert 'success' in json_response['created']
        assert 'id' in json_response
        id = json_response['id']
        # guess invalid chars
        guess_chars = 'A,?.\n\tD'
        for i, c in enumerate(guess_chars):
            rv = self.app.post('/games/%s' % id, data=dict(char=c))
            assert 400 == rv.status_code
            json_response = json.loads(rv.data)
            assert 'error' in json_response
            assert 'invalid char.' == json_response['error']

    def test_not_found(self):
        # creates an empty db
        sampleapp.init_db()

        # create a game
        rv = self.app.post('/games')
        assert 200 == rv.status_code
        json_response = json.loads(rv.data)
        assert 'success' in json_response['created']
        assert 'id' in json_response

        # id is set to a non existent number
        id = int(json_response['id']) + 1
        rv = self.app.get('/games/%s' % str(id))
        assert 404 == rv.status_code
        json_response = json.loads(rv.data)
        assert 'error' in json_response
        assert 'game is not found.' == json_response['error']

if __name__ == '__main__':
    unittest.main()