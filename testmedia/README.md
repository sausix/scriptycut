ffmpeg -f lavfi -i testsrc=duration=10:size=1280x720:rate=30 -preset slow -crf 22 x264-720p30.mkv 
ffmpeg -f lavfi -i testsrc=duration=10:size=1920x1080:rate=60 -preset slow -crf 22 x264-1080p60.mkv
