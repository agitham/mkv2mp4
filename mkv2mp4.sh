#! /bin/bash
fps=`mediainfo "$1" | grep -F "Frame rate" | sed ''s/[^0-9.]*//g''`
vt=`mediainfo "$1" | grep -A 1 Video | grep ID | sed ''s/[^0-9.]*//g''`
let vt=$vt-1;
tput setaf 1;
echo 'mkvextract' $1
echo $fps fps
echo 'Video track: '$vt
tput sgr0
mkvextract tracks "$1" $vt:v.264
tput setaf 1; echo 'avconv -i '$1' -vn -ac 2 -c:a libvo_aacenc -flags +qscale -global_quality 5 -cutoff 17k a.mp4'
tput sgr0
avconv -i "$1" -vn -ac 2 -c:a libvo_aacenc -flags +qscale -global_quality 5 -cutoff 17k a.mp4
tput setaf 1; echo 'MP4Box -add v.264:fps='$fps' -add a.mp4' "${1%.mkv}.mp4"
tput sgr0
MP4Box -add v.264:fps=$fps -add a.mp4 "${1%.mkv}.mp4"
rm v.264 a.mp4
