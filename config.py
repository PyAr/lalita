servers = {
        'perrito':{
            'host' : "10.100.0.164",
            'port' : 6667,
            'nickname' : "_morelia",
            'channels':{
                'humites':{
                    'modules':{ 'Log':{} }
                    },
                },
            'modules':{
                'Log': {}
                }
            },
        'perrito1':{
            'host' : "10.100.0.194",
            'port' : 6668,
            'nickname' : "lolita",
                'channels':{
                    'humites':{
                        'modules':{ 'Log':{} }
                        },
                    'perrites':{
                        'modules':{ 'Log':{} }
                        }
                    },
                'modules':{
                    'Log': {}
                    }
                }
        }
