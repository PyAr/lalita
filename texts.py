# -*- coding: utf8 -*-
"""
Very basic Internationalization support.

The structure is basically nested dicts:

langs = { 'lang': lang_dict}

lang_dict is also a nested dict, organized as follow, e.g:

es = {
    'module1':{'key':'text'}
    'module2':{'key':'text'}
    }
"""

es = {
    'dispatcher': {
        "no_such_command":u"%s: No existe esa orden!",
        "help":u'"list" para ver las ordenes; "help cmd" para cada uno',
        "empty_commands":u"No hay ninguna orden registrada...",
        "command_not_exist":u"Esa orden no existe...",
        "no_docs":u"No tiene documentación, y yo no soy adivina...",
        "several_methods":u"Hay varios métodos para esa orden:",
        "no_commands_registered":u"Decí alpiste, no hay ordenes todavía...",
        "commands_are":u"Las ordenes son: %s"}
    }

en = {
    'dispatcher':{
        "no_such_command":u"%s: command not found!",
        "help":u'"list" To see the available commands ; "help cmd" for specific command help',
        "empty_commands":u"PANIC! I have no commands!!!",
        "command_not_exist":u"No such command...",
        "no_docs":u"Missing documentation",
        "several_methods":u"Several handlers for the same command:",
        "no_commands_registered":u"No commands available (yet)",
        "commands_are":u"The available commands are: %s"}
    }

langs = {'es':es,
         'en':en}
