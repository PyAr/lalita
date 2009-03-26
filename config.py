# -*- coding: utf8 -*-

servers = {
        'localhost': dict (
            encoding='utf8',
            host='127.0.0.1', port=6667,
            nickname='examplia',
            channels= {
                '#humites': dict(plugins={}),
            },
            plugins= {
                'url.Url': { },
                'seen,Seen': { },
            },
        ),
        'example': dict (
            encoding='utf8',
            host='10.100.0.156', port=6667,
            nickname='examplia',
            channels= {
                '#humites': dict(plugins={}),
            },
            plugins= {
                'example.Example': { },
            },
        ),
        'freenode': dict (
            encoding='utf8',
            host='irc.freenode.net', port=6667,
            nickname='lalita',
            channels= {
                '#not-grulic': dict (plugins={
                    'url.Url': { },
                    'seen,Seen': { },
                }),
                '#pyar': dict (plugins={
                    'url.Url': { },
                    'seen,Seen': { },
                }),
            },
            plugins= {
                'register.Register': { 'password': 'zaraza' },
            },
        ),
        'perrito':{
            'encoding': 'utf8',
            'host' : "10.100.0.156",
            'port' : 6667,
            'nickname' : "morelia",
            'channels':{
                '#humites':{
                    'plugins':{
                        'url.Url': dict (
                            database= 'url_public',
                        ),
                        'seen.Seen': {},
                    },
                    'encoding': 'utf8',
                    },
                '#perrites':{
                    'encoding': 'utf8',
                    'plugins':{
                        'url.Url': dict (
                            database= 'url_perrites_private',
                        ),
                    },
                    },
                },
            'plugins':{
                'url.Url': dict (
                    database= 'url_public',
                ),
                'seen.Seen': {},
                }
            },
        'testbot-a':{
            'encoding': 'utf8',
            'host' : "10.100.0.175",
            'port' : 6667,
            'nickname' : "itchy",
            'channels':{
                '#humites':{
                    'plugins': {}
                    },
                },
            'plugins':{
                'testbot.TestPlugin': {'other': 'scratchy'}
                },
            'plugins_dir': "./core/tests/plugins",
            },
        'testbot-b':{
            'encoding': 'utf8',
            'host' : "10.100.0.175",
            'port' : 6667,
            'nickname' : "scratchy",
            'channels':{
                '#humites':{
                    'plugins': {}
                    },
                },
            'plugins':{
                'testbot.TestPlugin': {'other':'itchy'}
                },
            'plugins_dir': "./core/tests/plugins",
            },
        'perrito1':{
            'encoding': 'utf8',
            'host' : "10.100.0.194",
            'port' : 6668,
            'nickname' : "lolita",
                'channels':{
                    '#humites':{
                        'plugins':{ 'Log':{} },
                        'encoding': 'utf8',
                        },
                    '#perrites':{
                        'plugins':{ 'Log':{} }
                        }
                    },
                'plugins':{
                    'Log': {}
                    }
                },
        'pyar2':{
            'encoding': 'utf8',
            'host' : "irc.freenode.net",
            'port' : 6667,
            'nickname' : "apu",
            'channels':{
                'pyar':{
                    'plugins':{ 'Log':{} },
                    'encoding': 'utf8',
                    },
                },
            'plugins':{
                'Log': {}
                }
            },
        'javito':{
            'encoding': 'utf8',
            'host' : "10.100.0.156",
            'port' : 6667,
            'nickname' : "manyula",
            'channels':{
                '#humites':{
                    'plugins':{
                        'randomer.Randomer': dict (
                            database= 'url_public',
                        )
                    },
                    'encoding': 'utf8',
                    },
                },
        }
        }
