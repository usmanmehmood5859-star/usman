#!/bin/bash
# Throne Roofing reel v2: black / white / red
# call pickup -> satellite zoom -> drone -> word-by-word text over site footage -> photo montage -> STAY ALERT card
set -e
B=/tmp/claude-0/-home-user-usman/17155274-85b6-5c26-9ac5-e4d3e2acc502
S=$B/scratchpad/work2; mkdir -p $S; cd $S
IMG=$B/images
V="/root/.claude/uploads/17155274-85b6-5c26-9ac5-e4d3e2acc502/ac293ef8-WhatsApp_Video_2026-11-18_at_6.24.02_PM.mp4"
SAT=$B/scratchpad/sat/satzoom.mp4
DRONE=${DRONE:-}          # optional AI drone clip(s); falls back to photo-based move
FB=/usr/share/fonts/opentype/inter/Inter-Black.otf
FX=/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf
FPS=30
ENC="-c:v libx264 -preset medium -crf 18 -pix_fmt yuv420p -r $FPS"
RED=0xD7141E
CALL=2.5

# ---------- A. phone call (original 0 - 2.5s) ----------
ffmpeg -y -v error -t $CALL -i "$V" -filter_complex "
[0:v]fps=$FPS,split[a][b];[a]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,gblur=sigma=40[bg];
[b]scale=1080:-2:flags=lanczos[fg];[bg][fg]overlay=(W-w)/2:(H-h)/2,hue=s=0,setsar=1" -an $ENC A.mp4

# ---------- B. satellite zoom ----------
ffmpeg -y -v error -i $SAT -vf "fps=$FPS,setsar=1,fade=in:st=0:d=0.12:color=white" -an $ENC B.mp4
SATD=$(ffprobe -v error -show_entries format=duration -of csv=p=0 B.mp4)

# ---------- C. drone ----------
LOOK="eq=contrast=1.12:saturation=1.05:gamma=0.97,unsharp=5:5:0.6,\
scale=1124:1998,crop=1080:1920:x='22+9*sin(t*21)+5*sin(t*37)':y='39+11*sin(t*17+1)+5*sin(t*31)',\
vignette=PI/4.5,noise=alls=7:allf=t,setsar=1"
if [ -n "$DRONE" ]; then
  ffmpeg -y -v error -i "$DRONE" -vf "fps=$FPS,scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,eq=contrast=1.08,noise=alls=5:allf=t,setsar=1,fade=in:st=0:d=0.15:color=white" -an $ENC C.mp4
else
  ffmpeg -y -v error -loop 1 -t 2.4 -framerate $FPS -i $IMG/1.webp -vf "
scale=-2:2600:flags=lanczos,rotate='0.06-0.05*t/2.4':ow=iw:oh=ih:c=black,
crop=1460:2596:x='(iw-ow)*(0.9-0.6*t/2.4)':y='(ih-oh)/2',scale=1080:1920,$LOOK,fade=in:st=0:d=0.15:color=white" $ENC C.mp4
fi
DRD=$(ffprobe -v error -show_entries format=duration -of csv=p=0 C.mp4)

# ---------- D. word-by-word text over site footage (timed to original beat 2.5s-12.9s) ----------
# background plate: dark, almost black & white, slow push
plate() { # $1 img $2 dur $3 out $4 zoom-direction(+1/-1)
  local n=$(python3 -c "print(int(round($2*$FPS)))")
  ffmpeg -y -v error -i $IMG/$1 -vf "
crop=ih*9/16:ih,scale=2160:3840:flags=lanczos,
zoompan=z='if(gt($4,0),1.0+0.10*on/$n,1.12-0.10*on/$n)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=$n:s=1080x1920:fps=$FPS,
hue=s=0.12,eq=contrast=1.25:brightness=-0.16,vignette=PI/3.5,noise=alls=8:allf=t,setsar=1" -frames:v $n $ENC $3
}
word() { # $1 plate-img $2 dur $3 text $4 color $5 out $6 zoomdir
  plate $1 $2 _p.mp4 $6
  ffmpeg -y -v error -i _p.mp4 -vf "
drawbox=x=0:y=0:w=iw:h=ih:color=$RED@0.55:t=fill:enable='lt(t,0.06)',
drawtext=fontfile=$FB:text='$3':fontcolor=$4:fontsize='if(lt(t,0.12),190-300*t,154)':x=(w-tw)/2:y=(h-th)/2:shadowcolor=black@0.7:shadowx=0:shadowy=6,
drawbox=x=(iw-360)/2:y=1060:w=360:h=10:color=$RED:t=fill,
drawtext=fontfile=$FB:text='THRONE ROOFING':fontsize=40:fontcolor=white@0.9:x=(w-tw)/2:y=110" $ENC $5
}
word 1.webp 0.8 'ARE'       white  w1.mp4  1
word 3.webp 1.0 'YOU'       white  w2.mp4 -1
word 4.webp 1.8 'READY?'    white  w3.mp4  1
word 2.webp 0.8 'SOMETHING' white  w4.mp4 -1
word 5.webp 0.8 'BIG'       $RED   w5.mp4  1
word 3.webp 1.0 'IS'        white  w6.mp4 -1
word 1.webp 1.8 'COMING'    $RED   w7.mp4  1
word 4.webp 0.8 'SOON.'     white  w8.mp4 -1
# FOLLOW US... typed, 1.6s
plate 2.webp 1.6 _p.mp4 1
TX=$(python3 -c "from PIL import ImageFont;f=ImageFont.truetype('$FB',120);print(int((1080-f.getlength('FOLLOW US...'))/2))")
TY=""; T="FOLLOW US..."; for k in $(seq 1 ${#T}); do
  s=$(python3 -c "print(round(0.05+($k-1)*0.065,3))"); e=$(python3 -c "print(round(0.05+$k*0.065,3) if $k<${#T} else 9)")
  TY="$TY,drawtext=fontfile=$FB:text='${T:0:$k}':fontsize=120:fontcolor=white:x=$TX:y=(h-th)/2:enable='between(t,$s,$e)'"
done
ffmpeg -y -v error -i _p.mp4 -vf "null$TY,drawbox=x=90:y=1040:w=900:h=10:color=$RED:t=fill:enable='gte(t,0.85)',
drawtext=fontfile=$FX:text='@THRONEROOFING':fontsize=46:fontcolor=$RED:x=(w-tw)/2:y=1090:enable='gte(t,0.85)',
drawtext=fontfile=$FB:text='THRONE ROOFING':fontsize=40:fontcolor=white@0.9:x=(w-tw)/2:y=110" $ENC w9.mp4

# ---------- E. photo montage with red captions ----------
WM="drawtext=fontfile=$FB:text='THRONE ROOFING':fontsize=40:fontcolor=white@0.9:x=(w-tw)/2:y=110:shadowcolor=black@0.6:shadowx=2:shadowy=2"
FLASH="fade=in:st=0:d=0.16:color=white"
cap() { local y=1450
  echo "drawbox=x=0:y=$((y-20)):w='min(iw,iw*(t-0.1)/0.22)':h=150:color=$RED@0.95:t=fill:enable='gte(t,0.1)',\
drawbox=x=0:y=$((y+130)):w='min(iw,iw*(t-0.14)/0.22)':h=8:color=black:t=fill:enable='gte(t,0.14)',\
drawtext=fontfile=$FB:text='$1':fontsize=74:fontcolor=white:x='min(60,60-700*(0.36-t)/0.22)':y=$y:enable='gte(t,0.13)',\
drawtext=fontfile=$FX:text='$2':fontsize=38:fontcolor=white@0.95:x='min(62,62-700*(0.42-t)/0.22)':y=$((y+82)):enable='gte(t,0.18)'"
}
D=1.3; N=$(python3 -c "print(int($D*$FPS))")
ffmpeg -y -v error -loop 1 -t $D -framerate $FPS -i $IMG/1.webp -vf "
scale=-2:2400:flags=lanczos,crop=1350:2400:x='(iw-ow)*(0.85-0.55*t/$D)':y=0,scale=1080:1920,
$LOOK,$WM,$(cap '26,500+ SQ FT' 'HOSPITAL ROOF REPLACEMENT'),$FLASH" $ENC e1.mp4
zp() { ffmpeg -y -v error -i $IMG/$1 -vf "
crop=ih*9/16:ih,scale=2160:3840:flags=lanczos,zoompan=z='$3':x='$4':y='$5':d=$N:s=1080x1920:fps=$FPS,
$LOOK,$WM,$(cap "$6" "$7"),$FLASH" -frames:v $N $ENC $2; }
zp 3.webp e2.mp4 "1.0+0.16*on/$N" "iw/2-(iw/zoom/2)+120*on/$N" "ih/2-(ih/zoom/2)" 'FULL TEAR-OFF' 'CREW ON SITE - ROCKGLEN, SK'
zp 5.webp e3.mp4 "1.22-0.18*on/$N" "iw/2-(iw/zoom/2)" "ih/2-(ih/zoom/2)" 'DOWN TO THE DECK' 'NEW INSULATION LAYER'
zp 4.webp e4.mp4 "1.05+0.15*on/$N" "iw/2-(iw/zoom/2)" "ih*0.55-(ih/zoom/2)" 'NEW MEMBRANE' 'COMMERCIAL GRADE SYSTEM'
zp 2.webp e5.mp4 "1.18-0.14*on/$N" "iw/2-(iw/zoom/2)" "ih/2-(ih/zoom/2)" 'SASKATCHEWAN' 'BUILT BY THRONE ROOFING'

# ---------- F. STAY ALERT card (black / red / white), ends abruptly ----------
CARD=2.6
ffmpeg -y -v error -loop 1 -t $CARD -framerate $FPS -i $IMG/2.webp -vf "
crop=ih*9/16:ih,scale=1080:1920,gblur=sigma=30,hue=s=0,eq=brightness=-0.42:contrast=1.2,
drawbox=x=0:y=0:w=iw:h=ih:color=$RED@0.22:t=fill:enable='lt(mod(t,0.5),0.1)*lt(t,1.6)',
drawbox=x=90:y=640:w=900:h=10:color=$RED:t=fill,
drawbox=x=90:y=1270:w=900:h=10:color=$RED:t=fill,
drawbox=x=0:y=684:w=iw:h=160:color=$RED:t=fill,
drawtext=fontfile=$FB:text='⚠ STAY ALERT':fontsize=118:fontcolor=white:x=(w-tw)/2:y=704:alpha='if(lt(t,1.2),gt(mod(t,0.3),0.1),1)',
drawtext=fontfile=$FB:text='SOMETHING BIG':fontsize=96:fontcolor=white:x=(w-tw)/2:y=880:enable='gte(t,0.35)',
drawtext=fontfile=$FB:text='IS COMING':fontsize=96:fontcolor=white:x=(w-tw)/2:y=990:enable='gte(t,0.55)',
drawtext=fontfile=$FX:text='by THRONE ROOFING':fontsize=60:fontcolor=$RED:x=(w-tw)/2:y=1150:enable='gte(t,0.8)',
drawtext=fontfile=$FX:text='26,500+ SQ FT  •  ROCKGLEN, SK':fontsize=36:fontcolor=white@0.85:x=(w-tw)/2:y=1330:enable='gte(t,1.0)',
noise=alls=6:allf=t,vignette=PI/5,setsar=1,$FLASH" $ENC F.mp4

printf "file '%s'\n" A.mp4 B.mp4 C.mp4 w1.mp4 w2.mp4 w3.mp4 w4.mp4 w5.mp4 w6.mp4 w7.mp4 w8.mp4 w9.mp4 e1.mp4 e2.mp4 e3.mp4 e4.mp4 e5.mp4 F.mp4 > list.txt
ffmpeg -y -v error -f concat -safe 0 -i list.txt -c copy video.mp4
TOT=$(ffprobe -v error -show_entries format=duration -of csv=p=0 video.mp4)

# ---------- Audio ----------
INS=$(python3 -c "print($SATD+$DRD)")
TXT0=$(python3 -c "print($CALL+$INS)")         # where the beat-synced text starts
MONT=$(python3 -c "print(5*$D+$CARD)")
# satellite / drone sound design: riser + wind + lock beeps + boom at drone cut
ffmpeg -y -v error -f lavfi -i "aevalsrc='0.35*sin(2*PI*(80*t+60*t*t/$SATD))*(t/$SATD)':s=48000:d=$SATD" \
  -f lavfi -i "anoisesrc=d=$INS:c=pink:a=0.5" -filter_complex "
[0:a]aformat=channel_layouts=stereo[r];[1:a]lowpass=f=700,highpass=f=80,volume=0.8,afade=t=in:d=0.6,afade=t=out:st=$(python3 -c "print($INS-0.3)"):d=0.3,aformat=channel_layouts=stereo[w];
[r][w]amix=inputs=2:normalize=0:duration=longest" -ar 48000 ins_bed.wav
ffmpeg -y -v error -f lavfi -i "sine=f=1800:d=0.07" -af "volume=0.35,aformat=sample_rates=48000:channel_layouts=stereo" beep.wav
ffmpeg -y -v error -f lavfi -i "anoisesrc=d=0.45:c=pink:a=0.9" -af "highpass=f=400,lowpass=f=5000,afade=t=in:d=0.3:curve=exp,afade=t=out:st=0.33:d=0.12,aformat=sample_rates=48000:channel_layouts=stereo" whoosh.wav
ffmpeg -y -v error -f lavfi -i "sine=f=48:d=1.0" -f lavfi -i "anoisesrc=d=0.12:c=white:a=0.7" -filter_complex "
[0:a]volume=2.4,afade=t=out:d=1.0:curve=exp[s];[1:a]lowpass=f=3000,afade=t=out:d=0.12[n];
[s][n]amix=inputs=2:normalize=0,alimiter=limit=0.95,aformat=sample_rates=48000:channel_layouts=stereo" impact.wav

# music: original call audio, inserted sound design, original beat-synced text audio, then reused beat for montage
ffmpeg -y -v error -i "$V" -i ins_bed.wav -filter_complex "
[0:a]atrim=0:$CALL,asetpts=N/SR/TB,afade=t=out:st=$(python3 -c "print($CALL-0.1)"):d=0.1,aformat=sample_rates=48000:channel_layouts=stereo[a1];
[1:a]aformat=sample_rates=48000:channel_layouts=stereo[a2];
[0:a]atrim=2.5:12.9,asetpts=N/SR/TB,afade=t=in:d=0.04,aformat=sample_rates=48000:channel_layouts=stereo[a3];
[0:a]atrim=2.5:$(python3 -c "print(2.5+$MONT)"),asetpts=N/SR/TB,afade=t=in:d=0.05,afade=t=out:st=$(python3 -c "print($MONT-0.08)"):d=0.08,aformat=sample_rates=48000:channel_layouts=stereo[a4];
[a1][a2][a3][a4]concat=n=4:v=0:a=1[m]" -map "[m]" music.wav

# SFX placement
EV=$(python3 - <<EOF
call=$CALL; sat=$SATD; dr=$DRD; t0=$TXT0; D=$D
ev=[]
ev.append(('whoosh',call-0.35)); ev.append(('impact',call))                 # into satellite
lock=call+sat*0.82
for k in range(4): ev.append(('beep',lock+k*0.12))                          # target lock beeps
ev.append(('whoosh',call+sat-0.4)); ev.append(('impact',call+sat))          # into drone
ev.append(('whoosh',t0-0.4)); ev.append(('impact',t0))                      # into text
m0=t0+10.4
for k in range(6): ev.append(('whoosh',m0+k*D-0.4)); ev.append(('impact',m0+k*D))
print(' '.join(f'{n}:{max(0,t):.3f}' for n,t in ev))
EOF
)
INPUTS="-i music.wav"; F=""; MIX="[0:a]"; k=1
for e in $EV; do n=${e%%:*}; t=${e##*:}; ms=$(python3 -c "print(int($t*1000))")
  case $n in whoosh) v=0.55;; impact) v=0.9;; beep) v=1.0;; esac
  INPUTS="$INPUTS -i $n.wav"; F="$F[$k:a]adelay=$ms|$ms,volume=$v[s$k];"; MIX="$MIX[s$k]"; k=$((k+1)); done
ffmpeg -y -v error $INPUTS -filter_complex "${F}${MIX}amix=inputs=$k:normalize=0:duration=first,alimiter=limit=0.95" -c:a aac -b:a 192k audio.m4a

ffmpeg -y -v error -i video.mp4 -i audio.m4a -map 0:v -map 1:a -c:v copy -c:a copy -shortest -movflags +faststart $B/scratchpad/ThroneRoofing_Reel_v2.mp4
ffprobe -v error -show_entries format=duration -of csv=p=0 $B/scratchpad/ThroneRoofing_Reel_v2.mp4
