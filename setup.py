#!/usr/bin/env python
from distutils.core import setup

setup(
    # metadata
    name='lalita',
    version='0.1',
    maintainer='laliputienses',
    maintainer_email='',
    description='Yet another IRC bot, one where new functionality is simple ' \
                'to create just adding easy-to-write plugins.',
    license='GNU GPL v3 ',
    keywords=['irc', 'bot', 'twisted', 'plugin'],
    url='https://launchpad.net/lalita/',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Console',
        'Framework :: Twisted',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License (GPL)',
        'Programming Language :: Python',
        'Topic :: Communications :: Chat :: Internet Relay Chat',
    ],

    # content
    package_dir={'': 'src'},
    packages=['lalita', 'lalita.core', 'lalita.plugins'],

    # scripts
    scripts=['src/lalita/ircbot.py'],

    # dependencies
    requires=[
        'beautifulsoup',
        'chardet',
        'pyopenssl',
        'pysqlite',
        'twisted',
    ],
)
