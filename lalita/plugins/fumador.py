# -*- coding: utf8 -*-

# this is the only stuff from lalita you need to import
from lalita import Plugin

import re

TRANSLATION_TABLE = {
    u'Uhhhh... Está hablando del fasooo!': {
        'en': u'Oh, yeah! He is talking about mariiiaaaa juanaaa!',
    },
}

MSG = ['fumar', 'humo', 'faso', 'marihuana', 'yerba', 'fumo', u'fumé',
       'marijuana', 'maria juana', 'verde', 'flores', 'flor', 'cogoyo',
       'cogolo', 'jamaica', 'san marcos sierra', 'fumador', 'pucho']

class Fumador(Plugin):
    def init(self, config):
        # register the translation table for our messages
        self.register_translation(self, TRANSLATION_TABLE)

        # log that we started
        self.logger.info("Init! config: %s", config)

        # register our methods to the events
        self.register(self.events.PUBLIC_MESSAGE, self.message)

        self.regex = re.compile('(' + '|'.join(MSG) + ')', re.IGNORECASE)

    def message(self, user, channel, msg):
        self.logger.debug("%s talked to me in %s: %s", user, channel, msg)
        if self.regex.findall(msg) != []:
            txt = u"Uhhhh... Está hablando del fasooo!"
            self.say(channel, txt)
