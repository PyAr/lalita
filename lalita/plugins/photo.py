# -*- coding: utf8 -*-

# Copyright 2009 laliputienses
# License: GPL v3
# For further info, see LICENSE file

import os
import shelve

from lalita import Plugin

TRANSLATION_TABLE = {
    u"%s: URL configured!": {'es': u"%s: URL configurada"},
}


class Photo(Plugin):
    """Plugin that implements the "photo" command."""
    def init(self, config):
        base = config.get('base_dir')
        self.register_translation(self, TRANSLATION_TABLE)
        if base is not None:
            if not os.path.exists(base):
                os.makedirs(base)
            self._photos = shelve.open(os.path.join(base, 'photos'))
        else:
            self._photos = {}

        self.register(self.events.COMMAND, self.photo, ['foto'])

    def photo(self, user, channel, command, nick=None, url=None):
        u"""Devuelve o configura la foto del usuario.

        Sintaxis:

            photo <nick>: contesta con la foto de 'nick'
            photo <nick> <url>: configura 'url' para ese 'nick'
            photo <nick> None: borrar la config de 'nick'

        Nota: un usuario sólo puede configurar su propia URL.
        """
        if nick is None:
            self.say(channel, u"%s: tell me the nick", user)

        if url is None:
            # getting stuff
            photo = self._get_photo(nick)
            if not photo:
                self.say(channel, u"%s: doesn't have configured URL", user)
                return
            self.say(channel, u"%s: %s", user, photo)
        else:
            # setting stuff
            if nick != user:
                self.say(channel, u"%s: can't change other user's photo", user)
                return

            if url == u"None":
                photo = self._get_photo(nick)
                if photo:
                    self._del_photo(nick)
                    self.say(channel, u"%s: URL removed (was: %s )",
                             user, photo)
                else:
                    self.say(channel, u"%s: doesn't have configured URL", user)
                return

            # set the photo!
            self._set_photo(nick, url)
            self.say(channel, u"%s: URL configured!", user)

    def _get_photo(self, nick):
        """Returns the photo for the nick."""
        return self._photos.get(nick)

    def _set_photo(self, nick, url):
        """Sets the photo for the nick."""
        self._photos[nick] = url

    def _del_photo(self, nick):
        """Removes the photo for the nick."""
        del self._photos[nick]
