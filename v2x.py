#!/usr/bin/python
import sys, os, subprocess, re
# from subprocess import Popen, PIPE
file = sys.argv[1]

def getFPS(mkvINFO):
    fps = -1
    fpsPattern = re.compile(r'\w+.\w+ frames/fields per second for a video track\)\n\W\s+\+ Video track')
    fps = fpsPattern.search(mkvINFO)
    fpsPattern = re.compile(r'\w+.\w+')
    fps = fpsPattern.search(fps.group())
    return(fps.group())

def getVT(mkvINFO):
    vt = -1
    vtPattern = re.compile(r'\d\)\n\W\s+\+ Track UID: \d+\n\W\s+\+ Track type: video')
    vt = vtPattern.search(mkvINFO)
    vtPattern = re.compile(r'\d')
    vt = vtPattern.search(vt.group())
    return(vt.group())

def getVideoStats(file):
    mkvinfo_args = ['mkvinfo',file]
    mkvINFO = subprocess.check_output(mkvinfo_args)
    fps = getFPS(mkvINFO)
    vt = getVT(mkvINFO)
    print(mkvINFO)
    return(vt,fps)

def extractVideo(file,vt):
    videoExtract = -1
    h264File = os.path.splitext(file)[0] + '.264'
    mkvExtractArgs = 'mkvextract tracks \'' + file + '\' ' + vt + ':\'' + h264File + '\''
    if (os.path.isfile(h264File)):
        print('Skipping video extract, ' + h264File + ' already exists')
        videoExtract = 0
    else:
        print(mkvExtractArgs)
        videoExtract = subprocess.call(mkvExtractArgs, shell=True)
    return(videoExtract)

def getAudioStats():
    mediaInfoArgs = 'mediainfo \'' + file + '\''
    mediaInfo = subprocess.check_output(mediaInfoArgs, shell=True)
    pattern = re.compile(r'Bit rate mode\s+:\s+\w+')
    brm = pattern.search(mediaInfo)
    pattern = re.compile(r':\w+')
    brm = brm.group().rsplit(None, 1)[-1]
    pattern = re.compile(r'Bit rate mode\s+:\s+\w+\nBit rate\s+:\s+\d+\s+\w+')
    br = pattern.search(mediaInfo)
    pattern = re.compile(r'\d+\s+\w')
    br = pattern.search(br.group())
    br = br.group().replace(" ", "")
    return(brm.group(),br.group())

def extractAudio(file):
    mp4File = os.path.splitext(file)[0] + ' audioOnly.mp4'
    if os.path.isfile(mp4File):
        print('Skipping audio conversion, ' + mp4File + ' already exists')
        audioExtract = 0
    else:
        mediaInfo = getAudioStats()
        if (mediaInfo[0] == 'Constant'):
            ffmpegArgs = 'ffmpeg -i \'' + file + '\\ -vn -ac 2 -c:a libfdk_aac -flags -b:a ' + mediaInfo[1] + '\'' + mp4File + '\''
        else:
            ffmpegArgs = 'ffmpeg -i \'' + file + '\' -vn -ac 2 -c:a libfdk_aac -flags +qscale -global_quality 5 -cutoff 17k \'' + mp4File + '\''
        print(ffmpegArgs)
        audioExtract = subprocess.call(ffmpegArgs, shell=True)
    return(audioExtract)

def rebuildFile(file,fps):
    h264File = os.path.splitext(file)[0] + '.264'
    mp4File = os.path.splitext(file)[0] + ' audioOnly.mp4'
    newFile = os.path.splitext(file)[0] + '.mp4'
    mboxArgs = 'MP4Box -add \'' + h264File + '\':fps=' + fps + ' -add \'' + mp4File + '\' \'' + newFile + '\''
    print(mboxArgs)
    MP4Merge = subprocess.call(mboxArgs, shell=True)
    if (MP4Merge == 0):
        subprocess.call('rm \'' + h264File + '\'')
        subprocess.call('rm \'' + mp4File + '\'')
    return(MP4Merge)

if(file.endswith('.mkv') and os.path.isfile(file)):
    if os.path.isfile(os.path.splitext(file)[0] + ".mp4"):
        print(file + ' may have been converted already, check and remove before continuing.')
        sys.exit()
    mkvINFO = getVideoStats(file)
    print("video track: " + mkvINFO[0] + " at " + mkvINFO[1] + " fps" )
    if (mkvINFO[0] != -1 and mkvINFO[1] != -1):
        videoExtract = -1
        videoExtract = extractVideo(file,mkvINFO[0])
    else:
        print('Error gathering video metadata.')
        sys.exit()
    if (videoExtract == 0):
        audioExtract = -1
        audioExtract = extractAudio(file)
    else:
        print('Error extracting h264')
        sys.exit()
    if (audioExtract == 0):
        rebuildFile(file,mkvINFO[1])
    else:
        print('Error converting to mp4')
        sys.exit()