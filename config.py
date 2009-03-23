servers = {
        'perrito':{
            'host' : "10.100.0.175",
            'port' : 6667,
            'nickname' : "_morelia",
            'channels':{
                'humites':{
                    'plugins':{ 'Log':{} }
                    },
                },
            'plugins':{
                'Log': {}
                }
            },
        'testbot-a':{
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
            'host' : "10.100.0.194",
            'port' : 6668,
            'nickname' : "lolita",
                'channels':{
                    'humites':{
                        'plugins':{ 'Log':{} }
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
            'host' : "10.100.0.175",
            'port' : 6667,
            'nickname' : "manyula",
            'channels':{
                'humites':{
                    'plugins':{ 'Log':{} , 'moin_search.MoinSearch': {'fruta': 'banana'}}
                    },
                'perrites':{
                    'plugins':{ 'Log':{'arbol':5} }
                    }
                },
            'plugins':{
                    'Log': {}
                    }
                }
        }
