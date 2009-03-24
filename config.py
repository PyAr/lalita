servers = {
        'perrito':{
            'encoding': 'utf8',
            'host' : "10.100.0.175",
            'port' : 6667,
            'nickname' : "_morelia",
            'channels':{
                'humites':{
                    'plugins':{ 'Log':{} },
                    'encoding': 'utf8',
                    },
                },
            'plugins':{
                'Log': {}
                }
            },
        'testbot-a':{
            'encoding': 'utf8',
            'host' : "10.100.0.175",
            'port' : 6667,
            'nickname' : "itchy",
            'channels':{
                'humites':{
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
                'humites':{
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
                    'humites':{
                        'plugins':{ 'Log':{} },
                        'encoding': 'utf8',
                        },
                    'perrites':{
                        'plugins':{ 'Log':{} }
                        }
                    },
                'plugins':{
                    'Log': {}
                    }
                },
        'javito':{
            'encoding': 'utf8',
            'host' : "10.100.0.175",
            'port' : 6667,
            'nickname' : "manyula",
            'channels':{
                'humites':{
                    'plugins':{ 'Log':{} , 'moin_search.MoinSearch': {'fruta': 'banana'}},
                    'encoding': 'utf8',
                    },
                'perrites':{
                    'plugins':{ 'Log':{'arbol':5} },
                    'encoding': 'utf8',
                    }
                },
            'plugins':{
                    'Log': {}
                    }
                }
        }
