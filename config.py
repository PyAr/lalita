servers = {
        'perrito':{
            'host' : "10.100.0.164",
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
            'host' : "10.100.0.164",
            'port' : 6667,
            'nickname' : "itchy",
            'channels':{
                'humites':{
                    'plugins': { 'test_side': 'a' }
                    },
                },
            'plugins':{
                'Log': {}
                }
            },
        'testbot-b':{
            'host' : "10.100.0.164",
            'port' : 6667,
            'nickname' : "scratchy",
            'channels':{
                'humites':{
                    'plugins': { 'test_side': 'b' }
                    },
                },
            'plugins':{
                'Log': {}
                }
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
                }
        }
