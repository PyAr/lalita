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

        self.register(self.events.COMMAND, self.photo_command, ['foto'])
        self.register(self.events.PRIVATE_MESSAGE, self.photo_private)

    def photo_command(self, user, channel, command, nick=None, url=None):
        u"""Devuelve o configura la foto del usuario.

        Sintaxis:

            photo <nick>: contesta con la foto de 'nick'
            photo <nick> <url>: configura 'url' para ese 'nick'
            photo <nick> None: borrar la config de 'nick'

        Nota: un usuario sólo puede configurar su propia URL.
        """

        retTxt = self._photo(user, nick, url)
        self.say(channel, retTxt)

    def photo_private(self, user, msg):
        u"""Devuelve o configura la foto del usuario.

        Sintaxis:

            photo <nick>: contesta con la foto de 'nick'
            photo <nick> <url>: configura 'url' para ese 'nick'
            photo <nick> None: borrar la config de 'nick'

        Nota: un usuario sólo puede configurar su propia URL.
        """

        args = msg.split()
        command = args[0]
        if not 'foto' in command:
            return
        if len(args) == 1:
            nick, url = (None, None)
        else:
            nick = args[1]
            url = args[2] if len(args) == 3 else None

        retTxt = self._photo(user, nick, url)
        self.say(user, retTxt)

    def _photo(self, user, nick=None, url=None):
        u"""Funcionalidad en común para photo_command y photo_private."""

        if nick is None:
            return u"%s: tell me the nick" % user

        if url is None:
            # getting stuff
            photo = self._get_photo(nick)
            if not photo:
                return u"%s: doesn't have configured URL" % user
            return u"%s: %s" % (user, photo)
        else:
            # setting stuff
            if nick != user:
                return u"%s: can't change other user's photo" % user

            if url == u"None":
                photo = self._get_photo(nick)
                if photo:
                    self._del_photo(nick)
                    return u"%s: URL removed (was: %s )" % (user, photo)
                else:
                    return u"%s: doesn't have configured URL" % user
                return

            # set the photo!
            self._set_photo(nick, url)
            return u"%s: URL configured!" % user

    def _get_photo(self, nick):
        """Returns the photo for the nick."""
        return self._photos.get(nick)

    def _set_photo(self, nick, url):
        """Sets the photo for the nick."""
        self._photos[nick] = url

    def _del_photo(self, nick):
        """Removes the photo for the nick."""
        del self._photos[nick]
