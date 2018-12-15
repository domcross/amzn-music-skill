from mycroft import MycroftSkill, intent_file_handler


class AmznMusic(MycroftSkill):
    def __init__(self):
        MycroftSkill.__init__(self)

    @intent_file_handler('music.amzn.intent')
    def handle_music_amzn(self, message):
        self.speak_dialog('music.amzn')


def create_skill():
    return AmznMusic()

