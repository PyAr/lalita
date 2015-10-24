# -*- coding: utf8 -*-

# Copyright 2015 laliputienses
# License: GPL v3
# For further info, see LICENSE file

from lalita import Plugin


class SeDice(Plugin):
    '''Plugin to teach Lalita how to answer'''

    def init(self, config):
        # log that we started
        self.logger.info("Init! config: %s", config)

        # register our methods to the events
        self.register(self.events.TALKED_TO_ME, self.talked_to_me)
        self.register(self.events.COMMAND, self.se_dice, ("se_dice",))
        self.register(self.events.COMMAND, self.no_se_dice, ("no_se_dice",))
        self.register(self.events.COMMAND, self.badword, ("badword",))

    def talked_to_me(self, user, channel, msg):
        self.logger.debug("%s talked to me in %s: %s", user, channel, msg)
        question = self.sanitize_question(msg)
        answer = self.get_answer(question)
        if answer:
            answer = "{}: %s".format(answer)
            self.say(channel, answer, user)
        else:
            self.store_question(question)

    def get_answer(self, question):
        pass

    def store_question(self, question):
        pass

    def sanitize_question(self, question):
        """ pongo question en minuscula y reemplazo caracteres raros
        """
        question = question.lower().strip().replace("#", " ").replace('"', " ")..replace("'", " ")
        return question

    def se_dice(self, user, channel, commands, *args):
        u"@se_dice: le enseña a lalita qué responder"
        pass

    def no_se_dice(self, user, channel, commands, *args):
        u"@no_se_dice: le enseña a lalita que NO responder"
        pass

    def badword(self, user, channel, commands, *args):
        u"@badword: Agrega una palabra a un blacklist"
        pass
