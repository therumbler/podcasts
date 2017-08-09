from flask import Flask, render_template, request, redirect, send_from_directory
import subprocess
import logging
import hmac
from configparser import ConfigParser
from podcast import Podcast

app = Flask(__name__)
    
def get_config():
    cp = ConfigParser()
    path = 'etc/config.conf'
    with open(path) as f:
        cp.readfp(f)

    config = {}
    for section in cp.sections():
        items = cp.items(section)
        config[section] =  {item[0]: item[1] for item in items}

    return config

@app.route("/")
def index():
    return send_from_directory("public", "index.html")

@app.route('/test')
def test():
    return 'TEST'

@app.route("/feeds")
def feed():
    if "url" in request.args:
        url = request.args['url']
        p = Podcast()
        slug = p.process_feed_url(url)
        return redirect('/feeds/{}'.format(slug))

@app.route("/feeds/<slug>")
def from_slug(slug):
    p = Podcast()
    json_feed = p.process_slug(slug)
    return render_template("podcast.html", **json_feed)

@app.route('/gitpull', methods = ['POST'])
def gitpull():
    config = get_config()
    
    key = str.encode(config['github']['secret'])
    msg = request.data
    signature = hmac.new(key, msg).hexdigest()
    request_signature = request.headers['X-Hub-Signature']

    cmd = ['bash', './gitpull.sh']
    subprocess.run(cmd)
    return 'pulled'

def main():
    app.run(debug = True, host='0.0.0.0')

if __name__ == '__main__':
    main()
