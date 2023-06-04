# ScriptyCut
Python based video editing tool with simplified syntax approach


# Warning
This project is still in development (currently by one person) and is not yet ready to use.
I'm working on the optimal rendering method including caching.
Calls to FFmpeg not yet implemented.


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


# Example lines
```python
# Syntax preview. May change in near future a little.

# Static video files
intro = FileClip("intro.mpv")
outro = FileClip("outro.mpv")

# Images
agenda = ImageFromFile("agenda-2023.png")

# Project files
main_video = FileClip("Rick Sanchez - Always Gonna Give You Up.mp4", master=True)


def make_video_as_always(pre_image: Image, main: Clip) -> Clip:
    """
    Helper function to compose a full video.
    Just add the main clip
    """

    all_clips = intro + Crossfade(duration=1) + ImageClip(pre_image, 2.) + main + Crossfade(duration=1) + outro
    # You can also use lists and sum() to concatenate clips.
    
    # Match all formats of each Clip to the same format.
    # Scale resolutions to match the main clip.
    return all_clips.match_formats(from_master=True)


# Compose full video with a helper function
final_video = make_video_as_always(agenda, main_video)

# Render
final_video.render("final.mkv")
```

# Dependencies
- FFmpeg. Have it installed and reachable via your PATH variable or specifiy the full path to it.
- ImageIO: Basic images in and out
- Optional: Numpy for raw single frame input or processing.


# But MoviePy?
I've seen MoviePy of course. Looks a little unmaintained and messy.   
Their Code:
- A lot of issues. Code issues! Opening the project in PyCharm reveils a lot. 
- No typing and annotations. Your IDE can't help finding functions and give code completion.
- Hacky ways of implanting functions in classes
- Crazy decorators (doesn't make things easier at a point)
- Duplicating and modifying clips is unnecessary in a programming context

Problems for their users:
- Documentation is incomplete and inconsistent.
- Missing cool pythonic language features.
- A lot of handling with lists.
- Using NumPy for effects is probably slower than using the same effect shipped with FFmpeg.


# ToDo
- Encoder interface
- resolution & fps vs. cache?
- Stream interface for Clip classes
- Transitions with \_\_add__()
- Jupyter integration?
- Docs and tests :-)
- Get community, feedback and love :-)
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
