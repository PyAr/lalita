Lalita
======

Who is Lalita?
-----------------

Lalita is an extensively pluginable IRC bot.

That is, Lalita is a framework that lets you create your own custom IRC bot
according to your needs.

moreover, Lalita comes with a couple plugins included (see below)

What is an IRC bot?
-------------------

IRC (Internet Relay Chat) is a chat

Most of the time, an IRC bot doesn't try to mimic an human being (but it can do
it), instead, it provides services to the channel users.

This bot provides services by listening to the users and answering certain
commands they provide him. Next we'll see some ways of doing this.

Our first example
=================

In this section we'll make a simple bot that sums the numbers the user gives
it.

Here is the code:

    # -*- coding: utf8 -*-

    from lalita import Plugin

    class Sum(Plugin):
        """Example that adds the given numbers"""

        def init(self, config):
            self.register(self.events.TALKED_TO_ME, self.action)

        def action(self, user, channel, msg):
            u"Adds the given numbers"
            result = sum(int(x) for x in msg.split())
            self.say(channel, u"%s, the sum is %d", user, result)

This plugin starts by making a new Python class which inherits from the
included ``Plugin`` class. This class gives us everything needed to start
coding our plugin, as we'll see in the next paragraphs.

This class will be instanced in each channel and server the bot runs, with a
certain configuration (none in this example). When the class is instanced, this
instance should be registered to the desired events, in this case, the event
``TALKED_TO_ME``, and the method to execute.

Let's analize this line of code::

    self.register(self.events.TALKED_TO_ME, self.action)

The self.register method is the method we use to register an event. This method
needs at least two parameters (see below for full documentation): the event
itself, and the method to run.

In this example, the event is ``TALKED_TO_ME``, this event is in self.events
and is triggered when somebody in the channel talks to the bot. And the method
is ``self.action`` defined in the same class.

This method is pretty unrestricted, but one must be careful to define each set
of parameters for each event. In this example, the method will take the user
who talked to the bot, the channel in which he said it, and the message itself.

After computing the result (the sum of the numbers), we return this result to
the user with another inherited method, ``self.say``. This method takes: the
destination of this message (in this case, the channel where we got the
message), the message we want to send, and the values to be inserted in this
message (later we'll see the reason we don't pass them together).

The next dialogue is an example of this example running in real life::

    <user>   examplebot, 12 88
    <examplebot>  user, the sum is 100
    <user>   examplebot, 4 5 6
    <examplebot>  user, the sum is 15


How do I test this example?
----------------------

Lalita is a Python module. To run Lalita, you need to install Python,
``http://www.python.org/getit`` and the Twisted module for Python
``http://twistedmatrix.com/trac/wikiDonwloads``.

If you have setuptools, you can install Lalita by entering
``easy_install lalita`` in a terminal. also you can get Lalita in a tarball,
from ``https://edge.launchpad.net/lalita`` or if you have bazaar, you can
download the complete project with ``bzr branch lp:lalita``.

If you have already downloaded Lalita you can uncompress it in any folder, go
to that folder and run ``python setup.py install``.

After installing, you can access the installed folder, there you will see many
files, now we will focus on three.

- The example code, which we will save in the ``plugins`` folder, in a file
called ``plugins/exampledoc.py``.

-The main file, called ``ircbot.py``, the one we'll execute later.

-A config file, ``lalita.cfg.sample``, that has many default configurations,
that you can adjust to your liking. Here we will show you how to make a basic
configuration for this example.

This config file is a Python dictionary with all the needed data to setup the
bot. Here we will show a basic configuration. The rest  of the options will be
explained later.

for this example we will use::

    servers = {
       'example': dict(
           encoding = 'utf8',
           host = 'localhost', port = 6667,
           nickname = 'examplebot',
           channels = {
               '#humites': {},
           },
           plugins = {
               'ejemplodoc.Sum': {},
           },
       ),
    }

In this example, we have only one server, called ``example``, which points to
localhost, port 6667 (for testing, it's preferred to install an IRC server in
your own computer, like ``dancer-ircd``, so we can define our personal
configuration, without any hassle).

In the configuration we decided to name this bot ``examplebot``, to use utf-8
encoding, and to connect to the server in the ``humites`` channel, and to make
an instance of the example plugin, ``ejemplodoc.Sum`` (the filename without
.py, and the classname, separated by a dot), this lets you select which plugins
to use, without using all of the plugins in the file.

After we have saved lalita.cfg, we can test the bot::

  python ircbot.py example

We use ``python`` to call the Python interpreter, ``ircbot.py`` to execute
Lalita, and ``example`` to point Lalita the server to use (we can have many,
and select which ones to use). This is the simplest way to run Lalita, we will
show more options below.


Using commands
==============

The most common way to use the functionality of the previous example is with
the help of commands.

Using  commands lets us ask the bot to do certain functions without having to
speak directly to him. Commands can be identified easily because all begin with
the ``@`` character


    <user>   @sum 12 88
    <examplebot>  user, the sum is 100
    <user>   @sum 4 5 6
    <examplebot>  user, the sum is 15

Here you can see that we don't speak to the bot directly, instead we use the
command ``sum``. To use commands, we have to modify our previous source like
this::

    # -*- coding: utf8 -*-

    from lalita import Plugin

    class Sum(Plugin):
        """Example that sums the given numbers."""

        def init(self, config):
            self.register(self.events.COMMAND, self.action, ("sum",))

        def action(self, user, channel, command, *args):
            u"Sums the given numbers."
            result = sum(int(x) for x in args)
            self.say(channel, u"%s, the sum is %d", user, result)

You can see that we changed the register line. Now we register another event,
and we give it another parameter: a tuple with commands to register (``sum``,
that we'll use with the ``@``)

Also, it changed the parameters of the ``action`` function, now it takes an
user, a channel, and the command we'll use to call it (the sum is calculated in
another way because the arguments come preprocessed)


Multiple commands for the same functionality
-----------------------------------------------

It's normal to need multiple commands with the same functionality. This is used
to support multiple languages, or deprecated commands.

Lalita lets you do this easily in the same way we choose one command::

        self.register(self.events.COMMAND, self.action,
                      ("suma", "sumar", "sum"))

Then we can use any of the following commands::

    <user>   @sumar 12 3
    <examplebot>  user, the sum is 15
    <user>   @suma 12 3
    <examplebot>  user, the sum is 15
    <user>   @sum 12 3
    <examplebot>  user, the sum is 15


lalita default commands
-------------------------

Lalita has its own meta-commands that lets you check on its functionality
irregardless of the installed plugins.

These commands are: ``help``, ``list`` and ``more``.

``help`` gives you basic documentation, or the documentation of any especific
command. ``list`` gives you a list of all available commands.
Here are some examples::

    <user>   @help
    <examplebot>  "list" para ver las ordenes; "help cmd" para cada uno
    <user>   @list
    <examplebot>  Las ordenes son: ['help', 'list', 'more', 'sum', 'suma', 'sumar']
    <user>   @help sum
    <examplebot>  Sums the given numbers.

In the list of commands you can see all the meta-commands, and all the commands
that we registered (even multiple commands for the same function). The help
comes from the docstring at the beginning of each method.

The third meta-command is ``more``, It's a command used only in very specific
cases: to avoid problems with moderation.
``
IRc bots can answer commands with multiple lines responses, this is useful in
certain cases, like a search function. But if the bot posts too much responses
in a short period of time, the server considers it flooding, and will kick the
bot off the channel. this is the reason Lalita has a limit to responses a
plugin can make over time.

If the plugin posts too many lines to the same channel, or to the same user,
the first 5 will be posted, and the rest will be queued until the user who
issued the command gives the command ``more``, making the bot post 5 more,
until the queue is emptied, the user gives other command, or a certain time
passes, and the messages are deleted automatically.

*FIXME: point how to change the number of posts (5)*


Which are the events we can receive?
============================================

Plugins can receive many events. The following list groups them by the type of
event, and shows the parameters it gives, and a brief description.

Events related to the connection of a bot in a server::

- ``CONNECTION_MADE []``: The connection was succesful against the server.

- ``CONNECTION_LOST []``: Thee connection got lost.

- ``SIGNED_ON []``: The bot Logged in succesfuly.

- ``JOINED [channel]``: The plugin joined the indicated channel.

Events that point people speaking:

- ``PRIVATE_MESSAGE [user, message]``: Somebody talked to Lalita in a private
(not in a public channel).

- ``TALKED_TO_ME [user, channel, message]``: Somebody talked specifically to
Lalita in a public channel.

- ``PUBLIC_MESSAGE [user, channel, message]``: Somebody said something in a
public channel.

- ``COMMAND [user, channel, command, parameters]``: A command that somebody
said in a channel, specifies the user, the channel, the command and the
parameters.

Events that represent actions of users or between users.

- ``ACTION [user, channel, message]``: the user generated an action in the
channel (for example, "/me").

- ``JOIN [user, channel]``: The user joined the channel.

- ``LEFT [user, channel]``: The user left the channel.

- ``QUIT [user, message]``: The user disconnected from the channel, leaving a
predefined message.

- ``KICK [kicked, channel, kicker, message]``: The "kicked" user has been
banned from the channel by the "kicker" user, with a message written by the
kicker.

Registering events
===================

We already saw the basics of a plugin registering a method against an event.
Now we'll see all posible combinations.

As we said, the basics of registering an event are::

    self.register(<event>, <method>)

Most of events will only take those two parameters, but sometimes we'll need
more.

*FIXME: explain what happens if a method is registered twice*


Multiple commands
------------------

In the case of the ``command`` event, one must specify a tuple with the names
of the commands that will be registered for the method. This lets us especify
multiple commands for one method, and multiple  methos for one command. For
example::


    self.register(self.events.COMMAND, self.sum, ("sumar", "sum"))
    self.register(self.events.COMMAND, self.multiply, ("mult", "multiply"))
    self.register(self.events.COMMAND, self.divide, ("div",))

*FIXME: there isn't an example for multiple methods for one command*


Filtering the messages
----------------------

If the event is one of the following: ``TALKED_TO_ME``, ``PRIVATE_MESSAGE`` and
``PUBLIC_MESSAGE``, you can especify a regular expression so Lalita can filter
between the received messages. This is useful because there can be many
unwanted messages that the bot doesn't need to read, especially the ones from
``PUBLIC_MESSAGE``, that comprises all of the channel's traffic.

An example of filtering::

        regex = re.compile(".*http://.*")
        self.register(self.events.PUBLIC_MESSAGE, self.action, regex)

Then our method ``self.action`` won't read all messages, instead, it will only
read those that have ``http://`` in the message.

You should take notice that we don't use the regular expression string.
Instead, we use a compiled regular expression, whis is for flexibility: so we
can use not only regular expressions, but any object that has the ``.match()``
method (the message is passed to the plugin only if the method returns
``True``).

Automatic commands
------------------

It's easier and more direct for the bot users, in some cases, to specify the
command talking directly with the bot, either in public or in private (and not
only using ``@`` at the beginning).

For example, if we have an ``add`` command, as with the previous example, we
could have the following dialog::

    <user>   @add 12 3
    <examplebot>  user, the sum is 15
    <user>   examplia, add 12 3
    <examplebot>  user, the sum is 15

This could be done by hand (receiving all public and private events, and
filtering), but Lalita already provides this functionality.

To activate it, just do this::

        self.set_options(automatic_command=True)

*FIXME: we won't have set_options, all options will be handled from config.*

This way, all the events ``TALKED_TO_ME`` and ``PRIVATE_MESSAGE`` that have a
message that begins with a registered command will be modified and sent to the
plugin as if it was an order, and not an event of those types.


Speaking with more freedom
==========================

In a previous chapter, we showed the basic use of ``self.say``, the tool that
plugins have to say things to users.

The tool's sintax is quite simple::

    self.say(<target>, <text>, [<arg1>, ...])

The target is to whom the message is destined.  If it's a user, the message
will be private; if it's a channel (starts with ``#``), the message will be
published publicly. Nevertheless, Lalita applies a restriction here: the plugin
only answers something through the same channel used for asking or in private,
but it won't cross channels.

The second parameter is the text that we intend to send. There isn't a
restriction on the length, but really long texts will break into several lines
because of restrictions inherent to IRC. It's recommended that the text is a
Unicode chain, even if the message only contain ASCII characters.

If we want to compose the message with some parameters (like the user name or
the sumation from the previous example), you MUST NOT replace it directly, but
assemble the string and pass the parameters after the text.

In other words, and with the previous example on mind, it's recommended NOT to
do the following::

        self.say(channel, u"%s, la suma es %d" % (user, result))

You should do it this way::

        self.say(channel, u"%s, la suma es %d", user, result)

There's two reasons for this. The first one is that if we have a wrong number
of parameters or incorrect data types, Lalila can handle this much better. The
second and most important reason is that, if we don't replace those values,
they can be internationalized (see below for more details).


Being verbose
-------------

There's no restriction on the number of lines that a plugin can answer (besides
the message queuing to avoid *flooding*).

That is, a plugin can answer two or more lines, using ``self.say`` several
times, for example::

        self.say(channel, u"The result is %d", result)
        self.say(channel, u"(calculation time: %.2f seconds)", t)


Promissing answers
------------------

Plugin methods shouldn't take long to finish. This is because Lalita is
programmed using an asynchronous execution engine called Twisted_, so method
executions are not interruptable.

In other words, if a plugin method takes too long to finish, Lalita can't do
the rest of things it's supposed to do (listen to multiple channels, execute
other plugins' methods, etc.).

So ¿How can potentially long services, like databases or the network, be used?
Here is where a Twisted's mechanism called Deferreds_ enters.

You can search documentation about Deferreds on that link, and check in the
example plugin (``plugins/example.py``) how to implement it, but basically the
process is: instead of doing ``self.say()`` and answer something, the method's
execution returns the promise to answer.

This promise is the *deferred*, which will be consumed when the plugin is ready
to answer. The plugin can return or not the deferred, and the functionality
will be the same. But, if after using a deferred, the plugin
returns it, Lalita will use it to log whether the method ended successfully or
not.


Talking without answering
-------------------------

*FIXME: maybe we should say the default is "talk freely", and that you can
configure it to be more restricted. We should rewrite this here if it is that
way*

As we said before, there's a basic rule that Lalita enforces for all plugins:
they can only answer through the channel that talked to them (or the person
that started the dialog, in private). This is a useful security rule, but at
the same time it restricts a function that specific plugins may wish to have
(for example, a plugin that notifies something on all the channels that Lalita
is present).

A secondary effect of this limitation is that Lalita can't speak without being
spoken to, and there are use cases that would desire such a feature, for
instance, a plugin that informs news received from a RSS.

If you require any of those features, you should deactivate this restriction
this way::

        self.set_options(free_talk=True)

*FIXME: we won't have set_options, all options will be handled from config.*

After this configuration, we can generate all the messages we want from the
plugin, to whichever target, regardless of who initiated the conversation.


Writing a more professional plugin
==================================

Even if writing a plugin is simple, implementing a robust feature, capable of
distributing messages in a number of languages, or have it running 7x24 as a
reliable service, requires taking a few precaucions and using some mechanisms.

Logging
-------

A tool that Lalita offers is logging information, which will be saved to disk
or printed on the screen, depending on the configuration, see below). For this,
plugins incorporate ``self.logger``, which you can use with different levels of
severity, for example::

        self.logger.debug("Received a message from %s", user)
        self.logger.error("Internal error while processing the request")

The different levels that can be used are ``debug``, ``info``, ``warning``,
``error`` and ``critical``. These levels are the classical levels from the
`Python logging module`_.


Documenting your methods
------------------------

The docstrings for plugins' methods, which implement the required
functionality, are interpreted automatically by Lalita as the help
documentation it will offer to the user.

On our previous example, there's a method that added numbers supplied to the
bot through the ``add`` command::

    def action(self, user, channel, command, *args):
        u"Add the supplied numbers."
        ...

The user, then, could do...::

    <user>   @help add
    <examplia>  Add the supplied numbers.

...and receive directly the documentation.

These docstrings should be Unicode strings. Also, these docstrings are
internationalizable, as it is explained in the next section.


Internationalizing the text
---------------------------

Lalita has an internationalization (i18n) mechanism that differs from the
standard followed by all programs. This is because the standard way implies
that the program has a specific language; Lalita can speak a certain language
in a specific channel, and a different language in another.

The plugin must provide a translation table, and it should register it this
way::

        self.register_translation(self, TRANSLATION_TABLE)

This translation table is simply a Python dictionary with the following
structure::

    { <original string 1>: { <language1> : <string 1 en language 1>,
                             <language2> : <string 1 en language 2>,
                             ...
                           },
      <original string 2>: { <language1> : <string 2 en language 1>,
                             <language2> : <string 2 en language 2>,
                             ...
                           },
      ...
    }

Note that you don't have to wrute the original chains on your code in a
particular language, you just need to provide the translations to the relevant
languages on the table.

The different languages 1, 2, etc. shown before are "en", "it", etc.,
that is, they follow the two-letter standard. This two letters are used on the
channel configuration, and it's the way Lalita and the plugins knows which
language is spoken on the server.

You can see a real implementation of this in the example plugin
``plugins/example.py``.


Configuring the plugin
----------------------

On the example ``lalita.cfg``, there's an option to use the sumation plugin::

       plugins = {
           'ejemplodoc.Sum': {},
       },

There's an empty configuration dictionary being provided, but a perfectly
arbitrarious dictionary can be supplied; Lalita will give this configuration to
the plugin at initialization time. The ``config`` parameter from ``__init__``
is just that, and allows for plugin configuration from the file, without the
need to implement alternative mechanisms.


Some plugins integrated to Lalita
=================================

Lalita ships with a few plugins that implement basic functionality, useful for
a lot of IRC channels.

The idea behing them being part of the project is that, if the same or similar
functionality is required, it's not necessary to start from scratch. In the
same way, they are also useful as examples on how to do certain tasks. Having
said that, the pĺugins' quality varies: some of them comply with PEP 8 and have
test cases in the folder ``plugins/tests/``, while others not even have
docstrings...

- example.py: Example plugin; doesn't provide any useful or specific
  functionality, but is a good example to read and copy.

- freenode.py: Performs an authentication dialog against Freenode servers (some
  parameters need to be configured properly, see ``lalita.cfg.sample``). This
  plugin doesn't offer functionality to the end user, but it allows the
  connection to those servers without requiring us to authenticate.

- misc.py: Implements very simple functionality: answers "pong" to the user
  when someone tells Lalita "ping".

- seen.py: Implements two interesting functionalities: "last" y "seen".
  The former tells what was the last thing a specific user said, and the latter
  tells you when was the last time the user was seen
  (sometimes this works, sometimes it doesn't).

- url.py: Recollects all the URLs that are mentioned on the different channels,
  and you can search them afterwards.

- zmq_proxy.py: It's a IRC-ZeroMQ <http://www.zeromq.org/> proxy/bridge, that 
  publish all lalita events to a PUB/SUB ZeroMQ socket and listen for commands
  in other socket (in json format). See zmq_plugins/example.py for an example 
  plugin using this.


Advanced configuration
======================

The configuration file used by Lalita has many options and is quite flexible,
so beyond inspecting the ``lalita.cfg.sample`` it's interesting to describe its
capabilities.  Also, when ``ircbot.py`` executes, there are other options that
can be used, which will be described in the next section.


The config file
--------------------

The ``lalita.cfg`` file structure is basically the one of a giant Python
dictionary.

Each one of the keys of this dictionary is one of the servers, that can be
selected when startig lalita. And the values of each key is another dictionary
that defines the configuration of each server

The dictionary of each server can have the following keys:

 - encoding: character encoding that will be used in the server ("utf8",
"latin1", etc.).

 - host: The IP or name of the server.

 - port: The port number that will be used for the connnection.

 - nickname: The nick that will be used by the bot

 - channels: The channels that the bot will enter, and their configuration

 - plugins: The plugins (and their configuration) that will be executed serve
side (see below).

 - ssl: Must be ``True`` if we are going to use SSL for the connection.

 - password: An optional password for the server.

 - plugins_dir: The directory where the server will look for the plugins (by
default, the ``plugins/`` directory).

The value of the ``channels`` key must be a dictionary, where the keys are the
name of the channels, and the value is the configuration for each channel. This
configuration has two keys: ``plugins``, that defines the plugins enabled in
this channel, and ``encoding``, with the encoding for the channel (if it
differs from the one of the serverr).

The plugins can be defined both at server level, and at channel level. Both
cases can be useful, and there is no definition of which is better. We'll
define it on the channel level if we want it on a specific channel, and we'll
define it at server level if it is needed for the server connection, or we want
to use it on private messages, or if we want it in all of the server.

It would be difficult too explain all the different configurations, but you can
check the ``lalita.cfg.sample`` for more information.


Command line parameters
------------------------------

When we run Lalita through ``ircbot.py`` you have multiple parameters that let
you control many options.

The sintax is::

    ircbot.py [-t][-a][-o output_loglvl][-p plugins_loglvl]
              [-f fileloglvl][-n logfname] [server1, [...]]


The *-t* argument (or *--test*) lets you realize a couple of tests: it runs two
plugins that connect to a channel and chat between them. This is only for tests
reasons, and has no other use.

The *-o* argument, (or *--output-log-level*),  *-p* (or *--plugin-log-level*)
and *-f* (or *--file-log-level*) let you select different verbose levels for
the different logs (output, plugins), and if you want to save log files.

The logging level by default is INFO (which won't show debug messages), you can
select DEBUG, to see all, and WARNING, if you want to see only warnings and
more serious problems, or any desired combination.

The *-n* parameter (or *--log-filename*) defines in which file to save the logs.

.. _IRC: http://en.wikipedia.org/wiki/Internet_Relay_Chat
.. _Twisted: http://twistedmatrix.com/trac/
.. _Deferreds: http://twistedmatrix.com/documents/current/core/howto/defer.html
.. _Python logging module: http://docs.python.org/dev/library/logging.html#logging-levels
