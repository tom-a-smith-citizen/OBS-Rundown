# -*- coding: utf-8 -*-
"""
Created on Tue Jul 15 08:14:36 2025

@author: TOSmith
"""

import obsws_python as obs

cl = obs.ReqClient(host="10.10.1.29",port=4455,password="newstar")
audio_inputs = cl.get_input_list('wasapi_input_capture').inputs
special_sources = cl.get_special_inputs()
global_sources = special_sources.__dict__
sources_output = {}
for key, value in global_sources.items():
    if key != "attrs" and key[0:2] != "__":
        sources_output[key] = {'global': True,
                               'name': value,
                               'UUID': None}

for x in audio_inputs:
        sources_output[x['inputUuid']] = {'global': False,
                               'name': x['inputName'],
                               'UUID': x['inputUuid']}
    
for _input in sources_output:
    print(_input)


for key, value in sources_output.items():
    if sources_output[key]['name'] is not None:
        level = cl.get_input_volume(sources_output[key]['name']).input_volume_db
        print(f"{sources_output[key]['name']}: {level} dB")