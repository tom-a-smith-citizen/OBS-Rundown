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
import platform
import requests

class OBS(object):
    def __init__(self, parent, host, port, password):
        self.parent = parent
        self.host = host
        self.port = port
        self.password = password
    
    def connect(self,event):
        print(f"Connecting to {self.host}:{self.port}")
        self.cl = obs.ReqClient(host=self.host,port=int(self.port),password=self.password,timeout=3)
        self.cl_events = obs.EventClient(host=self.host,port=int(self.port),password=self.password,timeout=3)
        self.cl_events.callback.register(self.on_scene_list_changed)
        self.cl_events.callback.register(self.on_scene_transition_ended)
        self.parent.grid_panel.set_scene_choices()
        self.parent.grid_panel.set_transition_choices()
    
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
        try:
            resp = self.cl.get_scene_list()
            scenes = [di.get("sceneName") for di in reversed(resp.scenes)]
            return scenes
        except Exception as e:
            print("Couldn't load scene list:", e)
            return []
    
    def get_transition_list(self):
        try:
            resp = self.cl.get_scene_transition_list()
            transitions = resp.transitions
            transitions = [di.get("transitionName") for di in reversed(transitions)]
            return transitions
        except Exception as e:
            print("Couldn't load transition list:",e)
            return []

    def get_visible_items(self):
        resp = self.cl.get_current_program_scene()
        name = resp.scene_name
        items = self.cl.get_scene_item_list(name).scene_items
        output = {}
        for x in items:
            output[x['sourceName']] = {'id': x['sceneItemId'],
                                       'enabled': x['sceneItemEnabled']}
        return output
    
    def toggle_item(self, event, k, v, enabled):
        self.cl.set_current_preview_scene(self.cl.get_current_program_scene().scene_name)
        self.cl.set_scene_item_enabled(self.cl.get_current_program_scene().scene_name,v,enabled)
        self.cl.trigger_studio_mode_transition()
        self.parent.grid_panel.grid.SetFocus()
        

class GUI(wx.Frame):
    def __init__(self,title,obs_connection,super_endpoint):
        super().__init__(parent=None,title=title)
        self.Bind(wx.EVT_CLOSE,self.on_close)
        self.super_endpoint = super_endpoint
        self.obs_connection = obs_connection
        self.obs_conn = OBS(self,obs_connection[0],obs_connection[1],obs_connection[2])
        self.ribbon_panel = Ribbon(self)
        self.grid_panel = Grid(self)
        self.build_menubar()
        self.CreateStatusBar(1)
        self.SetStatusText("Ready.")
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.ribbon_panel)
        sizer.Add(self.grid_panel, 1, wx.EXPAND)
        self.SetSizer(sizer)
        self.Bind(wx.EVT_SIZE,self.grid_panel.auto_resize_columns)
        self.Layout()
        self.Show()
        
    def return_focus(self,func):
        def wrapper():
            func()
            self.grid_panel.SetFocus()
        return wrapper
        
    def on_close(self, event):
        try:
            if not os.path.isdir("data/settings"):
                os.makedirs("data/settings")
            with open("data/settings/obs_settings.json", "w") as file:
                settings = {"host": self.obs_conn.host,
                            "port": self.obs_conn.port,
                            "password": self.obs_conn.password}
                json.dump(settings,file)
                print("Json saved.")
        except Exception as e:
            print("Error dumping json settings to file:", e)
        try:
            if not os.path.isdir("data/settings"):
                os.makedirs("data/settings")
            with open("data/settings/super_endpoint.json","w") as file:
                settings = {"endpoint": self.super_endpoint}
                json.dump(settings,file)
                print("Json saved.")
        finally:
            self.Destroy()
            
    def build_menubar(self):
        menubar = wx.MenuBar()
        
        file = wx.Menu()
        new = file.Append(wx.ID_ANY,"New","New Rundown")
        self.Bind(wx.EVT_MENU, self.on_new, new)
        
        
        menubar.Append(file,"File")
        
        self.SetMenuBar(menubar)
        
    def on_new(self, event):
        GUI("OBS Rundown",(self.obs_connection[0],self.obs_connection[1],self.obs_connection[2]),self.super_endpoint)
        

class Ribbon(wx.Panel):
    def __init__(self, parent):
        super().__init__(parent=parent)
        self.parent = parent
        self.sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.is_playing = False
        self.load_bitmaps()
        self.SetSizer(self.sizer)
        self.Layout()
            
    def load_bitmaps(self):
        sys_appearance = wx.SystemSettings.GetAppearance()
        if sys_appearance.IsDark() and platform.system() != "Windows":
            self.directory = "./data/icons/dark"
        else:
            self.directory = "./data/icons/light"
        self.button_play = wx.BitmapButton(self, bitmap=wx.Bitmap(os.path.join(self.directory,"play.png"),wx.BITMAP_TYPE_PNG))
        self.button_play.Bind(wx.EVT_BUTTON,self.on_play)
        self.sizer.Add(self.button_play,1,wx.ALL)
        self.button_settings = wx.BitmapButton(self, bitmap=wx.Bitmap(os.path.join(self.directory,"settings-sliders.png"),wx.BITMAP_TYPE_PNG))
        self.button_settings.Bind(wx.EVT_BUTTON,self.on_settings)
        self.sizer.Add(self.button_settings,1,wx.ALL)
        self.button_new = wx.BitmapButton(self, bitmap=wx.Bitmap(os.path.join(self.directory,"add-document.png"),wx.BITMAP_TYPE_PNG))
        self.button_new.Bind(wx.EVT_BUTTON,self.parent.on_new)
        self.sizer.Add(self.button_new,1,wx.ALL)
        self.button_open = wx.BitmapButton(self, bitmap=wx.Bitmap(os.path.join(self.directory,"open.png"),wx.BITMAP_TYPE_PNG))
        self.button_open.Bind(wx.EVT_BUTTON, self.on_open)
        self.sizer.Add(self.button_open,1,wx.ALL)
        self.button_save = wx.BitmapButton(self, bitmap=wx.Bitmap(os.path.join(self.directory,"save.png"),wx.BITMAP_TYPE_PNG))
        self.button_save.Bind(wx.EVT_BUTTON,self.on_save)
        self.sizer.Add(self.button_save,1,wx.ALL)
        self.button_refresh = wx.BitmapButton(self, bitmap=wx.Bitmap(os.path.join(self.directory,"refresh.png"),wx.BITMAP_TYPE_PNG))
        self.button_refresh.Bind(wx.EVT_BUTTON, self.on_refresh)
        self.sizer.Add(self.button_refresh,1,wx.ALL)
        self.button_visible = wx.BitmapButton(self, bitmap=wx.Bitmap(os.path.join(self.directory,"eye.png"),wx.BITMAP_TYPE_PNG))
        self.button_visible.Bind(wx.EVT_BUTTON,self.on_visible)
        self.sizer.Add(self.button_visible,1,wx.ALL)
        
    def on_play(self,event):
        self.is_playing = not self.is_playing
        if self.is_playing:
            print("Now Playing...")
            self.button_play.SetBitmap(wx.Bitmap(os.path.join(self.directory,"stop.png"),wx.BITMAP_TYPE_PNG))
            self.parent.obs_conn.connect(wx.Event)
        else:
            print("Stopped.")
            self.button_play.SetBitmap(wx.Bitmap(os.path.join(self.directory,"play.png"),wx.BITMAP_TYPE_PNG))
        self.parent.grid_panel.grid.SetFocus()
        
    def on_settings(self,event):
        SettingsUI(self.parent)
        
    def on_open(self, event):
        with wx.FileDialog(self, "Open rundown", wildcard="JSON files (*.json)|*.json",defaultDir="./saved_rundowns",
                           style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as fileDialog:
            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return
            pathname = fileDialog.GetPath()
            try:
                self.parent.grid_panel.load_rundown(pathname)
            except IOError:
                wx.LogError(f"Cannot open file '{pathname}'.")

    def on_save(self,event):
        with wx.FileDialog(self, "Save rundown", wildcard="JSON files (*.json)|*.json", defaultDir="./saved_rundowns",style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT) as fileDialog:
            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return     # the user changed their mind
            # save the current contents in the file
            pathname = fileDialog.GetPath()
            try:
                self.parent.grid_panel.save_rundown(wx.Event, pathname)
            except IOError:
                wx.LogError("Cannot save current data in file '%s'." % pathname)
                
    def on_refresh(self,event):
        self.parent.grid_panel.set_scene_choices()
        self.parent.grid_panel.set_transition_choices()
   
    def on_visible(self, event):
        button = event.GetEventObject()
        screen_pos = button.GetScreenPosition()
        button_size = button.GetSize()

        # Convert to coordinates relative to this panel (self)
        client_pos = self.ScreenToClient(screen_pos)

        menu_x = client_pos.x
        menu_y = client_pos.y + button_size.height  # just below the button
        
        items = self.parent.obs_conn.get_visible_items()
        self.PopupMenu(VisiblityPopupMenu(self, items), menu_x, menu_y)

    
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
    
    def save_rundown(self, event, filename):
        rundown = {}
        for row in range(self.grid.GetNumberRows()):
            rundown[str(row)] = {
                'slug': self.grid.GetCellValue(row, 0),
                'super': self.grid.GetCellValue(row, 1),
                'scene': self.grid.GetCellValue(row, 2),
                'transition': self.grid.GetCellValue(row, 3),
                }
        if not os.path.isdir("./saved_rundowns"):
            os.makedirs("./saved_rundowns")
        with open(filename, "w") as file:
            json.dump(rundown, file, indent=2)
            print(f"Saved rundown to {filename}")
    
    def load_rundown(self, filename):
        try:
            with open(filename, "r") as file:
                rundown = json.load(file)

            self.grid.ClearGrid()
            existing_rows = self.grid.GetNumberRows()
            needed_rows = len(rundown)

            if needed_rows > existing_rows:
                self.grid.AppendRows(needed_rows - existing_rows)
            elif needed_rows < existing_rows:
                self.grid.DeleteRows(0, existing_rows - needed_rows)

            for row_str, data in rundown.items():
                row = int(row_str)
                self.grid.SetCellValue(row, 0, data.get('slug', ''))
                self.grid.SetCellValue(row, 1, data.get('super', ''))
                self.grid.SetCellValue(row, 2, data.get('scene', ''))
                self.grid.SetCellValue(row, 3, data.get('transition', ''))

            self.set_scene_choices()
            self.set_transition_choices()
            self.grid.ForceRefresh()
            print(f"Loaded rundown from {filename}")
        except Exception as e:
            wx.LogError(f"Could not load rundown from file '{filename}': {e}")

    
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
    
    def send_super_text(self,text):
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        data = f"text={text}"
        requests.post(self.parent.super_endpoint,headers=headers,data=data)
    
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
            super_text = self.grid.GetCellValue(green_row,1)
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
            if super_text.strip() != "":
                print(super_text)
                self.send_super_text(super_text)

        else:
            event.Skip()

class SettingsUI(wx.Frame):
    def __init__(self,parent):
        super().__init__(parent=parent, title="Settings")
        self.parent = parent
        self.panel_main = wx.Panel(self)
        self.sizer_main = wx.FlexGridSizer(5,2,10,10)
        self.sizer_buttons = wx.BoxSizer(wx.HORIZONTAL)
        self.label_host = wx.StaticText(self.panel_main,label="Host")
        self.field_host = wx.TextCtrl(self.panel_main)
        self.field_host.SetValue(self.parent.obs_conn.host)
        self.label_port = wx.StaticText(self.panel_main,label="Port")
        self.field_port = wx.TextCtrl(self.panel_main)
        self.field_port.SetValue(str(self.parent.obs_conn.port))
        self.label_password = wx.StaticText(self.panel_main,label="Password")
        self.field_password = wx.TextCtrl(self.panel_main,style=wx.TE_PASSWORD)
        self.field_password.SetValue(self.parent.obs_conn.password)
        self.label_endpoint = wx.StaticText(self.panel_main,label="Super Endpoint")
        self.field_endpoint = wx.TextCtrl(self.panel_main)
        self.field_endpoint.SetValue(self.parent.super_endpoint)
        self.button_apply = wx.Button(self.panel_main,label="Apply")
        self.button_apply.Bind(wx.EVT_BUTTON,self.on_apply)
        self.button_cancel = wx.Button(self.panel_main,label="Cancel")
        self.button_cancel.Bind(wx.EVT_BUTTON,self.on_cancel)
        self.sizer_buttons.AddMany([(self.button_apply,1,wx.ALL),
                                    (self.button_cancel,1,wx.ALL)])
        self.sizer_main.AddMany([(self.label_host,1,wx.ALL|wx.EXPAND),
                                 (self.field_host,1,wx.ALL|wx.EXPAND),
                                 (self.label_port,1,wx.ALL|wx.EXPAND),
                                 (self.field_port,1,wx.ALL|wx.EXPAND),
                                 (self.label_password,1,wx.ALL|wx.EXPAND),
                                 (self.field_password,1,wx.ALL|wx.EXPAND),
                                 (self.label_endpoint,1,wx.ALL|wx.EXPAND),
                                 (self.field_endpoint,1,wx.ALL|wx.EXPAND),
                                 (self.sizer_buttons,1,wx.ALL)])
        self.panel_main.SetSizerAndFit(self.sizer_main)
        self.Layout()
        self.Show()
        
    def on_apply(self, event):
        host = self.field_host.GetValue()
        port = self.field_port.GetValue()
        password = self.field_password.GetValue()
        endpoint = self.field_endpoint.GetValue()
        if host == "" or port == "" or password == "" or endpoint == "":
            dlg = wx.MessageDialog(self,message="Fields cannot be left empty. Make sure all fields are filled out and try again.",caption="Fields Cannot Be Empty",style=wx.OK|wx.ICON_ERROR)
            dlg.ShowModal()
        else:
            self.parent.obs_conn.host = host
            self.parent.obs_conn.port = port
            self.parent.obs_conn.password = password
            self.parent.super_endpoint = endpoint
        self.Destroy()
            
            
    def on_cancel(self, event):
        self.Destroy()

class VisiblityPopupMenu(wx.Menu):
    def __init__(self, parent, items):
        super().__init__()
        self.parent = parent
        self.build_items(items)

    def build_items(self, items):
        for key, value in items.items():
            item = self.Append(wx.ID_ANY, key, kind=wx.ITEM_CHECK)
            item.Check(value['enabled'])
            self.Bind(
                wx.EVT_MENU,
                lambda evt, k=key, v=value['id'], enabled=not value['enabled']: self.parent.parent.obs_conn.toggle_item(evt, k, v, enabled),
                id=item.GetId()  # ✅ Correctly bind to the item's ID
            )
        
def load_obs_settings():
    if os.path.isfile("data/settings/obs_settings.json"):
        with open("data/settings/obs_settings.json","r") as file:
            settings = json.load(file)
            obs_connection = (settings['host'],int(settings['port']),settings['password'])
            return obs_connection
    else:
        return ("localhost", 4455, "password")
    
def load_super_endpoint():
    if os.path.isfile("data/settings/super_endpoint.json"):
        with open("data/settings/super_endpoint.json","r") as file:
            settings = json.load(file)
            super_endpoint = settings['endpoint']
            return super_endpoint
    else:
        return "N/A"
        
if __name__ == "__main__":
    obs_connection = load_obs_settings()
    super_endpoint = load_super_endpoint()
    app = wx.App()
    frame = GUI("OBS Rundown",obs_connection,super_endpoint)
    app.MainLoop()