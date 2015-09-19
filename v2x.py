#!/usr/bin/python
import sys, os, subprocess, re, string
# from subprocess import Popen, PIPE
file = sys.argv[1]

def getFPS(mkvINFO):
    fps = -1
    fpsPattern = re.compile(r'Track type: video(.*)',re.DOTALL)
    fps = fpsPattern.search(mkvINFO)
    if fps == None:
        print('Could not find Frame Rate')
        fps = -1
    else:
        fpsPattern = re.compile(r'\w+.\w+ frames/fields per second for a video track')
        fps = fpsPattern.search(fps.group())
        if fps == None:
            print('Error finding Frame Rate')
            fps=-1
        else:
            fpsPattern = re.compile(r'\w+.\w+')
            fps = fpsPattern.search(fps.group())
            fps = fps.group()
    return(fps)

def getTracks(mkvINFO):
    vt = -1
    vtPattern = re.compile(r'Track ID \d+: video')
    vt = vtPattern.search(mkvINFO)
    if vt == None:
        vt = -1
    else:
        vtPattern = re.compile(r'\d')
        vt = vtPattern.search(vt.group())
    return(vt.group())

def getVideoStats(file):
    mkvinfo_args = ['mkvinfo',file]
    mkvINFO = subprocess.check_output(mkvinfo_args)
    print(mkvINFO)
    fps = getFPS(mkvINFO)
    mkvinfo_args = ['mkvmerge -i \"' + file + '\"']
    mkvINFO = subprocess.check_output(mkvinfo_args, shell=True)
    print(mkvINFO)
    vt = getTracks(mkvINFO)
    return(vt,fps)

def extractVideo(file,vt):
    videoExtract = -1
    h264File = os.path.splitext(file)[0] + '.264'
    mkvExtractArgs = 'mkvextract tracks \"' + file + '\" ' + vt + ':\"' + h264File + '\"'
    if (os.path.isfile(h264File)):
        print('Skipping video extract, ' + h264File + ' already exists')
        videoExtract = 0
    else:
        print(mkvExtractArgs)
        videoExtract = subprocess.call(mkvExtractArgs, shell=True)
    return(videoExtract)

def getAudioStats():
    mediaInfoArgs = 'mediainfo \"' + file + '\"'
    mediaInfo = subprocess.check_output(mediaInfoArgs, shell=True)
    pattern = re.compile(r'Audio\nID(.*)',re.DOTALL)
    audioStats = pattern.search(mediaInfo)
    aChannels = -1
    if audioStats is None:
        print('Audio stream unknown')
        brm = 'NA'
        br = 'NA'
    else:
        pattern = re.compile(r'Bit rate mode\s+:\s+\w+')
        brm = pattern.search(audioStats.group())
        pattern = re.compile(r'Format\s+:\s+\w+')
        codec = pattern.search(audioStats.group())
        if codec is not None:
            brm = codec.group().rsplit(None,1)[-1]
        else:
            brm = 'NA'
        if brm is None:
            
            pattern = re.compile(r'Channel(.*)')
            aChannels = pattern.search(audioStats.group())
            if aChannels is not None:
                all=string.maketrans('','')
                nodigs=all.translate(all, string.digits)
                aChannels = aChannels.group().translate(all, nodigs)
            else:
                aChannels = -1
        else:
            pattern = re.compile(r':\w+')
            brm = brm.group().rsplit(None, 1)[-1]
        pattern = re.compile(r'Bit rate mode\s+:\s+\w+\nBit rate(.*)')
        br = pattern.search(mediaInfo)
        if br == None:
            br = -1
        else:
            br = br.group().replace(" ", "")
            pattern = re.compile(r'\d+\w')
            br = pattern.search(br)
            br = br.group()
    return(brm,br,aChannels)


def extractAudio(file):
    aacFile = os.path.splitext(file)[0] + '.aac'
    if os.path.isfile(aacFile):
        print('Skipping audio conversion, ' + aacFile + ' already exists')
        audioExtract = 0
    else:
        mediaInfo = getAudioStats()
        if (mediaInfo[0] == 'Constant'):
            ffmpegArgs = 'ffmpeg -i \"' + file + '\" -vn -ac 2 -c:a libfdk_aac -b:a ' + mediaInfo[1] + ' \"' + aacFile + '\"'
        elif (mediaInfo[0] == 'AAC' and mediaInfo[2] == '2'):
            ffmpegArgs = 'ffmpeg -i \"' + file + '\" -vn -c:a copy \"' + aacFile + '\"'
        else:
            ffmpegArgs = 'ffmpeg -i \"' + file + '\" -vn -ac 2 -c:a libfdk_aac -flags +qscale -global_quality 5 -cutoff 17k \"' + aacFile + '\"'
#ffmpegArgs = 'ffmpeg -i \"' + file + '\" -vn -ac 2 -c:a libfdk_aac -flags +qscale -global_quality 5 -cutoff 17k \"' + aacFile + '\"'
        print(ffmpegArgs)
        audioExtract = subprocess.call(ffmpegArgs, shell=True)
    return(audioExtract)

def rebuildFile(file,fps):
    h264File = os.path.splitext(file)[0] + '.264'
    aacFile = os.path.splitext(file)[0] + '.aac'
    newFile = os.path.splitext(file)[0] + '.mp4'
    mboxArgs = 'MP4Box -add \"' + h264File + '\":fps=' + fps + ' -add \"' + aacFile + '\" \"' + newFile + '\"'
    print(mboxArgs)
    MP4Merge = subprocess.call(mboxArgs, shell=True)
    if (MP4Merge == 0):
        subprocess.call('rm -v \"' + h264File + '\"', shell=True)
        subprocess.call('rm -v \"' + aacFile + '\"', shell=True)
        subprocess.call('rm -v \"' + file + '\"', shell=True)
    return(MP4Merge)

if(file.endswith('.mkv') and os.path.isfile(file)):
    if os.path.isfile(os.path.splitext(file)[0] + ".mp4"):
        print(file + ' may have been converted already, check and remove before continuing.')
        sys.exit()
    print('Attempting conversion of ' + file)
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
