# Throne Roofing: drone story reel

Final video: `deliverables/throne_roofing_drone_story.mp4` (1080x1920 vertical, 30 fps, 46.6 s, AAC 48 kHz, -15 LUFS).
Made for YouTube Shorts, Instagram Reels and TikTok.

Reference: "Roof Transformation Timelapse Canada" (Skyluxe Roofing). It is a top-down drone
timelapse of a flat commercial roof going from old membrane to tear-off to new cap sheet.

## Story (6 acts)

| Time | Shot | Voiceover / on-screen text | Sound |
|---|---|---|---|
| 0.0 to 4.0 | Drone tilt-down over a Calgary neighbourhood (real Throne photo) with drone HUD (REC, altitude) | "Every roof tells a story." | Drone rotor hum, wind, soft piano and pad |
| 4.0 to 9.6 | Whip-pan to a top-down view. The drone descends and rotates over the old roof, ending close on ponding and cracks | "Years of Calgary hail, wind & snow" / "Until it couldn't take any more." | Hum fading, piano in D minor |
| 9.6 to 13.0 | Crew on the roof, then the torch kit (real photos) | "So our crew went to work." | Whoosh, torch roar, riser |
| 13.0 to 27.4 | 3-day top-down timelapse: DAY 1 tear-off, DAY 2 base sheet torched on, DAY 3 torch-on cap sheet. Crew, torch glow, material pallets, a filling dumpster, cars changing each day, sun shadows sweeping, cloud shadows, a night dip between days | "Tear-off." / "Base sheet." / "Torch-on cap." | Drop with impact. Kick, bass and hats build up each day. Scraping on day 1, torch on days 2 and 3 |
| 27.4 to 33.4 | Quick detail cuts on the beat: torch on base, vent flashing, skylight, membrane seams, vents (real photos) | "Sealed tight." / "Every seam. Every vent. Every flashing." | Punch-in impact, claps, swishes |
| 33.4 to 39.4 | Reveal with a white flash: finished roofs, with stats counting up (90+ commercial, 100 residential, 30 crew, 300 happy customers) | "BUILT TO LAST" | Big impact, full beat, count ticks |
| 39.4 to 46.6 | End card: logo, "BUILT TO RULE.", services, cities, FREE QUOTE, (587) 701-1400, throneroofing.ca | "Throne Roofing. Built to rule." | Final hit, sub drop, shimmer |

All content comes from throneroofing.ca: services, service areas, stats, phone number, safety and
WCB lines, logo and the 16+ real project photos.

## Edit techniques
- **Drone motion on stills:** eased push-ins and pulls, lateral slides, and a small hover drift and roll, so each photo moves like gimbal footage.
- **Timelapse feel:** the crew jumps between positions every frame, exposure flickers slightly, the sun swings from morning to evening each day, and the frame dips toward night between days.
- **Transitions:** whip-pans with directional motion blur (4.0 s, 9.6 s, 13.0 s), hard cuts on the beat (100 BPM grid), a punch-in on the drop, a white flash on the reveal and a dip to black before the end card.
- **Colour:** one LUT across every shot (S-curve, warm highlights and cool shadows, +8% saturation), plus a lens vignette and film grain, so real photos and CG frames look like they came from the same camera.
- **Text:** Inter ExtraBold with a soft shadow, red pill kickers in the brand colour (#BA1F27), slide-up and fade animation, and placement clear of the Shorts and Reels UI areas.

## Sound design
- Voiceover: Higgsfield `seed_audio`, voice "Barrett". Each phrase is cut by silence detection and placed on its beat. Processing: EQ, then compression, then a light room reverb.
- Score: all synthesised. D minor (Dm, Bb, F, C) at 100 BPM, with one chord per timelapse day. Pad, piano arpeggios, sidechained bass, kick, clap and hats.
- SFX: all synthesised. Four-rotor drone hum, wind, torch roar with crackle, scraping, whooshes, risers, impacts, a logo shimmer and count ticks.
- Mix: the music ducks about 7 dB under the voice. Mastered with loudnorm and a limiter to about -15 LUFS integrated and -1.4 dB true peak.

## Rebuild
```bash
pip install numpy pillow scipy
python3 make_audio.py vo.wav mix.wav
python3 make_video.py <photos_dir> out_part.mp4 <start_frame> <end_frame>
```
`roofsim.py` contains the procedural top-down roof simulation.
