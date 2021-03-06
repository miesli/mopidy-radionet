from __future__ import unicode_literals

import logging
import re

from mopidy import backend
from mopidy.models import Album, Artist, Ref, SearchResult, Track

logger = logging.getLogger(__name__)


class RadioNetLibraryProvider(backend.LibraryProvider):
    root_directory = Ref.directory(uri='radionet:root', name='Radio.net')

    def __init__(self, backend):
        super().__init__(backend)

    def lookup(self, uri):

        if not uri.startswith('radionet:'):
            return None

        uri_parts = self.parse_uri(uri)

        if uri_parts[0] == 'station':
            identifier = int(uri_parts[1])
            radio_data = self.backend.radionet.get_station_by_id(identifier)

            artist = Artist(name=radio_data.name)

            album = Album(
                artists=[artist],
                name=radio_data.description + ' / ' + radio_data.continent +
                     ' / ' + radio_data.country + ' - ' + radio_data.city,
                uri='radionet:station:%s' % (identifier))

            track = Track(
                artists=[artist],
                album=album,
                name=radio_data.name,
                genre=radio_data.genres,
                comment=radio_data.description,
                uri=radio_data.stream_url)
            return [track]
        elif uri_parts[0] == 'station_play':
            radio_data = self.backend.radionet.get_station_by_name(uri_parts[1])

            artist = Artist(name=radio_data.name)

            album = Album(
                artists=[artist],
                name=radio_data.description + ' / ' + radio_data.continent +
                     ' / ' + radio_data.country + ' - ' + radio_data.city,
                uri='radionet:station:%s' % (uri_parts[1]))

            track = Track(
                artists=[artist],
                album=album,
                name=radio_data.name,
                genre=radio_data.genres,
                comment=radio_data.description,
                uri=radio_data.stream_url)
            return [track]

        return []

    def browse(self, uri):
        self.backend.refresh()

        directories = []
        tracks = []
        uri_parts = self.parse_uri(uri)
        if uri_parts[0] == 'root':
            if self.backend.radionet.local_stations:
                directories.append(
                    self.ref_directory(
                        "radionet:category:localstations", "Local stations")
                )
            if self.backend.radionet.top_stations:
                directories.append(
                    self.ref_directory(
                        "radionet:category:top100", "Top 100")
                )
            if self.backend.radionet.favorite_stations:
                directories.append(
                    self.ref_directory(
                        "radionet:category:favorites", "Favorites")
                )
            return directories
        elif uri_parts[0] == 'category' and uri_parts[1]:
            if uri_parts[1] == "localstations":
                for station in self.backend.radionet.local_stations:
                    tracks.append(self.station_to_ref(station))
            if uri_parts[1] == "top100":
                for station in self.backend.radionet.top_stations:
                    tracks.append(self.station_to_ref(station))
            if uri_parts[1] == "favorites":
                for station in self.backend.radionet.favorite_stations:
                    tracks.append(self.station_to_ref(station))
            tracks.sort(key=lambda ref: ref.name)
            return tracks
        else:
            logger.debug('Unknown URI: %s', uri)
            return []

    def search(self, query=None, uris=None, exact=False):

        result = []

        self.backend.radionet.do_search(' '.join(query['any']))

        for station in self.backend.radionet.search_results:
            result.append(self.station_to_track(station))

        return SearchResult(
            tracks=result
        )

    def station_to_ref(self, station):
        return Ref.track(
            uri='radionet:station:%s' % (station.id),
            name=station.name,
        )

    def station_to_track(self, station):
        ref = self.station_to_ref(station)
        return Track(uri=ref.uri, name=ref.name, album=Album(uri=ref.uri, name=ref.name),
                     artists=[Artist(uri=ref.uri, name=ref.name)])

    def ref_directory(self, uri, name):
        return Ref.directory(uri=uri, name=name)

    def parse_uri(self, uri):
        if not uri.startswith('radionet:'):
            return []

        uri = uri.replace('radionet:', '')
        return uri.split(':')
