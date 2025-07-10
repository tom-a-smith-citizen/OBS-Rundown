# -*- coding: utf-8 -*-
"""
OBS-Rundown GUI
Created on Tue Jul  8 10:18:43 2025

@author: TOSmith
"""

import wx
import wx.grid as gridlib
import obsws_python as obs
import os
import json
from PIL import Image, ImageOps

class OBS(object):
    def __init__(self, parent, host, port, password):
        self.parent = parent
        self.host = host
        self.port = port
        self.password = password
    
    def connect(self,event):
        self.cl = obs.ReqClient(host=self.host,port=self.port,password=self.password,timeout=3)
        self.cl_events = obs.EventClient(host=self.host,port=self.port,password=self.password,timeout=3)
        self.cl_events.callback.register(self.on_scene_list_changed)
        self.cl_events.callback.register(self.on_scene_transition_ended)
    
    def on_scene_list_changed(self, event):
        print("Scene list changed.")
        self.parent.grid_panel.set_scene_choices()
        
    def on_scene_transition_ended(self, event):
        print("Transition finished.")
        for row in range(self.parent.grid_panel.grid.GetNumberRows()):
            color = self.parent.grid_panel.grid.GetCellBackgroundColour(row, 0)
            if color == wx.Colour(0, 255, 0):  # Green
                green_row = row
                break
        name = self.parent.grid_panel.grid.GetCellValue(green_row,2)
        transition = self.parent.grid_panel.grid.GetCellValue(green_row,3)
        if transition == "":
            print("Transition not set, using cut.")
            transition = "Cut"
        self.cl.set_current_preview_scene(name)
        self.cl.set_current_scene_transition(transition)
     
    def get_scene_list(self):
        resp = self.cl.get_scene_list()
        scenes = [di.get("sceneName") for di in reversed(resp.scenes)]
        return scenes
    
    def get_transition_list(self):
        resp = self.cl.get_scene_transition_list()
        transitions = resp.transitions
        transitions = [di.get("transitionName") for di in reversed(transitions)]
        return transitions

class GUI(wx.Frame):
    def __init__(self,title,obs_connection):
        super().__init__(parent=None,title=title)
        self.Bind(wx.EVT_CLOSE,self.on_close)
        self.obs_connection = obs_connection
        if obs_connection is not None:
            self.obs_conn = OBS(self,obs_connection[0],obs_connection[1],obs_connection[2])
        self.ribbon_panel = Ribbon(self)
        self.grid_panel = Grid(self)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.ribbon_panel)
        sizer.Add(self.grid_panel, 1, wx.EXPAND)
        self.SetSizer(sizer)
        self.Bind(wx.EVT_SIZE,self.grid_panel.auto_resize_columns)
        self.Layout()
        self.Show()
        
    def on_close(self, event):
        try:
            if not os.path.isdir("data/settings"):
                os.makedirs("data/settings")
            with open("data/settings/obs_settings.json", "w") as file:
                settings = {"host": self.obs_connection[0],
                            "port": self.obs_connection[1],
                            "password": self.obs_connection[2]}
                json.dump(settings,file)
        except Exception as e:
            print("Error dumping json settings to file:", e)
        finally:
            self.Destroy()

class Ribbon(wx.Panel):
    def __init__(self, parent):
        super().__init__(parent=parent)
        self.parent = parent
        self.sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.load_bitmaps()
        self.SetSizer(self.sizer)
        self.Layout()
        
    def load_bitmaps(self):
        sys_appearance = wx.SystemSettings.GetAppearance()
        if sys_appearance.IsDark():
            filenames = ["./data/icons/dark/add-document.png", "./data/icons/dark/play.png", "./data/icons/dark/refresh.png", "./data/icons/dark/settings-sliders.png", "./data/icons/dark/stop.png"]
        else:
            filenames = ["./data/icons/light/add-document.png", "./data/icons/light/play.png", "./data/icons/light/refresh.png", "./data/icons/light/settings-sliders.png", "./data/icons/light/stop.png"]
        for fname in filenames:
            bitmap = wx.Bitmap(fname, wx.BITMAP_TYPE_PNG)
            button = wx.BitmapButton(self, bitmap=bitmap)
            self.sizer.Add(button, 1, wx.ALL | wx.EXPAND, 5)
        
class Grid(wx.Panel):
    def __init__(self,parent):
        super().__init__(parent=parent)
        self.parent = parent
        self.Bind(wx.EVT_KEY_DOWN, self.on_key_down)
        self.Bind(gridlib.EVT_GRID_LABEL_RIGHT_CLICK,self.on_label_right_click)
        self.Bind(gridlib.EVT_GRID_CELL_CHANGED,self.auto_resize_columns)
        self.grid = gridlib.Grid(self)
        self.grid.CreateGrid(5,4)
        self.grid.SetColLabelValue(0,"SLUG")
        self.grid.SetColLabelValue(1,"SUPER")
        self.grid.SetColLabelValue(2,"SCENE")
        self.grid.SetColLabelValue(3,"TRANSITION")
        self.set_scene_choices()
        self.set_transition_choices()
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.grid,1,wx.ALL|wx.EXPAND)
        self.SetSizer(sizer)
        self.highlight_row(0, wx.Colour(0, 255, 0))  # Green
        self.grid.SetFocus()
    
    def auto_resize_columns(self, event=None):
        total_width = self.grid.GetSize().width
        col_count = self.grid.GetNumberCols()

        for col in range(col_count):
            self.grid.SetColSize(col, total_width // col_count)

        self.grid.ForceRefresh()

        if event:
            event.Skip()
    
    def highlight_row(self, row, color):
        for col in range(self.grid.GetNumberCols()):
            self.grid.SetCellBackgroundColour(row, col, color)

    def clear_all_highlights(self):
        for row in range(self.grid.GetNumberRows()):
            for col in range(self.grid.GetNumberCols()):
                self.grid.SetCellBackgroundColour(row, col, wx.WHITE)    
     
    def add_row(self):
        row = self.grid.GetNumberRows()
        self.grid.AppendRows(1)
        
        # Optionally, copy column labels or default cell values
        self.grid.SetCellValue(row, 0, "")  # SLUG
        self.grid.SetCellValue(row, 1, "")  # SUPER
        self.grid.SetCellValue(row, 2, "")  # SCENE
        self.grid.SetCellValue(row, 3, "")  # TRANSITION
        
        # Re-apply editors for the new row
        self.set_scene_choices()
        self.set_transition_choices()
        
        self.grid.ForceRefresh()
     
    def set_scene_choices(self):
        if hasattr(self.parent, "obs_conn"):
            new_scene_choices = self.parent.obs_conn.get_scene_list()
            current_selections = {}
            for row in range(self.grid.GetNumberRows()):
                current_value = self.grid.GetCellValue(row, 2)
                current_selections[row] = current_value
            for row in range(self.grid.GetNumberRows()):
                editor = wx.grid.GridCellChoiceEditor(choices=new_scene_choices, allowOthers=False)
                self.grid.SetCellEditor(row, 2, editor)
                self.grid.SetCellValue(row, 2, "")
                if current_selections[row] in new_scene_choices:
                    self.grid.SetCellValue(row, 2, current_selections[row])
            self.grid.ForceRefresh()
        
    def set_transition_choices(self):
        if hasattr(self.parent, "obs_conn"):
            new_transition_choices = self.parent.obs_conn.get_transition_list()
            current_selections = {}
            for row in range(self.grid.GetNumberRows()):
                current_value = self.grid.GetCellValue(row, 3)
                current_selections[row] = current_value
            for row in range(self.grid.GetNumberRows()):
                editor = wx.grid.GridCellChoiceEditor(choices=new_transition_choices, allowOthers=False)
                self.grid.SetCellEditor(row, 3, editor)
                self.grid.SetCellValue(row, 3, "")
                if current_selections[row] in new_transition_choices:
                    self.grid.SetCellValue(row, 3, current_selections[row])
            self.grid.ForceRefresh()
     
    def on_label_right_click(self, event):
        row = event.GetRow()
        try:
            name = self.grid.GetCellValue(row,2)
            self.parent.obs_conn.cl.set_current_preview_scene(name)
        except Exception as e:
            print(e)
        # Optional: Clear existing highlights
        for r in range(self.grid.GetNumberRows()):
            for c in range(self.grid.GetNumberCols()):
                self.grid.SetCellBackgroundColour(r, c, wx.WHITE)

        # Highlight the selected row in yellow
        for col in range(self.grid.GetNumberCols()):
            self.grid.SetCellBackgroundColour(row, col, wx.GREEN)

        self.grid.ForceRefresh()
       
    def on_key_down(self, event):
        code = event.GetKeyCode()
        if event.ControlDown() and code == ord('I'):
            print("Ctrl+I pressed! Adding a row...")
            self.add_row()
            return
        if code == wx.WXK_SPACE:
            print("Spacebar was pressed!")

            red_row = None
            green_row = None

            # Step 1: Identify currently green and red rows
            for row in range(self.grid.GetNumberRows()):
                color = self.grid.GetCellBackgroundColour(row, 0)
                if color == wx.Colour(0, 255, 0):  # Green
                    green_row = row
                elif color == wx.Colour(255, 0, 0):  # Red
                    red_row = row

            #Step 1.5 Set Preview
            name = self.grid.GetCellValue(green_row,2)
            if name != "":
                self.parent.obs_conn.cl.set_current_preview_scene(name)

            # Step 2: Clear all highlights
            self.clear_all_highlights()

            # Step 3: Promote green → red, next → green
            if green_row is not None:
                self.highlight_row(green_row, wx.Colour(255, 0, 0))  # Red

                next_row = green_row + 1
                if next_row >= self.grid.GetNumberRows():
                    next_row = 0
            if next_row < self.grid.GetNumberRows():
                self.highlight_row(next_row, wx.Colour(0, 255, 0))  # Green

            # If there was no green row yet (first press), start at top
            elif red_row is None:
                self.highlight_row(0, wx.Colour(0, 255, 0))  # First green row

            self.grid.ForceRefresh()

            # Trigger OBS transition
            self.parent.obs_conn.cl.trigger_studio_mode_transition()

        else:
            event.Skip()

def load_obs_settings():
    if os.path.isfile("/data/settings/obs_settings.json"):
        with open("/data/settings/settings.json","r") as file:
            settings = json.load(file)
            obs_connection = (settings['obs_conn']['host'],settings['obs_conn']['port'],['obs_settings']['password'])
            return obs_connection
    return None
        
if __name__ == "__main__":
    #obs_connection = ["10.10.1.29", 4455, "XdwGltOUzfaC8VvB"]
    obs_connection = load_obs_settings()
    app = wx.App()
    frame = GUI("OBS Rundown",obs_connection)
    app.MainLoop()