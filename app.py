from flask import Flask, render_template, request, redirect, send_from_directory
from podcast import Podcast
app = Flask(__name__)

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

def main():
    app.run(debug = True, host='0.0.0.0')

if __name__ == '__main__':
    main()
