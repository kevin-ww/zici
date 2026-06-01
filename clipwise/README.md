# Clipwise Demo

Product demo recording for Zici using [clipwise](https://www.npmjs.com/package/clipwise).

## Requirements

- Node.js 18+
- `npm install` (clipwise is a dev dependency)
- Dev stack running: `./dev.sh start`

## Regenerate narration audio

```bash
# Generate and time-stretch to match video duration
say -v Samantha -r 170 "$(cat clipwise/narration.txt)" -o /tmp/narration.aiff
ffmpeg -y -i /tmp/narration.aiff -codec:a libmp3lame -qscale:a 2 artifacts/narration.mp3

# Get video duration first (record without audio), then stretch:
# VIDEO_DUR=$(ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 artifacts/clipwise-recording.mp4)
# AUDIO_DUR=$(ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 artifacts/narration.mp3)
# TEMPO=$(echo "scale=4; $AUDIO_DUR / $VIDEO_DUR" | bc)
# ffmpeg -y -i artifacts/narration.mp3 -filter:a "atempo=$TEMPO" artifacts/narration-synced.mp3
```

## Record

```bash
npx clipwise record clipwise/scenario.yaml -f mp4 -o ./artifacts
```

Output: `artifacts/clipwise-recording.mp4`
