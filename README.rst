
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

The project page is `https://github.com/PyAr/lalita`

To run the bot, create a config file (you can use the sample lalita.cfg.sample)
as a guideline, and run::

	ircbot.py -c <configfile> <server>

There're a lot of test cases! You can try them running `./test` (you
need to have `fades <https://github.com/PyAr/fades>` installed).

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

First you have to install the dependecies (maybe you want to do it inside a virtualenv)::

    pip install -r requirements.txt 

From the top-level directory and inside a virtualenv run::

    python lalita/ircbot.py

For example, setting logs in debug mode, pointing to the sample
configuration, and choosing a server in localhost::

    python lalita/ircbot.py -o DEBUG lalita.cfg.sample localhost

Or if you have `fades` installed just run::
   
    ./run_lalita -o DEBUG lalita.cfg.sample localhost


How To do a source release
--------------------------

 * edit setup.py and increment the version number.
 * 'python setup.py sdist'
 * look at the contents of the tarball created in dist/ to be sure they are ok
 * step into the dist directory for the following commands
 * sign the tarball by a command like:
     gpg -a --detach-sign lalita-VERSION.tar.gz
     this should create a file like lalita-VERSION.tar.gz.asc
 * Upload the new release to launchpad with a command like:
     lp-project-upload lalita VERSION lalita-VERSION.tar.gz
 * Announce the release, ping someone to build updated packages for the PPA and Ubuntu.


How To do a PPA release
-----------------------

 * "dch -e" and touch the version for lucid
 * debuild -S -sa
 * go to parent directory where you find the .changes
 * dput ppa:laliputienses/lalita-ppa lalita_VERSION_source.changes

 ** repeat this procedure for every Ubuntu version you want the PPA
