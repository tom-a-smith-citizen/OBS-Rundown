![NROBS Logo](./data/icons/app.png)
# NROBS

## Introduction
NROBS (Newsroom Open Broadcaster Software) is a simple program written in Python3.11 intended to act as a basic rundown and playout software for [OBS](https://obsproject.com/), meant to give professionals in a news environment a more accessible way to produce digital shows in OBS. It connects to OBS via the built in websocket server and controls it using [obsws-python](https://github.com/aatikturk/obsws-python).

## Basic Operation
- Rundowns play out from top to bottom.
- SCENE and TRANSITION columns populate automatically from what's available in OBS. If no TRANSITION is selected, CUT will be used by default.
- Press CTRL + I to add a line to the rundown.
- Play through the rundown by pressing Spacebar. Preview is green, air is red.
- Right click on a row number to jump to that row in preview.
- The eyeball UI icon can be used to toggle scene items on or off in program.
