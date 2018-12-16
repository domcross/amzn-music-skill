# from mycroft import intent_file_handler
from mycroft.audio.services.vlc import VlcService
# mplayer stutters every 10sec when playin Amzn-Music's chunked mp3 streams
# from mycroft.audio.services.mplayer import MPlayerService
from mycroft.skills.common_play_skill import CommonPlaySkill, CPSMatchLevel
from mycroft.util.log import LOG
from os import listdir, path  # makedirs, remove,
from os.path import dirname, join  # exists, expanduser, isfile, abspath, isdir
from .amazonmusic import AmazonMusic


class AmznMusicSkill(CommonPlaySkill):
    def __init__(self):
        super().__init__(name="AmznMusicSkill")
        # self.mediaplayer = MPlayerService(config=None, bus=None)
        self.mediaplayer = VlcService(config={'low_volume': 30, 'duck': False})
        self.state = 'idle'
        self.cps_id = "amazonmusic"
        self.am = None
        self.vocabs = []    # keep a list of vocabulary words
        self.username = ""
        self.password = ""
        self.library_only = True

    def initialize(self):
        self.username = self.settings.get("username", "")
        self.password = self.settings.get("password", "")
        self.library_only = self.settings.get("library_only", True)

        self._load_vocab_files()

        if self.username and self.password:
            LOG.debug("login to amazon music")
            self.am = AmazonMusic(credentials=[self.username, self.password])
        self.mediaplayer.clear_list()

    def CPS_match_query_phrase(self, phrase):
        LOG.debug("CPS_match_query_phrase: {}".format(phrase))
        if not self.am:
            if self.voc_match(phrase, "Amazon"):
                # User is most likely trying to use Amazon Music, e.g.
                # "play amazon" or "play John Denver using Amazon Music"
                return (self.cps_id, CPSMatchLevel.GENERIC)

        LOG.debug("try search")
        clean_phrase = self._clean_utterance(phrase)
        am_result = self.am.search(clean_phrase, library_only=self.library_only)
        if am_result:
            for ar in am_result:
                cat_name = ar[0]
                match_level = self._get_match_level_by_category(cat_name)
                LOG.debug(cat_name)
                hits = ar[1]['hits']
                for h in hits:
                    dockeys = h['document'].keys()
                    if 'name' in dockeys:
                        name = h['document']['name']
                        LOG.debug("name: {}".format(name))
                    elif 'title' in dockeys:
                        name = h['document']['title']
                        LOG.debug("title: {}".format(name))
                    else:
                        name = ""
                        LOG.debug("unknown")
                    if name:
                        data = {'name': name, 'asin': h['document']['asin'], 'category': cat_name}
                        if "tracks" in cat_name:
                            data['albumAsin'] = h['document']['albumAsin']
                        return (clean_phrase, match_level, data)
        elif self.voc_match(phrase, "Amazon"):
            # User has setup Amazon Music on their account and said Amazon,
            # so is likely trying to start Amazon, e.g.
            # "play amazon" or "play some music on amazon"
            return (self.cps_id, CPSMatchLevel.CATEGORY)

    def CPS_start(self, phrase, data):
        LOG.debug("phrase: {} data: {}".format(phrase, data))
        tracklist = []
        # single track
        if 'tracks' in data['category']:
            stream_url = ""
            album = self.am.get_album(data['albumAsin'])
            for track in album.tracks:
                if (track.identifierType == 'ASIN') and \
                   (track.identifier == data['asin']):
                    LOG.debug("getting url for {}".format(track.name))
                    try:
                        stream_url = track.stream_url
                    except Exception as e:
                        LOG.error(e)
                    break
            LOG.debug(stream_url)
            if stream_url:
                tracklist.append(stream_url)
        elif 'albums' in data['category']:
            album = self.am.get_album(data['asin'])
            for track in album.tracks:
                stream_url = ""
                LOG.debug("getting url for {}".format(track.name))
                try:
                    stream_url = track.stream_url
                except Exception as e:
                    LOG.error(e)

                LOG.debug(stream_url)
                if stream_url:
                    tracklist.append(stream_url)
        # TODO artists, playlists, stations
        if len(tracklist):
            if self.state != 'idle':
                self.mediaplayer.stop()
            self.mediaplayer.clear_list()
            self.mediaplayer.add_list(tracklist)
            self.mediaplayer.play()
            self.state = 'playing'
        else:
            LOG.debug("empty tracklist!")

    def stop(self):
        if self.state != 'idle':
            self.mediaplayer.stop()
            self.state = 'idle'
            return True
        else:
            return False

    def shutdown(self):
        if self.state != 'idle':
            self.mediaplayer.stop()

    # @intent_file_handler('music.amzn.intent')
    # def handle_music_amzn(self, message):
    #     self.speak_dialog('music.amzn')

    def _load_vocab_files(self):
        # Keep a list of all the vocabulary words for this skill.  Later
        # these words will be removed from utterances as part of the station
        # name.
        vocab_dir = join(dirname(__file__), 'vocab', self.lang)
        if path.exists(vocab_dir):
            for vocab_type in listdir(vocab_dir):
                if vocab_type.endswith(".voc"):
                    with open(join(vocab_dir, vocab_type), 'r') as voc_file:
                        for line in voc_file:
                            parts = line.strip().split("|")
                            vocab = parts[0]
                            self.vocabs.append(vocab)
        else:
            LOG.error('No vocab loaded, ' + vocab_dir + ' does not exist')

    def _clean_utterance(self, utterance):
        LOG.debug("in {}".format(utterance))
        utt = utterance.split(" ")
        common_words = self.translate("common.words").split(",")
        LOG.debug("common_words {}".format(common_words))
        LOG.debug("vocabs {}".format(self.vocabs))
        #for vocab in self.vocabs:
        #    utterance = utterance.replace(' ' + vocab + ' ', " ")
        for i in range(0, len(utt)):
            if utt[i] in self.vocabs or utt[i] in common_words:
                utt[i] = ""

        res = ""
        for u in utt:
            res += "{} ".format(u)
        res.replace("  ", " ")
        res.lstrip()
        LOG.debug("out {}".format(res))
        return res

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
