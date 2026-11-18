#!/bin/bash
set -e
B=/tmp/claude-0/-home-user-usman/17155274-85b6-5c26-9ac5-e4d3e2acc502
S=$B/scratchpad/work; mkdir -p $S; cd $S
IMG=$B/images
V="/root/.claude/uploads/17155274-85b6-5c26-9ac5-e4d3e2acc502/ac293ef8-WhatsApp_Video_2026-11-18_at_6.24.02_PM.mp4"
FB=/usr/share/fonts/opentype/inter/Inter-Black.otf
FX=/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf
FPS=30
ENC="-c:v libx264 -preset medium -crf 17 -pix_fmt yuv420p -r $FPS"
INTRO=12.35
D=1.5      # per photo clip
CARD=2.6

# ---------- 1. Intro: original video, 9:16 with blurred fill ----------
ffmpeg -y -v error -t $INTRO -i "$V" -filter_complex "
[0:v]fps=$FPS,split[a][b];
[a]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,gblur=sigma=40[bg];
[b]scale=1080:-2:flags=lanczos[fg];
[bg][fg]overlay=(W-w)/2:(H-h)/2,setsar=1" -an $ENC intro.mp4

# Grade + grain + vignette + handheld micro-shake, shared by all photo clips
LOOK="eq=contrast=1.10:saturation=1.18:gamma=0.97,colorbalance=bs=0.04:bh=-0.02,unsharp=5:5:0.6,\
scale=1124:1998,crop=1080:1920:x='22+9*sin(t*21)+5*sin(t*37)':y='39+11*sin(t*17+1)+5*sin(t*31)',\
vignette=PI/4.5,noise=alls=7:allf=t,setsar=1"
WM="drawtext=fontfile=$FB:text='THRONE ROOFING':fontsize=40:fontcolor=white@0.9:x=(w-tw)/2:y=110:shadowcolor=black@0.6:shadowx=2:shadowy=2"
FLASH="fade=in:st=0:d=0.18:color=white"

# lower-third style caption: blue bar + white text sliding in
cap() { # $1 line1  $2 line2
  local y=1450
  echo "drawbox=x=0:y=$((y-20)):w='min(iw,iw*(t-0.12)/0.25)':h=150:color=0x1E7FE0@0.92:t=fill:enable='gte(t,0.12)',\
drawtext=fontfile=$FB:text='$1':fontsize=74:fontcolor=white:x='min(60,60-700*(0.4-t)/0.25)':y=$y:enable='gte(t,0.15)',\
drawtext=fontfile=$FX:text='$2':fontsize=38:fontcolor=white@0.95:x='min(62,62-700*(0.45-t)/0.25)':y=$((y+82)):enable='gte(t,0.2)'"
}

N=$(python3 -c "print(int($D*$FPS))")

# Clip 1: landscape wide shot -> slow lateral pan (drone-like) with push in
ffmpeg -y -v error -loop 1 -t $D -framerate $FPS -i $IMG/1.webp -vf "
scale=-2:2400:flags=lanczos,crop=1350:2400:x='(iw-ow)*(0.85-0.55*t/$D)':y=0,scale=1080:1920,
$LOOK,$WM,$(cap '26,500+ SQ FT' 'HOSPITAL ROOF REPLACEMENT'),$FLASH" $ENC c1.mp4

# Clip 2..5: portrait photos -> zoompan on high-res upscale (smooth push / pull)
zp() { # $1 img  $2 out  $3 zoom expr  $4 x expr  $5 y expr  $6 caption1 $7 caption2
  ffmpeg -y -v error -i $IMG/$1 -vf "
crop=ih*9/16:ih,scale=2160:3840:flags=lanczos,
zoompan=z='$3':x='$4':y='$5':d=$N:s=1080x1920:fps=$FPS,
$LOOK,$WM,$(cap "$6" "$7"),$FLASH" -frames:v $N $ENC $2
}
zp 3.webp c2.mp4 "1.0+0.16*on/$N" "iw/2-(iw/zoom/2)+120*on/$N" "ih/2-(ih/zoom/2)" 'FULL TEAR-OFF' 'CREW ON SITE - ROCKY GLEN, SK'
zp 5.webp c3.mp4 "1.22-0.18*on/$N" "iw/2-(iw/zoom/2)" "ih/2-(ih/zoom/2)" 'DOWN TO THE DECK' 'NEW INSULATION LAYER'
zp 4.webp c4.mp4 "1.05+0.15*on/$N" "iw/2-(iw/zoom/2)" "ih*0.55-(ih/zoom/2)" 'NEW MEMBRANE' 'COMMERCIAL GRADE SYSTEM'
zp 2.webp c5.mp4 "1.18-0.14*on/$N" "iw/2-(iw/zoom/2)" "ih/2-(ih/zoom/2)" 'SASKATCHEWAN' 'BUILT BY THRONE ROOFING'

# ---------- Final alert card ----------
ffmpeg -y -v error -loop 1 -t $CARD -framerate $FPS -i $IMG/2.webp -vf "
crop=ih*9/16:ih,scale=1080:1920,gblur=sigma=28,eq=brightness=-0.18:saturation=0.6,
drawbox=x=0:y=0:w=iw:h=ih:color=0x0B4F9E@0.62:t=fill,
drawbox=x=0:y=0:w=iw:h=ih:color=0xFF2A2A@0.22:t=fill:enable='lt(mod(t,0.5),0.12)*lt(t,1.6)',
drawbox=x=90:y=640:w=900:h=10:color=white:t=fill,
drawbox=x=90:y=1270:w=900:h=10:color=white:t=fill,
drawtext=fontfile=$FB:text='⚠ STAY ALERT':fontsize=118:fontcolor=white:x=(w-tw)/2:y=700:alpha='if(lt(t,1.2),gt(mod(t,0.3),0.1),1)',
drawtext=fontfile=$FB:text='SOMETHING BIG':fontsize=96:fontcolor=0xBFE3FF:x=(w-tw)/2:y=880:enable='gte(t,0.35)',
drawtext=fontfile=$FB:text='IS COMING':fontsize=96:fontcolor=0xBFE3FF:x=(w-tw)/2:y=990:enable='gte(t,0.55)',
drawtext=fontfile=$FX:text='by THRONE ROOFING':fontsize=60:fontcolor=white:x=(w-tw)/2:y=1150:enable='gte(t,0.8)',
drawtext=fontfile=$FX:text='26,500+ SQ FT  •  ROCKY GLEN, SK':fontsize=36:fontcolor=white@0.85:x=(w-tw)/2:y=1330:enable='gte(t,1.0)',
noise=alls=6:allf=t,vignette=PI/5,setsar=1,$FLASH" $ENC card.mp4

# ---------- Concat video ----------
printf "file '%s'\n" intro.mp4 c1.mp4 c2.mp4 c3.mp4 c4.mp4 c5.mp4 card.mp4 > list.txt
ffmpeg -y -v error -f concat -safe 0 -i list.txt -c copy video.mp4

# ---------- Audio ----------
TAIL=$(python3 -c "print(5*$D+$CARD)")
# music: original track for intro, then reuse its beat bed for the montage
ffmpeg -y -v error -i "$V" -filter_complex "
[0:a]atrim=0:$INTRO,asetpts=N/SR/TB,afade=t=out:st=$(python3 -c "print($INTRO-0.15)"):d=0.15[m1];
[0:a]atrim=2.5:$(python3 -c "print(2.5+$TAIL)"),asetpts=N/SR/TB,afade=t=in:d=0.05,afade=t=out:st=$(python3 -c "print($TAIL-0.08)"):d=0.08[m2];
[m1][m2]concat=n=2:v=0:a=1,aformat=sample_rates=48000:channel_layouts=stereo[m]" -map "[m]" music.wav

# SFX synth: whoosh (filtered noise sweep) + impact (sub thump + noise crack)
ffmpeg -y -v error -f lavfi -i "anoisesrc=d=0.45:c=pink:a=0.9" -af "highpass=f=400,lowpass=f=5000,afade=t=in:d=0.3:curve=exp,afade=t=out:st=0.33:d=0.12,aformat=sample_rates=48000:channel_layouts=stereo" whoosh.wav
ffmpeg -y -v error -f lavfi -i "sine=f=52:d=0.9" -f lavfi -i "anoisesrc=d=0.12:c=white:a=0.7" -filter_complex "
[0:a]volume=2.2,afade=t=out:d=0.9:curve=exp[s];[1:a]lowpass=f=3000,afade=t=out:d=0.12[n];
[s][n]amix=inputs=2:normalize=0,alimiter=limit=0.95,aformat=sample_rates=48000:channel_layouts=stereo" impact.wav

# place SFX: whoosh just before every cut, impact on every cut
CUTS=$(python3 -c "
I=$INTRO;D=$D
print(' '.join(str(round(I+k*D,3)) for k in range(6)))")
INPUTS="-i music.wav"; F=""; k=1
for c in $CUTS; do
  w=$(python3 -c "print(int(max(0,($c-0.4))*1000))"); i=$(python3 -c "print(int($c*1000))")
  INPUTS="$INPUTS -i whoosh.wav -i impact.wav"
  F="$F[$k:a]adelay=$w|$w,volume=0.55[w$k];[$((k+1)):a]adelay=$i|$i,volume=0.9[i$k];"
  MIX="$MIX[w$k][i$k]"; k=$((k+2))
done
ffmpeg -y -v error $INPUTS -filter_complex "${F}[0:a]$MIX amix=inputs=$k:normalize=0:duration=first,alimiter=limit=0.95" -c:a aac -b:a 192k audio.m4a

ffmpeg -y -v error -i video.mp4 -i audio.m4a -map 0:v -map 1:a -c:v copy -c:a copy -shortest -movflags +faststart \
  $B/scratchpad/ThroneRoofing_Reel.mp4
ffprobe -v error -show_entries format=duration -of csv=p=0 $B/scratchpad/ThroneRoofing_Reel.mp4
