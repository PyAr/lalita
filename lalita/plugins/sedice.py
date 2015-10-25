# -*- coding: utf8 -*-

# Copyright 2015 laliputienses
# License: GPL v3
# For further info, see LICENSE file
import os
import shelve

from lalita import Plugin


class SeDice(Plugin):
    """Plugin to teach Lalita how to answer"""

    def init(self, config):
        # log that we started
        self.logger.info("Init! config: %s", config)
        self.current_question = None
        # open shelve DB
        base = config.get('basedir', None)
        if base is not None:
            base = os.path.join(base, config.get('channel_folder', ''))
            if not os.path.exists(base):
                os.makedirs(base)
            self.answers = shelve.open(os.path.join(base, 'answers'))
        else:
            self.answers = {}

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
            self.logger.debug("Answer found for %s: %s", question, answer)
            answer = "%s: {}".format(answer)
            self.say(channel, answer, user)
        else:
            self.logger.debug("No answer found for %s. I'm going to wait for someone to teach me")
            self.current_question = question

    def get_answer(self, question):
        """Search a answer for a given question."""
        if self.answers.has_key(question):
            return self.answers[question]
        return None

    def store_answer(self, question, answer, overwrite=False):
        """Store a new answer for a question."""
        if overwrite or not self.answers.has_key(question):
            self.logger.debug("Storing new answer for %s: %s", question, answer)
            self.answers[question] = answer
            self.answers.sync()

    def sanitize_question(self, question):
        """Returns a saniteized string."""
        chars_to_replace = ['\'', '"', '#', ';', ',']
        for char in chars_to_replace:
            question = question.replace(char, '')
        sanitized_question = " ".join(question.strip().lower().split())
        return sanitized_question

    def se_dice(self, user, channel, commands, *args):
        u"@se_dice: le enseña a lalita qué responder"
        pass

    def no_se_dice(self, user, channel, commands, *args):
        u"@no_se_dice: le enseña a lalita que NO responder"
        pass

    def badword(self, user, channel, commands, *args):
        u"@badword: Agrega una palabra a un blacklist"
        pass
