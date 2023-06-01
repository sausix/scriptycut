# ScriptyCut
Python based video editing tool with simplified syntax approach

# Warning
This project is still in development (by one person) and is not yet ready to use.
I'm working on the optimal rendering method including caching.


# For whom?
Not only for programmers.
But as programmer I experience some native video editors lacking of automation.
Working in timelines is often fiddly: Snapping, zooming, duplicating clips and effects.
May be expensive video software does support subclips, scripts and some automation?
ScriptyCut definitely wants to help!


# Features
- Templating and automation
- Parallel processing and caching on rendering if possible
- Immutable Clips
- "KISAP"? - Keep it simple and pythonic.
- No expensive processing within Python. ffmpeg's internal processing is on priority.
- Not reinventing the wheel. External tools are perfect and keep the project's code small and clean.


# Dependencies
- FFmpeg. Have it installed and reachable via your PATH variable or specifiy the full path to it.
- Optional: Numpy for raw single frame input or processing.


# ToDo
- Encoder interface
- resolution & fps vs. cache?
- Handling different resolutions and fps between clips
- Stream interface for Clip classes
- Transitions with \_\_add__()
- Jupyter integration?
- Docs and tests :-)
- Get community, feedback and love :-)


# Clip ToDo
- FFmpeg base
- Transform
- Filter
- Crossfade
- ClipSequence compare formats
- Time markers, named, typed
- Animation

# Roadmap
- Optional UI managing and helping with the python code.
- Animations (+motion blur)
- Setups for live streaming/conversion?
