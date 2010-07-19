#!/usr/bin/env python
from distutils.core import setup

setup(
    # metadata
    name = 'lalita',
    version = '0.1.3',
    maintainer = 'Facundo Batista',
    maintainer_email = 'facundo@taniquetil.com.ar',
    description = 'Yet another IRC bot.',
    long_description = 'Yet another IRC bot, one where new functionality is '\
                       'simple to create just adding easy-to-write plugins.',
    license = 'GPL v3',
    keywords = ['irc', 'bot', 'twisted', 'plugin'],
    url = 'https://launchpad.net/lalita/',
    classifiers = [
        'Development Status :: 5 - Production/Stable',
        'Environment :: Console',
        'Framework :: Twisted',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License (GPL)',
        'Programming Language :: Python',
        'Topic :: Communications :: Chat :: Internet Relay Chat',
    ],

    # content
    packages = ['lalita', 'lalita.core', 'lalita.core.tests',
                'lalita.core.tests.plugins', 'lalita.plugins',
                'lalita.plugins.randomer_utils', 'lalita.plugins.tests'],
    package_data = {
        'lalita.plugins.randomer_utils': ['#pyar.log'],
    },

    # scripts
    scripts = ['lalita/ircbot.py'],

    # dependencies
    requires = [
        'twisted',
        'beautifulsoup',
        'chardet',
    ],
)
