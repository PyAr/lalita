
==============================
Welcome to the lalita project!
==============================

lalita is yet another IRC bot, one where new functionality is simple to 
create just adding easy-to-write plugins.

lalita is written with some goals in mind:

	- Twisted! (we don't like threads)

	- Pluggable: easy to implement new functionalities

	- Have fun: yes, it's Python

All the code in lalita is licensed under GNU GPL v3. See LICENSE.txt for 
further info.

The project page is::

	https://edge.launchpad.net/lalita

To run the bot, create a config file (you can use the sample lalita.cfg.sample)
as a guideline, and run::

	ircbot.py -c <configfile> <server>

There're a lot of test cases! You can try them running "nosetests" (you 
need to have Nose installed).

To create a plugin, check the plugins/example.py one, and use it as a start.

We don't have a mail list for the project, but you can check in #pyar on 
Freenode, most of developers are around there.

Enjoy it!


Manhole
=======

The --manhole[-*] options enable a manhole ssh server the provides an
interactive interpreter to poke the bot instance(s).

Example:

Start the bot with "--manhole" option::

    $ python ircbot.py --manhole

From another terminal, connect to the machine where the bot is running,
port 2222::

    $ ssh admin@localhost -p 2222
    admin@localhost's password: admin

This will drop you in a python shell::

    >>> bot = servers['<server name>']
    # bot is a IrcBot instance
    >>> bot.say('<channel>', 'something')

WARNING: this is a potential security hole if the port 2222 (or the one you 
configure with --manhole-port) is accesible from internet or other machines.


How to run lalita without installing
====================================

From the top-level directory run::

    python lalita/ircbot.py

For example, setting logs in debug mode, pointing to the sample 
configuration, and choosing a server in localhost::

    python lalita/ircbot.py -o DEBUG lalita.cfg.sample localhost

