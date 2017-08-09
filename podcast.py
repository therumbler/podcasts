#!/usr/local/bin/python3
import xml.etree.ElementTree as ET
from datetime import datetime
from email.utils import parsedate_to_datetime
import json
import re
import os
try:
    # Python 3
    import urllib.request as request
except ImportError as e:
    # Python 2
    import urllib2 as request

class Podcast():
    def __init__(self):
        self.namespaces = {
            'itunes': 'http://www.itunes.com/dtds/podcast-1.0.dtd',
        }

    def process_feed_url(self, feed_url):
        json_feed = self.rss_to_json_feed(feed_url)
        slug = self.add_to_cache(json_feed, feed_url)
        return slug

    def process_slug(self, slug):
        feed_url = self.get_from_cache(slug)
        json_feed = self.rss_to_json_feed(feed_url)
        return json_feed


    def get_from_cache(self, slug):
        with open('etc/{}.json'.format(slug)) as f:
            obj = json.load(f)

        feed_url = obj['url']
        return feed_url

    def add_to_cache(self, json_feed, feed_url):
        new_slug = slug = self.slugify(json_feed['title'])
        print (json_feed['home_page_url'])

        filepath = 'etc/{}.json'.format(slug)

        try:
            obj = {}
            with open(filepath) as f:
                obj = json.load(f)

            exists = True
            if feed_url == obj['url']:
                # Already added
                return slug
            else:
                # needs to be added
                pass
        except IOError as e:
            exists = False
        
        exists = os.path.isfile(filepath)
        counter = 1
        while exists:
            new_slug = '{}-{}'.format(slug, counter)
            filepath = 'etc/{}.json'.format(new_slug)

            exists = os.path.isfile(filepath)
            if not exists:
                break
            counter += 1

            if counter > 100:
                raise Exception("Can't create file for {}".format(slug))

        if exists:
            pass
        else:
            try:
                os.makedirs('etc')
            except OSError as e:
                # file exists
                pass
            with open(filepath, "w") as f:
                data = {
                    'url': feed_url
                }
                f.write(json.dumps(data, indent = 2))

        return new_slug
    @staticmethod
    def slugify(text):
        text = text.lower()
        # (pattern, substitute)
        patterns = [
            (r'\s+', '-'),   # replace spaces with -
            (r'[^\w\-]+', ''),   # remove all non-word chars
            (r'\-\-+', '-'),   # multiple - with single -
            (r'^-+', ''),    # trim - from beginning
            (r'-+$', ''),    # trim - from end
        ]

        for p in patterns:
            text = re.sub(p[0], p[1], text)

        return text

    def rss_to_json_feed(self, feed_url):
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.115 Safari/537.36',
        }

        r = request.Request(feed_url, headers = headers)
        response = request.urlopen(r)

        try:
            root = ET.fromstring(response.read())
        except ET.ParseError as e:
            response = request.urlopen(r)
            return json.load(response)
        channel = root.find('.//channel')
        try:
            icon = channel.find('.//image/url').text
        except AttributeError as e:
            icon = ""
        json_feed = {
            'version': 'https://jsonfeed.org/version/1',
            'title': channel.find('.//title').text,
            'home_page_url': channel.find('.//link').text,
            'description': channel.find('.//description').text,
            'icon': icon,
            'feed_url': '',
            'items': [],
        }

        xml_items = channel.findall('.//item')
        for xml_item in xml_items:
            item = self.rss_to_json_feed_item(xml_item)
            json_feed['items'].append(item)

        return json_feed

    def rss_to_json_feed_item(self, xml_item):
        date_published_string = xml_item.find('pubDate').text.strip()

        print('type = {}'.format(type(date_published_string)))
        formats = [
            '%a, %d %b %Y %H:%M %Z',
            '%a, %d %b %Y %H:%M:%S %Z',
            '%a, %d %b %Y %H:%M:%S +0000',
            '%a, %d %b %Y %H:%M:%S %z',
        ]
        date_published = parsedate_to_datetime(date_published_string)
        if not date_published:
            for fmt in formats:
                try:
                    date_published = datetime.strptime(date_published_string, fmt)
                    break
                except ValueError as e:
                    pass

        if not date_published:
            raise ValueError('none of the formats matched "{}"'.format(date_published_string)) 
        time_string  = xml_item.find('itunes:duration', self.namespaces).text

        duration_in_seconds = self._get_seconds(time_string)

        try:
            url = xml_item.find('link').text
        except AttributeError as e:
            url = ""

        try:
            content_text = xml_item.find('description').text
        except AttributeError as e:
            content_text = xml_item.find('itunes:summary', self.namespaces).text

        try:
            tags = xml_item.find('itunes:keywords', self.namespaces).text.split(', ')
        except AttributeError as e:
            tags = ""

        try:
            author_name = xml_item.find('itunes:author', self.namespaces).text
        except AttributeError as e:
            author_name = None
            
        try:
            image =  xml_item.find('itunes:image', self.namespaces).get('href'),
        except AttributeError as e:
            image = None
        json_item = {
            'id': xml_item.find('guid').text,
            'url': url,
            'title': xml_item.find('title').text,
            'content_text': content_text,
            'image': image,
            'date_published': date_published.isoformat(),
            'tags': tags,
            'author': {
                'name': author_name,
            },
            'attachments': [{
                'url': xml_item.find('.//enclosure').get('url'),
                'mime_type': xml_item.find('.//enclosure').get('type'),   
                'duration_in_seconds': duration_in_seconds,
                'size_in_bytes': xml_item.find('.//enclosure').get('length'),
            }],
        }
        return json_item

    @staticmethod
    def _get_seconds(time_string):
        if ":" not in time_string:
            return int(time_string)
        try:
            h, m, s = time_string.split(':')
        except ValueError as e:
            h = 0
            m, s = time_string.split(':')
        return int(h) * 3600 + int(m) * 60 + int(s)

    @staticmethod
    def get_filepath(item):
        date_published = item['date_published']

        args = {
        }
        #filepath = '{year}/{month}/{date}/{filename}'.format(year = )
        
    def download(self, json_feed):
        for item in json_feed['items']:
            filepath = self.get_filepath(item)

def main():
    feed_url = 'https://www.residentadvisor.net/xml/podcast.xml'
    feed_url = 'http://portal-api.thisisdistorted.com/xml/claude-vonstroke-presents-the-birdhouse'
    feed_url = 'https://www.relay.fm/connected/feed'
    p = Podcast(feed_url)

if __name__ == "__main__":
    main()

