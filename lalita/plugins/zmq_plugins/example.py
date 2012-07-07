# -*- coding: utf8 -*-
# Copyright (C) 2011 Guillermo Gonzalez
import os
import json

from lalita.plugins.zmq_proxy import PluginProcess


class Example(PluginProcess):
    """Example zmq-based plugin."""

    def init(self, config):
        self.logger.info("Configuring Example Plugin!")
        # register the commands
        self.register_command(self.cmd_example, "example")
        self.register_command(self.cmd_example1, "example1")
        self.register("irc.private_message", self.example_priv)
        self.register("irc.talked_to_me", self.cmd_example)

    def example_priv(self, user, command, *args):
        """Just say something."""
        self.say(user, "This is an example plugin.")

    def cmd_example(self, user, channel, command, *args):
        """Just say something."""
        self.logger.debug("command %s from %s (args: %s)", command, user, args)
        self.say(channel, "This is an example plugin.")

    def cmd_example1(self, user, channel, command, *args):
        """Just say something."""
        self.logger.debug("command %s from %s (args: %s)", command, user, args)
        self.say(channel, "Another example.")


if __name__ == "__main__":
    import optparse
    parser = optparse.OptionParser()
    parser.add_option("-s", "--events-address", dest="events_address",
                      default="tcp://127.0.0.1:9090")
    parser.add_option("-b", "--bot-address", dest="bot_address",
                      default="tcp://127.0.0.1:9091")
    options, args = parser.parse_args()
    import logging
    logging.basicConfig()
    logging.getLogger().setLevel(logging.DEBUG)

    try:
        Example(options.events_address, options.bot_address).run()
    except:
        import traceback;
        traceback.print_exc()

