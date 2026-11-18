#!/bin/bash
# Throne Roofing reel v3 (black / white / red)
# call pickup -> satellite zoom -> 3D tilt dive (looking SW like the photos) -> AI-depth drone clips
# -> beat-synced words over drone footage -> hype montage -> STAY ALERT card
set -e
B=/tmp/claude-0/-home-user-usman/17155274-85b6-5c26-9ac5-e4d3e2acc502
S=$B/scratchpad/work3; mkdir -p $S; cd $S
P=$B/scratchpad/depth/clips          # p1..p5.mp4, 3.6s each, 1080x1920
V="/root/.claude/uploads/17155274-85b6-5c26-9ac5-e4d3e2acc502/ac293ef8-WhatsApp_Video_2026-11-18_at_6.24.02_PM.mp4"
FB=/usr/share/fonts/opentype/inter/Inter-Black.otf
FX=/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf
FPS=30; RED=0xD7141E; CALL=2.5
ENC="-c:v libx264 -preset medium -crf 18 -pix_fmt yuv420p -r $FPS"
WM="drawtext=fontfile=$FB:text='THRONE ROOFING':fontsize=40:fontcolor=white@0.9:x=(w-tw)/2:y=110:shadowcolor=black@0.6:shadowx=2:shadowy=2"
FLASH="fade=in:st=0:d=0.16:color=white"
COLOR="eq=contrast=1.10:saturation=1.12:gamma=0.97,unsharp=5:5:0.5,vignette=PI/4.5,noise=alls=6:allf=t,setsar=1"
DARK="hue=s=0.12,eq=contrast=1.25:brightness=-0.16,vignette=PI/3.5,noise=alls=8:allf=t,setsar=1"
seg() { echo "-ss $2 -t $3 -i $P/p$1.mp4"; }

# A. phone call
ffmpeg -y -v error -t $CALL -i "$V" -filter_complex "[0:v]fps=$FPS,split[a][b];[a]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,gblur=sigma=40[bg];[b]scale=1080:-2:flags=lanczos[fg];[bg][fg]overlay=(W-w)/2:(H-h)/2,hue=s=0,setsar=1" -an $ENC A.mp4
# B. satellite zoom + tilt dive
ffmpeg -y -v error -i $B/scratchpad/sat/satzoom.mp4 -vf "fps=$FPS,setsar=1,fade=in:st=0:d=0.12:color=white" -an $ENC B1.mp4
ffmpeg -y -v error -i $B/scratchpad/sat/tiltdive.mp4 -vf "fps=$FPS,setsar=1" -an $ENC B2.mp4
# C. drone arrival over the roof (looking SW, same as satellite end)
ffmpeg -y -v error $(seg 1 0 2.4) -vf "$COLOR,$WM,$FLASH" -an $ENC C.mp4

# D. beat-synced words over dark drone footage
word() { # $1 clip $2 start $3 dur $4 text $5 color $6 out
  ffmpeg -y -v error $(seg $1 $2 $3) -vf "$DARK,
drawbox=x=0:y=0:w=iw:h=ih:color=$RED@0.5:t=fill:enable='lt(t,0.05)',
drawtext=fontfile=$FB:text='$4':fontcolor=$5:fontsize='if(lt(t,0.12),190-300*t,154)':x=(w-tw)/2:y=(h-th)/2:shadowcolor=black@0.7:shadowx=0:shadowy=6,
drawbox=x=(iw-360)/2:y=1060:w=360:h=10:color=$RED:t=fill,$WM" -an $ENC $6; }
word 3 0.0 0.8 'ARE'       white w1.mp4
word 4 0.0 1.0 'YOU'       white w2.mp4
word 2 0.0 1.8 'READY?'    white w3.mp4
word 5 0.0 0.8 'SOMETHING' white w4.mp4
word 1 1.6 0.8 'BIG'       $RED  w5.mp4
word 3 1.4 1.0 'IS'        white w6.mp4
word 4 1.4 1.8 'COMING'    $RED  w7.mp4
word 5 1.4 0.8 'SOON.'     white w8.mp4
T="FOLLOW US..."; TX=$(python3 -c "from PIL import ImageFont;print(int((1080-ImageFont.truetype('$FB',120).getlength('$T'))/2))")
TY=""; for k in $(seq 1 ${#T}); do s=$(python3 -c "print(round(0.05+($k-1)*0.065,3))"); e=$(python3 -c "print(round(0.05+$k*0.065,3) if $k<${#T} else 9)")
  TY="$TY,drawtext=fontfile=$FB:text='${T:0:$k}':fontsize=120:fontcolor=white:x=$TX:y=(h-th)/2:enable='between(t,$s,$e)'"; done
ffmpeg -y -v error $(seg 2 1.9 1.6) -vf "$DARK$TY,drawbox=x=90:y=1040:w=900:h=10:color=$RED:t=fill:enable='gte(t,0.85)',
drawtext=fontfile=$FX:text='@THRONEROOFING':fontsize=46:fontcolor=$RED:x=(w-tw)/2:y=1090:enable='gte(t,0.85)',$WM" -an $ENC w9.mp4

# E. hype montage: big punchy line + small casual line
cap() { local y=1440
  echo "drawbox=x=0:y=$((y-24)):w='min(iw,iw*(t-0.08)/0.2)':h=160:color=$RED@0.95:t=fill:enable='gte(t,0.08)',
drawbox=x=0:y=$((y+136)):w='min(iw,iw*(t-0.12)/0.2)':h=8:color=black:t=fill:enable='gte(t,0.12)',
drawtext=fontfile=$FB:text='$1':fontsize=78:fontcolor=white:x='min(56,56-700*(0.32-t)/0.2)':y=$y:enable='gte(t,0.11)',
drawtext=fontfile=$FX:text='$2':fontsize=40:fontcolor=white:x='min(58,58-700*(0.4-t)/0.2)':y=$((y+86)):enable='gte(t,0.16)'"; }
D=1.4
ffmpeg -y -v error $(seg 1 2.2 $D) -vf "$COLOR,$WM,$(cap '26,500+ SQ FT.' 'yep. ONE roof.'),$FLASH" -an $ENC e1.mp4
ffmpeg -y -v error $(seg 3 2.2 $D) -vf "$COLOR,$WM,$(cap 'RIPPED. IT. ALL.' 'every single panel - gone'),$FLASH" -an $ENC e2.mp4
ffmpeg -y -v error $(seg 5 2.2 $D) -vf "$COLOR,$WM,$(cap 'DOWN TO THE BONES' 'fresh insulation going in'),$FLASH" -an $ENC e3.mp4
ffmpeg -y -v error $(seg 4 2.2 $D) -vf "$COLOR,$WM,$(cap 'NOW WE BUILD.' 'new membrane. zero shortcuts.'),$FLASH" -an $ENC e4.mp4
ffmpeg -y -v error $(seg 2 0.0 $D) -vf "$COLOR,$WM,$(cap 'ROCKGLEN, SK' 'and this is just the start...'),$FLASH" -an $ENC e5.mp4

# F. STAY ALERT card
CARD=2.6
ffmpeg -y -v error -loop 1 -t $CARD -framerate $FPS -i $B/images/2.webp -vf "
crop=ih*9/16:ih,scale=1080:1920,gblur=sigma=30,hue=s=0,eq=brightness=-0.42:contrast=1.2,
drawbox=x=0:y=0:w=iw:h=ih:color=$RED@0.22:t=fill:enable='lt(mod(t,0.5),0.1)*lt(t,1.6)',
drawbox=x=90:y=640:w=900:h=10:color=$RED:t=fill,drawbox=x=90:y=1270:w=900:h=10:color=$RED:t=fill,
drawbox=x=0:y=684:w=iw:h=160:color=$RED:t=fill,
drawtext=fontfile=$FB:text='⚠ STAY ALERT':fontsize=118:fontcolor=white:x=(w-tw)/2:y=704:alpha='if(lt(t,1.2),gt(mod(t,0.3),0.1),1)',
drawtext=fontfile=$FB:text='SOMETHING BIG':fontsize=96:fontcolor=white:x=(w-tw)/2:y=880:enable='gte(t,0.35)',
drawtext=fontfile=$FB:text='IS COMING':fontsize=96:fontcolor=white:x=(w-tw)/2:y=990:enable='gte(t,0.55)',
drawtext=fontfile=$FX:text='by THRONE ROOFING':fontsize=60:fontcolor=$RED:x=(w-tw)/2:y=1150:enable='gte(t,0.8)',
drawtext=fontfile=$FX:text='26,500+ SQ FT  •  ROCKGLEN, SK':fontsize=36:fontcolor=white@0.85:x=(w-tw)/2:y=1330:enable='gte(t,1.0)',
noise=alls=6:allf=t,vignette=PI/5,setsar=1,$FLASH" $ENC F.mp4

printf "file '%s'\n" A.mp4 B1.mp4 B2.mp4 C.mp4 w1.mp4 w2.mp4 w3.mp4 w4.mp4 w5.mp4 w6.mp4 w7.mp4 w8.mp4 w9.mp4 e1.mp4 e2.mp4 e3.mp4 e4.mp4 e5.mp4 F.mp4 > list.txt
ffmpeg -y -v error -f concat -safe 0 -i list.txt -c copy video.mp4
dur() { ffprobe -v error -show_entries format=duration -of csv=p=0 $1; }
SATD=$(dur B1.mp4); TILT=$(dur B2.mp4); DRD=$(dur C.mp4)
INS=$(python3 -c "print($SATD+$TILT+$DRD)"); TXT0=$(python3 -c "print($CALL+$INS)"); MONT=$(python3 -c "print(5*$D+$CARD)")

# ---------- audio ----------
ffmpeg -y -v error -f lavfi -i "aevalsrc='0.35*sin(2*PI*(80*t+60*t*t/$SATD))*(t/$SATD)':s=48000:d=$SATD" -f lavfi -i "anoisesrc=d=$INS:c=pink:a=0.5" -filter_complex "
[0:a]aformat=channel_layouts=stereo,apad=whole_dur=$INS[r];[1:a]lowpass=f=700,highpass=f=80,volume=0.8,afade=t=in:d=0.6,afade=t=out:st=$(python3 -c "print($INS-0.3)"):d=0.3,aformat=channel_layouts=stereo[w];
[r][w]amix=inputs=2:normalize=0:duration=longest" -ar 48000 ins_bed.wav
ffmpeg -y -v error -f lavfi -i "sine=f=1800:d=0.07" -af "volume=0.35,aformat=sample_rates=48000:channel_layouts=stereo" beep.wav
ffmpeg -y -v error -f lavfi -i "anoisesrc=d=0.45:c=pink:a=0.9" -af "highpass=f=400,lowpass=f=5000,afade=t=in:d=0.3:curve=exp,afade=t=out:st=0.33:d=0.12,aformat=sample_rates=48000:channel_layouts=stereo" whoosh.wav
ffmpeg -y -v error -f lavfi -i "anoisesrc=d=1.4:c=pink:a=0.9" -af "highpass=f=200,lowpass=f=3000,afade=t=in:d=1.1:curve=exp,afade=t=out:st=1.15:d=0.25,aformat=sample_rates=48000:channel_layouts=stereo" bigwhoosh.wav
ffmpeg -y -v error -f lavfi -i "sine=f=48:d=1.0" -f lavfi -i "anoisesrc=d=0.12:c=white:a=0.7" -filter_complex "[0:a]volume=2.4,afade=t=out:d=1.0:curve=exp[s];[1:a]lowpass=f=3000,afade=t=out:d=0.12[n];[s][n]amix=inputs=2:normalize=0,alimiter=limit=0.95,aformat=sample_rates=48000:channel_layouts=stereo" impact.wav
ffmpeg -y -v error -i "$V" -i ins_bed.wav -filter_complex "
[0:a]atrim=0:$CALL,asetpts=N/SR/TB,afade=t=out:st=$(python3 -c "print($CALL-0.1)"):d=0.1,aformat=sample_rates=48000:channel_layouts=stereo[a1];
[1:a]atrim=0:$INS,aformat=sample_rates=48000:channel_layouts=stereo[a2];
[0:a]atrim=2.5:12.9,asetpts=N/SR/TB,afade=t=in:d=0.04,aformat=sample_rates=48000:channel_layouts=stereo[a3];
[0:a]atrim=2.5:$(python3 -c "print(2.5+$MONT)"),asetpts=N/SR/TB,afade=t=in:d=0.05,afade=t=out:st=$(python3 -c "print($MONT-0.08)"):d=0.08,aformat=sample_rates=48000:channel_layouts=stereo[a4];
[a1][a2][a3][a4]concat=n=4:v=0:a=1[m]" -map "[m]" music.wav
EV=$(python3 - <<EOF
call=$CALL; sat=$SATD; tilt=$TILT; t0=$TXT0; D=$D
ev=[('whoosh',call-0.35),('impact',call)]
lock=call+sat*0.82
ev+= [('beep',lock+k*0.12) for k in range(4)]
ev+= [('bigwhoosh',call+sat-0.1),('whoosh',call+sat+tilt-0.4),('impact',call+sat+tilt)]
ev+= [('whoosh',t0-0.4),('impact',t0)]
m0=t0+10.4
for k in range(6): ev+= [('whoosh',m0+k*D-0.4),('impact',m0+k*D)]
print(' '.join(f'{n}:{max(0,t):.3f}' for n,t in ev))
EOF
)
INPUTS="-i music.wav"; F=""; MIX="[0:a]"; k=1
for e in $EV; do n=${e%%:*}; t=${e##*:}; ms=$(python3 -c "print(int($t*1000))")
  case $n in whoosh) v=0.55;; bigwhoosh) v=0.7;; impact) v=0.9;; beep) v=1.0;; esac
  INPUTS="$INPUTS -i $n.wav"; F="$F[$k:a]adelay=$ms|$ms,volume=$v[s$k];"; MIX="$MIX[s$k]"; k=$((k+1)); done
ffmpeg -y -v error $INPUTS -filter_complex "${F}${MIX}amix=inputs=$k:normalize=0:duration=first,alimiter=limit=0.95" -c:a aac -b:a 192k audio.m4a
ffmpeg -y -v error -i video.mp4 -i audio.m4a -map 0:v -map 1:a -c:v libx264 -preset slow -crf 23 -maxrate 14M -bufsize 28M -pix_fmt yuv420p -c:a copy -shortest -movflags +faststart /home/user/usman/output/ThroneRoofing_Reel_v3.mp4
ffprobe -v error -show_entries format=duration:format=size -of csv=p=0 /home/user/usman/output/ThroneRoofing_Reel_v3.mp4
