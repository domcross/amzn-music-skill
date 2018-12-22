import re
import pickle
import base64
# from mycroft import intent_file_handler
from mycroft.audio.services.vlc import VlcService
# mplayer stutters every 10sec when playin Amzn-Music's chunked mp3 streams
# from mycroft.audio.services.mplayer import MPlayerService
from mycroft.messagebus.message import Message
from mycroft.skills.common_play_skill import CommonPlaySkill, CPSMatchLevel
from mycroft.util.log import LOG
from mycroft.util.parse import match_one, fuzzy_match
from os import listdir, path  # makedirs, remove,
from os.path import dirname, join  # exists, expanduser, isfile, abspath, isdir
from .amazonmusic import AmazonMusic


class AmznMusicSkill(CommonPlaySkill):
    def __init__(self):
        super().__init__(name="AmznMusicSkill")
        # self.mediaplayer = MPlayerService(config=None, bus=None)
        self.mediaplayer = VlcService(config={'low_volume': 10, 'duck': True})
        self.state = 'idle'
        self.cps_id = "amzn-music"
        self.am = None
        self.vocabs = []  # keep a list of vocabulary words
        self.username = ""
        self.password = ""
        self.library_only = True

    def initialize(self):
        self.username = self.settings.get("username", "")
        self.password = self.settings.get("password", "")
        self.library_only = self.settings.get("library_only", True)
        # self._load_vocab_files()

        # handle credentials
        if (not self.username) and (not self.password):
            credentials = self._load_credentials_store()
            if credentials:
                self.username = base64.b64decode(credentials['e'])
                self.password = base64.b64decode(credentials['p'])

        if self.username and self.password:
            LOG.debug("login to amazon music")
            self.am = AmazonMusic(credentials=[self.username, self.password])
        self.mediaplayer.clear_list()
        # Setup handlers for playback control messages
        self.add_event('mycroft.audio.service.next', self.next)
        self.add_event('mycroft.audio.service.prev', self.previous)
        self.add_event('mycroft.audio.service.pause', self.pause)
        self.add_event('mycroft.audio.service.resume', self.resume)
        self.add_event('mycroft.audio.service.lower_volume', self.lower_volume)
        self.add_event('mycroft.audio.service.restore_volume',
                       self.restore_volume)
        self.add_event('recognizer_loop:audio_output_start', self.lower_volume)
        self.add_event('recognizer_loop:record_begin', self.lower_volume)
        self.add_event('recognizer_loop:audio_output_end', self.restore_volume)
        self.add_event('recognizer_loop:record_end', self.restore_volume)

        self.add_event('mycroft.audio.service.track_info', self._track_info_handler)
        self.add_event('mycroft.audio.playing_track', self._playing_track_handler)
        self.mediaplayer.set_track_start_callback(self._track_start_handler)

    def CPS_match_query_phrase(self, phrase):
        LOG.debug("phrase {} lib-only".format(phrase, self.library_only))
        # Not ready to play
        if not self.am:
            return None

        if 'amazon' in phrase.lower():
            bonus = 0.1
        else:
            bonus = 0

        #phrase = re.sub(self.translate('on_amazon_regex'), '', phrase)
        #LOG.debug("phrase {}".format(phrase))
        phrase = self._clean_utterance(phrase)
        LOG.debug("clean phrase {}".format(phrase))

        confidence, data = self.continue_playback(phrase, bonus)
        if not data:
            confidence, data = self.specific_query(phrase, bonus)
            if not data:
                confidence, data = self.generic_query(phrase, bonus)

        if data:
            if confidence > 0.9:
                confidence = CPSMatchLevel.EXACT
            elif confidence > 0.7:
                confidence = CPSMatchLevel.MULTI_KEY
            elif confidence > 0.5:
                confidence = CPSMatchLevel.TITLE
            else:
                confidence = CPSMatchLevel.CATEGORY
            return phrase, confidence, data

    def continue_playback(self, phrase, bonus=0.0):
        LOG.debug("phrase {}".format(phrase))
        if phrase.strip() == 'amazon':
            return (1.0,
                    {
                        'data': None,
                        'name': None,
                        'type': 'continue'
                    })
        else:
            return None, None

    def specific_query(self, phrase, bonus=0.0):
        LOG.debug("phrase {}".format(phrase))
        # Check if playlist
        match = re.match(self.translate('playlist_regex'), phrase)
        LOG.debug("match playlist {}".format(match))
        if match:
            bonus += 0.1
            playlist, conf, data = \
                self.get_best_playlist(match.groupdict()['playlist'])
            confidence = min(conf + bonus, 1.0)
            if not playlist:
                return 0, None
            return (confidence,
                    {
                        'asin': data['asin'],
                        'title': data['title'],
                        'name': playlist,
                        'type': 'Playlist'
                    })
        # Check album
        match = re.match(self.translate('album_regex'), phrase)
        LOG.debug("match album {}".format(phrase))
        if match:
            bonus += 0.1
            album = match.groupdict()['album']
            return self.query_album(album, bonus)
        # Check artist
        match = re.match(self.translate('artist_regex'), phrase)
        LOG.debug("match artist {}".format(phrase))
        if match:
            bonus += 0.1
            artist = match.groupdict()['artist']
            return self.query_artist(artist, bonus)
        # Check song/track
        match = re.match(self.translate('song_regex'), phrase)
        LOG.debug("match song {}".format(phrase))
        if match:
            bonus += 0.1
            track = match.groupdict()['track']
            return self.query_track(track, bonus)
        # Check genre
        match = re.match(self.translate('genre_regex'), phrase)
        LOG.debug("match genre {}".format(phrase))
        if match:
            bonus += 0.1
            genre = match.groupdict()['genre']
            return self.query_genre(genre, bonus)
        return None, None

    def generic_query(self, phrase, bonus=0.0):
        LOG.debug("phrase {}".format(phrase))

        playlist, conf, data = self.get_best_playlist(phrase)
        # playlist, conf, asin = self.get_best_playlist(phrase)
        if conf > 0.5:
            return (conf,
                    {
                        'asin': data['asin'],
                        'title': data['title'],
                        'artURL': data['artURL'],
                        'name': playlist,
                        'type': 'Playlist'
                    })

        else:
            return self.query_album(phrase, bonus)

    def query_genre(self, genre, bonus=0.0):
        LOG.debug("genre {}".format(genre))
        results = self.am.search(genre, library_only=self.library_only,
                                 tracks=True, albums=False, playlists=False,
                                 artists=False, stations=False)
        best_score = 0.0
        best_match = ""
        for res in results:
            if 'track' in res[0]:
                for hit in res[1]['hits']:
                    primaryGenre = hit['document']['primaryGenre']
                    score = fuzzy_match(genre.lower(), primaryGenre.lower())
                    if score > best_score:
                        best_match = primaryGenre
                        best_score = score
                    if (best_score + bonus) >= 1.0:
                        break
        if best_score > 0.0:
            conf = min(best_score + bonus, 1.0)
            return (conf,
                    {
                        'genre': best_match,
                        'name': genre,
                        'type': 'Genre'
                    })

    def query_track(self, trackname, bonus=0.0):
        LOG.debug("trackname {}".format(trackname))
        by_word = ' {} '.format(self.translate('by'))
        artist = ""
        if len(trackname.split(by_word)) > 1:
            trackname, artist = trackname.split(by_word)
            # trackname = '*{}* artist:{}'.format(trackname, artist)
            bonus += 0.1
        LOG.debug("trackname {} artist {}".format(trackname, artist))

        results = self.am.search(trackname, library_only=self.library_only,
                                 tracks=True, albums=False, playlists=False,
                                 artists=False, stations=False)

        tracks = {}
        for res in results:
            if 'track' in res[0]:
                for hit in res[1]['hits']:
                    title = hit['document']['title'].lower()
                    if artist:
                        title += (' ' + hit['document']['artistName'].lower())
                    asin = hit['document']['asin']
                    tracks[title] = {'asin': asin,
                                     'albumAsin': hit['document']['albumAsin'],
                                     'artist': hit['document']['artistName'],
                                     'title': hit['document']['title'],
                                     'artURL': hit['document']['artFull']['URL']}
        if tracks:
            match = trackname
            if artist:
                match += (' ' + artist)
            key, confidence = match_one(match.lower(),
                                        list(tracks.keys()))
            if confidence > 0.7:
                confidence = min(confidence + bonus, 1.0)
                return (confidence,
                        {
                            'asin': tracks[key]['asin'],
                            'albumAsin': tracks[key]['albumAsin'],
                            'name': key,
                            'artist': tracks[key]['artist'],
                            'title': tracks[key]['title'],
                            'artURL': tracks[key]['artURL'],
                            'type': 'Song'
                        })
        return None, None

    def query_artist(self, artist, bonus=0.0):
        results = self.am.search(artist, library_only=self.library_only,
                                 tracks=False, albums=False, playlists=False,
                                 artists=True, stations=False)

        artists = {}
        for res in results:
            if 'artists' in res[0]:
                for hit in res[1]['hits']:
                    name = hit['document']['name'].lower()
                    asin = hit['document']['asin']
                    artists[name] = {'asin': asin,
                                     'name': hit['document']['name'],
                                     'artURL': hit['document']['artFull']['URL']}
        if artists:
            key, confidence = match_one(artist.lower(),
                                        list(artists.keys()))
            if confidence > 0.7:
                confidence = min(confidence + bonus, 1.0)
                return (confidence,
                        {
                            'asin': artists[key]['asin'],
                            'name': key,
                            'artist': artists[key]['name'],
                            'type': 'Artist',
                            'artURL': artists[key]['artURL']
                        })
        return None, None

    def query_album(self, album, bonus=0.0):
        LOG.debug("album {}".format(album))
        by_word = ' {} '.format(self.translate('by'))
        artist = ""
        if len(album.split(by_word)) > 1:
            album, artist = album.split(by_word)
            bonus += 0.1
        LOG.debug("album {} artist {}".format(album, artist))

        results = self.am.search(album, library_only=self.library_only,
                                 tracks=False, albums=True, playlists=False,
                                 artists=False, stations=False)

        albums = {}
        for res in results:
            if 'album' in res[0]:
                for hit in res[1]['hits']:
                    title = hit['document']['title'].lower()
                    if artist:
                        title += (' ' + hit['document']['artistName'].lower())
                    asin = hit['document']['asin']
                    albums[title] = {'asin': asin,
                                     'artURL': hit['document']['artFull']['URL'],
                                     'artist': hit['document']['artistName'],
                                     'title': hit['document']['title']}
        if albums:
            match = album
            if artist:
                match += (' ' + artist)
            key, confidence = match_one(match.lower(),
                                        list(albums.keys()))
            if confidence > 0.7:
                confidence = min(confidence + bonus, 1.0)
                return (confidence,
                        {
                            'asin': albums[key]['asin'],
                            'artist': albums[key]['artist'],
                            'title': albums[key]['title'],
                            'artURL': albums[key]['artURL'],
                            'name': key,
                            'type': 'Album'
                        })
        return None, None

    def get_best_playlist(self, playlist):
        """ Get best playlist matching the provided name

        Arguments:
            playlist (str): Playlist name

        Returns: (str) best match, confidence, asin
        """
        LOG.debug("playlist {}".format(playlist))
        results = self.am.search(playlist, library_only=self.library_only,
                                 tracks=False, albums=False, playlists=True,
                                 artists=False, stations=False)
        playlists = {}
        for res in results:
            # LOG.debug(res[0])
            if 'playlist' in res[0]:
                for hit in res[1]['hits']:
                    title = hit['document']['title'].lower()
                    asin = hit['document']['asin']
                    playlists[title] = {'asin': asin,
                                        'artURL': hit['document']['artFull']['URL'],
                                        'title': hit['document']['title']}
        if playlists:
            key, confidence = match_one(playlist.lower(),
                                        list(playlists.keys()))
            LOG.debug("key {} confidence {}".format(key, confidence))
            if confidence > 0.7:
                return key, confidence, playlists[key]
        return None, 0, None

    def CPS_start(self, phrase, data):
        LOG.debug("phrase: {} data: {}".format(phrase, data))
        tracklist = []
        if 'continue' in data['type']:
            self.resume()
            return
        # single track
        if 'Song' in data['type']:
            stream_url = self._get_track_url_from_album(data['asin'],
                                                        data['albumAsin'])
            if stream_url:
                tracklist.append(stream_url)
        elif ('Album' in data['type']) or ('Playlist' in data['type']):
            if 'Album' in data['type']:
                entity = self.am.get_album(data['asin'])
            else:
                entity = self.am.get_playlists(data['asin'])
            for track in entity.tracks:
                stream_url = ""
                LOG.debug("getting url for {}".format(track.name))
                try:
                    stream_url = track.stream_url
                except Exception as e:
                    LOG.error(e)

                LOG.debug(stream_url)
                if stream_url:
                    tracklist.append(stream_url)
        elif 'Artist' in data['type']:
            results = self.am.search(data['name'],
                                     library_only=self.library_only,
                                     tracks=True, albums=False,
                                     playlists=False,
                                     artists=False, stations=False)
            tracklist = self._get_tracklist_from_searchresult(results, data)
        elif 'Genre' in data['type']:
            results = self.am.search(data['genre'],
                                     library_only=self.library_only,
                                     tracks=True, albums=False,
                                     playlists=False,
                                     artists=False, stations=False)
            tracklist = self._get_tracklist_from_searchresult(results, data)

        if len(tracklist):
            if self.state in ['playing', 'paused']:
                self.mediaplayer.stop()
                self.mediaplayer.clear_list()
            self.mediaplayer.add_list(tracklist)
            self.speak(self._get_play_message(data))
            metadata = self._get_play_ui_data(data)
            LOG.debug("metadata {}".format(metadata)
            self.enclosure.bus.emit(Message("metadata", metadata))
            self.mediaplayer.play()
            self.state = 'playing'
        else:
            LOG.debug("empty tracklist!")

    def _get_tracklist_from_searchresult(self, result, data):
        tracklist = []
        for res in result:
                for hit in res[1]['hits']:
                    stream_url = ""
                    if data['type'] == 'Artist':
                        if hit['document']['artistAsin'] == data['asin']:
                            album_asin = hit['document']['albumAsin']
                            track_asin = hit['document']['asin']
                            stream_url = self._get_track_url_from_album(
                                track_asin, album_asin)
                    elif data['type'] == 'Genre':
                        if hit['document']['primaryGenre'] == data['genre']:
                            album_asin = hit['document']['albumAsin']
                            track_asin = hit['document']['asin']
                            stream_url = self._get_track_url_from_album(
                                track_asin, album_asin)

                    if stream_url:
                        tracklist.append(stream_url)
        return tracklist

    def _get_play_ui_data(self, data):
        data_type = data['type']
        ui_data = {}
        ui_data["type"] = "amzn-music-skill.domcross"

        if data_type == 'Album':
            ui_data["upperText"] = "{}: {}".format(data_type, data['title'])
            ui_data["lowerText"] = data['artist']
            ui_data["imgLink"] = data['artURL']
        elif data_type == 'Song':
            ui_data["upperText"] = "{}: {}".format(data_type, data['title'])
            ui_data["lowerText"] = data['artist']
            ui_data["imgLink"] = data['artURL']
        elif data_type == 'Artist':
            ui_data["upperText"] = "{}".format(data_type)
            ui_data["lowerText"] = data['artist']
            ui_data["imgLink"] = data['artURL']
        elif data_type == 'Playlist':
            ui_data["upperText"] = "{}".format(data_type)
            ui_data["lowerText"] = data['title']
            ui_data["imgLink"] = data['artURL']
        elif data_type == 'Genre':
            ui_data["upperText"] = "{}".format(data_type)
            ui_data["lowerText"] = data['genre']
            ui_data["imgLink"] = data['artURL']

        return ui_data

    def _get_play_message(self, data):
        message = ""
        data_type = data['type']
        if data_type == 'Album':
            message = self.dialog_renderer.render(
                    "ListeningTo{}".format(data_type), {
                        'album': data['title'],
                        'artist': data['artist']
                    })
        elif data_type == 'Song':
            message = self.dialog_renderer.render(
                    "ListeningTo{}".format(data_type), {
                        'tracks': data['title'],
                        'artist': data['artist']
                    })
        elif data_type == 'Artist':
            message = self.dialog_renderer.render(
                    "ListeningTo{}".format(data_type), {
                        'artist': data['artist']
                    })
        elif data_type == 'Playlist':
            message = self.dialog_renderer.render(
                    "ListeningTo{}".format(data_type), {
                        'playlist': data['name']
                    })
        elif data_type == 'Genre':
            message = self.dialog_renderer.render(
                    "ListeningTo{}".format(data_type), {
                        'genre': data['genre']
                    })
        return message

    def _get_track_url_from_album(self, track_asin, album_asin):
        LOG.debug("track_asin {}, album_asin {}".format(track_asin,
                                                        album_asin))
        stream_url = ""
        album = self.am.get_album(album_asin)
        for track in album.tracks:
            if (track.identifierType == 'ASIN') and \
               (track.identifier == track_asin):
                LOG.debug("getting url for {}".format(track.name))
                try:
                    stream_url = track.stream_url
                except Exception as e:
                    LOG.error(e)
                break
        # LOG.debug(stream_url)
        return stream_url

    def stop(self):
        if self.state != 'idle':
            self.mediaplayer.stop()
            self.state = 'idle'
            return True
        else:
            return False

    def pause(self):
        if self.state == 'playing':
            self.mediaplayer.pause()
            self.state = 'paused'
            return True
        return False

    def resume(self):
        if self.state == 'paused':
            self.mediaplayer.resume()
            self.state = 'playing'
            return True
        return False

    def next(self):
        if self.state == 'playing':
            self.mediaplayer.next()
            return True
        return False

    def previous(self):
        if self.state == 'playing':
            self.mediaplayer.previous()
            return True
        return False

    def lower_volume(self):
        if self.state == 'playing':
            self.mediaplayer.lower_volume()
            return True
        return False

    def restore_volume(self):
        if self.state == 'playing':
            self.mediaplayer.restore_volume()
            return True
        return False

    def shutdown(self):
        if self.state != 'idle':
            self.mediaplayer.stop()
            self.mediaplayer.clear_list()

    def _track_start_handler(self):
        LOG.debug("_track_start_handler")

    def _playing_track_handler(self):
        LOG.debug("_playing_track_handler")

    def _track_info_handler(self):
        LOG.debug("_track_info_handler")

    # @intent_file_handler('music.amzn.intent')
    # def handle_music_amzn(self, message):
    #     self.speak_dialog('music.amzn')

    """
    Read credentials from file 'credentials.store' that is located in
    the skills base directory, e.g. /opt/mycroft/skills/amzn-music.comcross
    The credentials file is a pickled dictionary where the data is
    base64 encoded. This isn't super secure but will hinder the casual
    shoulder surfer to read the password
    """
    def _load_credentials_store(self):
        credentials = {}
        skill_dir = dirname(__file__)
        credentials_file = 'credentials.store'
        if path.exists(skill_dir):
            file_list = listdir(skill_dir)
            if credentials_file in file_list:
                with open(skill_dir + '/' + credentials_file, 'rb') as f:
                    credentials = pickle.load(f)
        return credentials

    def _load_vocab_files(self):
        # Keep a list of all the vocabulary words for this skill.  Later
        # these words will be removed from utterances as part of the station
        # name.
        vocab_dirs = [join(dirname(__file__), 'vocab', self.lang),
                      join(dirname(__file__), 'locale', self.lang)]
        for vocab_dir in vocab_dirs:
            if path.exists(vocab_dir):
                for vocab_type in listdir(vocab_dir):
                    if vocab_type.endswith(".voc"):
                        with open(join(vocab_dir, vocab_type), 'r') as vocfile:
                            for line in vocfile:
                                parts = line.strip().split("|")
                                vocab = parts[0]
                                self.vocabs.append(vocab)
        if not self.vocabs:
            LOG.error('No vocab loaded, ' + vocab_dirs + ' does not exist')

    def _clean_utterance(self, utterance):
        # LOG.debug("in {}".format(utterance))
        utt = utterance.split(" ")
        common_words = self.translate("common.words").split(",")
        # LOG.debug("common_words {}".format(common_words))
        # LOG.debug("vocabs {}".format(self.vocabs))
        for i in range(0, len(utt)):
            if utt[i] in self.vocabs or utt[i] in common_words:
                utt[i] = ""
        res = ""
        for u in utt:
            res += "{} ".format(u)
        prev_len = len(res) + 1
        while prev_len > len(res):
            res.replace("  ", " ")
            prev_len = len(res)
        # LOG.debug("out {}".format(res))
        return res.strip()

    def _get_match_level_by_category(self, cat_name):
        LOG.debug(cat_name)
        category = cat_name.lower()
        if "artists" in category:
            return CPSMatchLevel.ARTIST
        elif "tracks" in category:
            return CPSMatchLevel.TITLE
        elif "albums" in category:
            return CPSMatchLevel.TITLE
        elif "stations" in category:
            return CPSMatchLevel.CATEGORY
        elif "playlists" in category:
            return CPSMatchLevel.CATEGORY
        else:
            return None


def create_skill():
    return AmznMusicSkill()
