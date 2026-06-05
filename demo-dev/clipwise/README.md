# Clipwise Demo

Product demo recording for Zici using [clipwise](https://www.npmjs.com/package/clipwise).

## Requirements

- Node.js 18+
- `npm install` (clipwise is a dev dependency)
- Dev stack running: `./dev.sh start`

## Regenerate narration audio

```bash
# Generate and time-stretch to match video duration
say -v Samantha -r 170 "$(cat demo-dev/clipwise/narration.txt)" -o /tmp/narration.aiff
ffmpeg -y -i /tmp/narration.aiff -codec:a libmp3lame -qscale:a 2 demo-dev/artifacts/narration.mp3

# Get video duration first (record without audio), then stretch:
# VIDEO_DUR=$(ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 demo-dev/artifacts/clipwise-recording.mp4)
# AUDIO_DUR=$(ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 demo-dev/artifacts/narration.mp3)
# TEMPO=$(echo "scale=4; $AUDIO_DUR / $VIDEO_DUR" | bc)
# ffmpeg -y -i demo-dev/artifacts/narration.mp3 -filter:a "atempo=$TEMPO" demo-dev/artifacts/narration-synced.mp3
```

## Record

```bash
npx clipwise record demo-dev/clipwise/scenario.yaml -f mp4 -o ./demo-dev/artifacts
```

Output: `demo-dev/artifacts/clipwise-recording.mp4`
