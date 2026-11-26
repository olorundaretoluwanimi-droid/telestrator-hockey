#!/bin/sh
# THE SLOT — "Bookends". One command from the project folder: clips → voice → timeline → mix → master → subtitles.
# The picture renders on GitHub (render.yml, the finished film is the run's artifact); never render the whole film locally.
set -e
LIB=${LIB:-/c/Users/HP/lemo-opuscar}; export LIB
HERE=$(cd "$(dirname "$0")" && pwd); cd "$HERE"
PY="$LIB/.venv/Scripts/python.exe"; [ -x "$PY" ] || PY="$LIB/.venv/bin/python"
# source (CC BY, see CREDITS): .venv/Scripts/yt-dlp -f 298 -o raw/umb_psu_video.mp4 eLQLqgMSW2w ; -f 140-5 -o raw/umb_psu_audio.m4a
python -I tools/make_timeline.py                  # segments, clips, goals, voice cues → timeline.json
python -I tools/cut_clips.py                      # raw → raw/clips/*.mp4 (what the render machine preps into frames)
# voice (AI33 credits): python -I ../tools/tts_ai33.py lines audio/lines.json audio/vo_raw
"$PY" tools/clean_vo.py audio/vo_raw audio/vo
"$PY" -c "import json,glob,os,soundfile as sf;json.dump({os.path.basename(f)[:-4]:round(sf.info(f).duration,3) for f in glob.glob('audio/vo/v*.wav')},open('audio/vo/dur.json','w'))"
python -I tools/make_timeline.py
"$PY" tools/homography.py                         # rink feet ↔ the 280.7 s frame → assets/rink.json
python -I tools/fonts.py
ffmpeg -v error -y -i raw/umb_psu_audio.m4a -ac 2 -ar 48000 audio/orig.wav
"$PY" tools/mix.py                                # → out/mix.wav
sh tools/master.sh                                # → audio/master/soundtrack.m4a.part* (−14 LUFS)
python -I tools/cues.py && "$PY" "$LIB/core/render/srt.py" audio/cues.json subtitles_en.srt
# checks: (cd $LIB && node core/render/readcheck.mjs "$HERE")
# stills: "$PY" tools/prep.py --times <src,…> then (cd $LIB && node core/render/still.mjs "$HERE" <t> …)
# render: gh workflow run render.yml
