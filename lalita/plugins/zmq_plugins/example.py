# -*- coding: utf8 -*-
# Copyright (C) 2011 Guillermo Gonzalez
import os
import json

from lalita.plugins.zmq_proxy import SubProcessPlugin


class Example(SubProcessPlugin):
    """Example zmq-based plugin."""

    def __init__(self, config):
        super(Example, self).__init__(config)
        self.logger.info("Configuring Example Plugin!")
        # register the commands
        self.register_command(self.cmd_example, lambda a: "example" in a)
        self.register("irc.private_message", self.example_priv)
        self.register("irc.talked_to_me", self.cmd_example)

    def example_priv(self, user, command, *args):
        """Just say something."""
        self.say(user, "This is an example plugin.")

    def cmd_example(self, user, channel, command, *args):
        """Just say something."""
        self.logger.debug("command %s from %s (args: %s)", command, user, args)
        self.say(channel, "This is an example plugin.")


if __name__ == "__main__":
    config = json.loads(os.environ.get('plugin_config', '{}'))
    import logging
    logging.basicConfig()

    try:
        Example(config).run()
    except:
        import traceback;
        traceback.print_exc()

