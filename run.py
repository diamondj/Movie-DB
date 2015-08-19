#!flask/bin/python
from app import app
app.secret_key = '$\x8ac\x96V\xdb\x00\x16<\xff\xb1\x06\xbb\\C\xda\xbd\xa1'
app.config['SESSION_TYPE'] = 'filesystem'
app.run(host="0.0.0.0", debug = True)
