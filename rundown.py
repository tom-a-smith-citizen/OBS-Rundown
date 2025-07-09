# -*- coding: utf-8 -*-
"""
Created on Tue Jul  8 10:00:31 2025

@author: TOSmith
"""

import time
from obswebsocket import obsws, requests

class Rundown(object):
    def __init__(self, name: str, date: str, ws):
        self.name = name
        self.date = date
        self.ws = ws
        self.ws.connect()
        self.queue = []
        
    def preview(self,name):
        self.ws.call(requests.SetCurrentPreviewScene(sceneName=name))
        
    def program(self,name):
        self.ws.call(requests.SetCurrentProgramScene(sceneName=name))
        
    def add(self,slug,scene,lower_third):
        self.queue.append(RundownLine(self,slug,scene,lower_third))
        
class RundownLine(Rundown):
    def __init__(self, parent, slug, scene, lower_third):
        self.parent = parent
        self.slug = slug
        self.scene = scene
        self.lower_third = lower_third
        
    def preview(self):
        self.parent.preview(self.scene)
        
    def program(self):
        self.parent.program(self.scene)
        
if __name__ == "__main__":
    host = "10.10.1.29"
    port = 4455
    password = "XdwGltOUzfaC8VvB"
    ws = obsws(host,port,password)
    rundown = Rundown("Test Rundown",
                      "07-08-2025",
                      ws)
    rundown.add("GR Shooting", "Scene 1", "SHOOTING IN DOWNTOWN GR")
    rundown.add("GR Shooting", "Scene 2", "SHOOTING IN DOWNTOWN GR")
    '''
    try:
        scenes = ws.call(requests.GetSceneList())
        for s in scenes.getScenes():
            name = s['sceneName']
            print("Switching to {}".format(name))
            ws.call(requests.SetCurrentProgramScene(sceneName=name))
            time.sleep(2)
        print("EOL")
    except KeyboardInterrupt:
        pass
    '''
    for line in rundown.queue:
        line_number = rundown.queue.index(line)
        try:
            rundown.queue[line_number+1].preview()
        except IndexError:
            pass
        line.program()
        input("Press enter to continue...")
    ws.disconnect()