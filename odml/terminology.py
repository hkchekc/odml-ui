"""
Handles (deferred) loading of terminology data and access to it
for odML documents
"""
from . import tools

try:
    from urllib.request import urlopen
except ImportError:
    from urllib import urlopen

import threading

import os
import tempfile
import datetime
from hashlib import md5

CACHE_AGE = datetime.timedelta(days=1)
def cache_load(url):
    """
    load the url and store it in a temporary cache directory
    subsequent requests for this url will use the cached version
    """
    filename = md5(url.encode('utf-8')).hexdigest() + '.' + os.path.basename(url)
    cache_dir = os.path.join(tempfile.gettempdir(), "odml.cache")
    if not os.path.exists(cache_dir):
        try:
            os.makedirs(cache_dir)
        except OSError: # might happen due to concurrency
            if not os.path.exists(cache_dir):
                raise
    cache_file = os.path.join(cache_dir, filename)
    if not os.path.exists(cache_file) \
        or datetime.datetime.fromtimestamp(os.path.getmtime(cache_file)) < datetime.datetime.now() - CACHE_AGE:
            try:
                data = urlopen(url).read() # read data first, so we don't have empty files on error
            except Exception as e:
                print("failed loading '%s': %s" % (url, e.message))
                return
            fp = open(cache_file, "w")
            fp.write(data.decode('utf-8'))
            fp.close()
    return open(cache_file)

class Terminologies(dict):
    loading = {}

    def load(self, url):
        """
        load and cache a terminology-url

        returns the odml-document for the url
        """
        if url in self:
            return self[url]

        if url in self.loading:
            self.loading[url].join()
            self.loading.pop(url, None)
            return self.load(url)

        return self._load(url)

    def _load(self, url):
        # TODO also cache the data locally on disk
        # if url.startswith("http"): return None
        fp = cache_load(url)
        if fp is None:
            print("did not successfully load '%s'" % url)
            return
        try:
            term = tools.xmlparser.XMLReader(filename=url, ignore_errors=True).fromFile(fp)
            term.finalize()
        except tools.xmlparser.ParserException as e:
            print("Failed to load %s due to parser errors" % url)
            print(' "%s"' % e.message)
            term = None
        self[url] = term
        return term

    def deferred_load(self, url):
        """
        start a thread to load the terminology in background
        """
        if url in self or url in self.loading: return
        self.loading[url] = threading.Thread(target=self._load, args=(url,))
        self.loading[url].start()

terminologies = Terminologies()
load = terminologies.load
deferred_load = terminologies.deferred_load
