#!/bin/bash
# v4: v3 up to "FOLLOW US..." (~20.4s), then a clean ending:
# SOMETHING BIG IS COMING -> STAY CONNECTED -> Throne Roofing logo lockup -> fade to black
set -e
B=/tmp/claude-0/-home-user-usman/17155274-85b6-5c26-9ac5-e4d3e2acc502
S=$B/scratchpad/work3; cd $S          # reuses v3 segments A..w9 and sfx wavs
P=$B/scratchpad/depth/clips
LOGO=$B/scratchpad/logo/logo_white.png
V="/root/.claude/uploads/17155274-85b6-5c26-9ac5-e4d3e2acc502/ac293ef8-WhatsApp_Video_2026-11-18_at_6.24.02_PM.mp4"
FB=/usr/share/fonts/opentype/inter/Inter-Black.otf; FX=/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf
FPS=30; RED=0xD7141E
ENC="-c:v libx264 -preset medium -crf 18 -pix_fmt yuv420p -r $FPS"
DARK="hue=s=0.12,eq=contrast=1.25:brightness=-0.2,vignette=PI/3.5,noise=alls=8:allf=t,setsar=1"

# X1: SOMETHING BIG / IS COMING...  (2.2s, slow pull-back drone shot)
ffmpeg -y -v error -ss 0 -t 2.2 -i $P/p2.mp4 -vf "$DARK,fade=in:st=0:d=0.14:color=white,
drawtext=fontfile=$FB:text='SOMETHING':fontsize='if(lt(t,0.12),170-250*t,140)':fontcolor=white:x=(w-tw)/2:y=760,
drawtext=fontfile=$FB:text='BIG':fontsize='if(lt(t,0.42),300-400*(t-0.3),250)':fontcolor=$RED:x=(w-tw)/2:y=900:enable='gte(t,0.3)',
drawtext=fontfile=$FB:text='IS COMING...':fontsize=110:fontcolor=white:x=(w-tw)/2:y=1160:enable='gte(t,0.75)',
drawbox=x='(iw-min(820,820*(t-0.8)/0.3))/2':y=1300:w='min(820,820*(t-0.8)/0.3)':h=10:color=$RED:t=fill:enable='gte(t,0.8)'" -an $ENC x1.mp4

# X2: STAY / CONNECTED.  (1.8s)
ffmpeg -y -v error -ss 1.0 -t 1.8 -i $P/p3.mp4 -vf "$DARK,fade=in:st=0:d=0.12:color=white,
drawtext=fontfile=$FB:text='STAY':fontsize='if(lt(t,0.12),230-300*t,194)':fontcolor=white:x=(w-tw)/2:y=760,
drawbox=x=0:y=975:w='min(iw,iw*(t-0.2)/0.2)':h=190:color=$RED:t=fill:enable='gte(t,0.2)',
drawtext=fontfile=$FB:text='CONNECTED.':fontsize=150:fontcolor=white:x='min((w-tw)/2,(w-tw)/2-900*(0.42-t)/0.2)':y=992:enable='gte(t,0.22)',
drawtext=fontfile=$FX:text='turn on post notifications':fontsize=44:fontcolor=white@0.9:x=(w-tw)/2:y=1220:enable='gte(t,0.6)'" -an $ENC x2.mp4

# X3: logo lockup on black, slow push, fade to black (3.2s)
ffmpeg -y -v error -f lavfi -i "color=c=black:s=1080x1920:r=$FPS:d=3.2" -loop 1 -i $LOGO -filter_complex "
[1:v]format=rgba,scale=w='trunc(860*(0.92+0.08*min(1,t/3.2))/2)*2':h=-2:eval=frame,fade=in:st=0:d=0.45:alpha=1[l];
[0:v]drawbox=x=0:y=0:w=iw:h=ih:color=$RED@0.10:t=fill[bg];
[bg][l]overlay=x=(W-w)/2:y=640-h/2+60:shortest=1,
drawbox=x='(iw-min(760,760*(t-0.45)/0.35))/2':y=1010:w='min(760,760*(t-0.45)/0.35)':h=8:color=$RED:t=fill:enable='gte(t,0.45)',
drawtext=fontfile=$FB:text='SOMETHING BIG IS COMING':fontsize=56:fontcolor=white:x=(w-tw)/2:y=1060:alpha='min(1,max(0,(t-0.7)/0.3))',
drawtext=fontfile=$FX:text='STAY CONNECTED':fontsize=44:fontcolor=$RED:x=(w-tw)/2:y=1145:alpha='min(1,max(0,(t-0.95)/0.3))',
drawtext=fontfile=$FX:text='throneroofing.ca':fontsize=38:fontcolor=white@0.75:x=(w-tw)/2:y=1530:alpha='min(1,max(0,(t-1.2)/0.3))',
vignette=PI/4,noise=alls=4:allf=t,fade=out:st=2.6:d=0.6,setsar=1" $ENC x3.mp4

printf "file '%s'\n" A.mp4 B1.mp4 B2.mp4 C.mp4 w1.mp4 w2.mp4 w3.mp4 w4.mp4 w5.mp4 w6.mp4 w7.mp4 w8.mp4 w9.mp4 x1.mp4 x2.mp4 x3.mp4 > list4.txt
ffmpeg -y -v error -f concat -safe 0 -i list4.txt -c copy video4.mp4
dur() { ffprobe -v error -show_entries format=duration -of csv=p=0 $1; }
MAIN=$(python3 -c "print(sum(float(x) for x in '''$(for f in A B1 B2 C w1 w2 w3 w4 w5 w6 w7 w8 w9; do dur $f.mp4; done)'''.split()))")
X1=$(dur x1.mp4); X2=$(dur x2.mp4); X3=$(dur x3.mp4)
END=$(python3 -c "print($X1+$X2+$X3)")

# audio: v3 audio for the first part; ending = original beat bed fading out + hits + logo boom with echo tail
ffmpeg -y -v error -i audio.m4a -i "$V" -i impact.wav -i whoosh.wav -i bigwhoosh.wav -i impact.wav -i impact.wav -filter_complex "
[0:a]atrim=0:$MAIN,asetpts=N/SR/TB,aformat=sample_rates=48000:channel_layouts=stereo[a];
[1:a]atrim=2.5:$(python3 -c "print(2.5+$END)"),asetpts=N/SR/TB,afade=t=in:d=0.05,afade=t=out:st=$(python3 -c "print($X1+$X2)"):d=$(python3 -c "print($X3*0.8)"),aformat=sample_rates=48000:channel_layouts=stereo[bed];
[2:a]volume=0.9[i1];
[3:a]adelay=$(python3 -c "print(int(($X1-0.4)*1000))")|$(python3 -c "print(int(($X1-0.4)*1000))"),volume=0.55[w2];
[5:a]adelay=$(python3 -c "print(int($X1*1000))")|$(python3 -c "print(int($X1*1000))"),volume=0.9[i2];
[4:a]adelay=$(python3 -c "print(int(($X1+$X2-1.1)*1000))")|$(python3 -c "print(int(($X1+$X2-1.1)*1000))"),volume=0.6[bw];
[6:a]volume=1.2,aecho=0.8:0.7:180|420:0.45|0.3,adelay=$(python3 -c "print(int(($X1+$X2)*1000))")|$(python3 -c "print(int(($X1+$X2)*1000))")[boom];
[bed][i1][w2][i2][bw][boom]amix=inputs=6:normalize=0:duration=first,alimiter=limit=0.95,afade=t=out:st=$(python3 -c "print($END-0.6)"):d=0.6[e];
[a][e]concat=n=2:v=0:a=1[m]" -map "[m]" -c:a aac -b:a 192k audio4.m4a

ffmpeg -y -v error -i video4.mp4 -i audio4.m4a -map 0:v -map 1:a -c:v libx264 -preset slow -crf 23 -maxrate 14M -bufsize 28M -pix_fmt yuv420p -c:a copy -shortest -movflags +faststart /home/user/usman/output/ThroneRoofing_Reel_v4.mp4
echo main=$MAIN end=$END; ffprobe -v error -show_entries format=duration:format=size -of csv=p=0 /home/user/usman/output/ThroneRoofing_Reel_v4.mp4
