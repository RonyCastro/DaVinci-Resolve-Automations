#!/usr/bin/env python

#   Import the API
import DaVinciResolveScript as dvr
import sys
import os, os.path
from os import listdir
from os.path import isfile, join
from subprocess import call
import re
import time
import subprocess
from datetime import datetime
import getpass
import fnmatch
import shutil
import os
import math

# Set path to the course path where to collect Data
coursePath = "/Volumes/RAIDBR042/4211 VOADOR ESTUDIO 220926"
courseName = os.path.basename(os.path.normpath(coursePath))
raidName = coursePath.split('/')[2]

computerName = "MacMini 01"

#   Load Davinci
resolve = dvr.scriptapp("Resolve")

#   Load the project manager
project_manager = resolve.GetProjectManager()

#   Define Project Name
ProjectName = "JPEG2000_Auto"

#   Delete any project with the name Proxies_Auto
ProjectCurrentName = project_manager.GetCurrentProject()

project_manager.CloseProject(ProjectCurrentName)

project = project_manager.DeleteProject(ProjectName)

#   Create new project with the project manager.
project = project_manager.CreateProject(ProjectName)

#   Load blank new project Proxies_Auto
project = project_manager.LoadProject(ProjectName)

#   Object of MediaPool is gotten from project.
mediaPool = project.GetMediaPool()
rootFolder = mediaPool.GetRootFolder()
pidList = []
clipError = ""
sendSlack = False
currentpid = ""
countRaw = 0
countJpeg = 0
countScLive = 0
countScLiveJPEG = 0
renderError = ""
currentbin = []
currentUHD = []
currentFHD = []
current6K = []

def getclipinfo(c):
    # Convert dictionary to list and iterate to get values. 
    clips = c.values()
    for clip in clips:
        cRes = clip.GetClipProperty('Resolution')
        if cRes == '3840x2160' or cRes == '4096x2160':
            mediaPool.SetCurrentFolder(currentUHD[i - 1])
            mediaPool.MoveClips([clip], currentUHD[i - 1])
            fileName = clip.GetName()
            ts = time.time()
            dateTime = datetime.fromtimestamp(ts)
            strDateTime = dateTime.strftime("%d-%m-%Y, %H:%M:%S")
            f = open(coursePath + '/' + str(courseName) + '_log.txt','a+')
            f.write(str(strDateTime) + ' - ' + 'Clip ' + str(fileName) + ' Loaded \n')
        elif cRes == '1920x1080' :
            mediaPool.SetCurrentFolder(currentFHD[i - 1])
            mediaPool.MoveClips([clip], currentFHD[i - 1])
            fileName = clip.GetName()
            ts = time.time()
            dateTime = datetime.fromtimestamp(ts)
            strDateTime = dateTime.strftime("%d-%m-%Y, %H:%M:%S")
            f = open(coursePath + '/' + str(courseName) + '_log.txt','a+')
            f.write(str(strDateTime) + ' - ' + 'Clip ' + str(fileName) + ' Loaded \n')
        elif cRes == '6144x3456' :
            mediaPool.SetCurrentFolder(current6K[i - 1])
            mediaPool.MoveClips([clip], current6K[i - 1])
            fileName = clip.GetName()
            ts = time.time()
            dateTime = datetime.fromtimestamp(ts)
            strDateTime = dateTime.strftime("%d-%m-%Y, %H:%M:%S")
            f = open(coursePath + '/' + str(courseName) + '_log.txt','a+')
            f.write(str(strDateTime) + ' - ' + 'Clip ' + str(fileName) + ' Loaded \n')
        pass
    return

# Create in loop 9 Bins in the project and import media of folders if not empty.
i = 1
while i <= 9 :
    mediaPool.AddSubFolder(rootFolder, "BIN 0" + str(i))
    currentbin.insert (i, mediaPool.GetCurrentFolder())
    currentUHD.insert (i, mediaPool.AddSubFolder(currentbin[i - 1], "UHD"))
    currentFHD.insert (i, mediaPool.AddSubFolder(currentbin[i - 1], "FHD"))
    current6K.insert (i, mediaPool.AddSubFolder(currentbin[i - 1], "6K"))
    mediaPool.SetCurrentFolder(currentbin[i - 1])
    jpegPath = str(coursePath) + "/JPEG2000 10BITS FILES/BIN 0" + str(i)
# If Bin in RAW is not empty will add a new job to render
    if mediaPool.ImportMedia([str(coursePath) + '/02 RAW/BIN 0' + str(i)]) != [] and os.path.exists(jpegPath) == False :
        mediaPool.SetCurrentFolder(currentbin[i - 1])
        clips = currentbin[i - 1].GetClips()
        clipList = getclipinfo(clips)
        clipsUHD = currentUHD[i - 1].GetClips()
        mediaPool.SetCurrentFolder(currentUHD[i - 1])
        UHDClips = mediaPool.CreateTimelineFromClips('TimeLine UHD' + str(i), clipsUHD)
        project.LoadRenderPreset('JPEG2000_UHD')
        project.SetRenderSettings({
            "SelectAllFrames" : 1,
            "TargetDir" : str(coursePath) + "/JPEG2000 10BITS FILES/BIN 0" + str(i),
            "RenderJobName" : "Bin 0" + str(i),
        })
        if clipsUHD != {} :
            pidList.append(project.AddRenderJob())
            clipsUHD = ""
        pass

        clipsFHD = currentFHD[i - 1].GetClips()
        mediaPool.SetCurrentFolder(currentFHD[i - 1])
        FHDClips = mediaPool.CreateTimelineFromClips('TimeLine FHD' + str(i), clipsFHD)
        project.LoadRenderPreset('JPEG2000_FHD')
        project.SetRenderSettings({
            "SelectAllFrames" : 1,
            "TargetDir" : str(coursePath) + "/JPEG2000 10BITS FILES/BIN 0" + str(i),
            "RenderJobName" : "Bin 0" + str(i),
        })
        if clipsFHD != {} :
            pidList.append(project.AddRenderJob())
            clipsFHD = ""
        pass

        clips6K = current6K[i - 1].GetClips()
        mediaPool.SetCurrentFolder(current6K[i - 1])
        sixKClips = mediaPool.CreateTimelineFromClips('TimeLine 6K' + str(i), clips6K)
        project.LoadRenderPreset('JPEG2000_6K')
        project.SetRenderSettings({
            "SelectAllFrames" : 1,
            "TargetDir" : str(coursePath) + "/JPEG2000 10BITS FILES/BIN 0" + str(i),
            "RenderJobName" : "Bin 0" + str(i),
        })
        if clips6K != {} :
            pidList.append(project.AddRenderJob())
            clips6K = ""
        pass

        counter = len(pidList)
        sendSlack = True
    pass
    i = i + 1
pass

if 'counter' in locals():
    i = 1
    while i <= counter and counter != "" :
        project.StartRendering(pidList[i - 1])
        while pidList[i - 1] != "" :
            jobStatus = project.GetRenderJobStatus(pidList[i - 1])
            if jobStatus['JobStatus'] == 'Complete' or jobStatus['JobStatus'] == 'Cancelled' :
                if jobStatus['JobStatus'] == 'Complete' :
                    ts = time.time()
                    dateTime = datetime.fromtimestamp(ts)
                    strDateTime = dateTime.strftime("%d-%m-%Y, %H:%M:%S")
                    f = open(coursePath + '/' + str(courseName) + '_log.txt','a+')
                    f.write(str(strDateTime) + ' - ' + 'Job ' + str(i) + ' Complete \n')
                    call(['screencapture', str(coursePath) + '/' + str(courseName) + '_Job' + str(i) + '_Complete.png'])
                    pidList[i - 1] = ""
                elif jobStatus['JobStatus'] == 'Cancelled' :
                    ts = time.time()
                    dateTime = datetime.fromtimestamp(ts)
                    strDateTime = dateTime.strftime("%d-%m-%Y, %H:%M:%S")
                    f = open(coursePath + '/' + str(courseName) + '_log.txt','a+')
                    f.write(str(strDateTime) + ' - ' + 'Job ' + str(i) + ' Cancelled \n')
                    call(['screencapture', str(coursePath) + '/' + str(courseName) + '_Job' + str(i) + '_Cancelled.png'])
                    pidList[i - 1] = ""
                    timeline = project.GetCurrentTimeline()
                    clipError = timeline.GetCurrentVideoItem()
                pass
            if jobStatus['JobStatus'] == 'Failed' :
                timeline = project.GetCurrentTimeline()
                clipError = timeline.GetCurrentVideoItem()
                while renderError == "" :
                    jobStatus = project.GetRenderJobStatus(pidList[i - 1])
                    renderError = jobStatus['Error']
                pass
                timeline = project.GetCurrentTimeline()
                clipError = timeline.GetCurrentVideoItem()
                call(['screencapture', str(coursePath) + '/'+ str(courseName) +'_Job' + str(i) + '_Failed.png'])
                clipWithError = clipError.GetMediaPoolItem()
                ts = time.time()
                dateTime = datetime.fromtimestamp(ts)
                strDateTime = dateTime.strftime("%d-%m-%Y, %H:%M:%S")
                f = open(coursePath + '/' + str(courseName) + '_log.txt','a+')
                f.write(str(strDateTime) + ' - ' + 'Job ' + str(i) + ' Failed' + ' - ' + str(renderError) + ' \n')
                binCounter = len(currentbin)
                b = 1
                while b <= binCounter :
                    mediaPool.SetCurrentFolder(currentbin[b - 1])
                    folder = mediaPool.GetCurrentFolder()
                    folderClips = folder.GetClipList()
                    for x in folderClips :
                        clipName = x.GetName()
                        print renderError
                        print clipName
                        if clipName in renderError :
                            mediaPool.DeleteClips(x)
                        pass
                    pass
                    b += 1
                pass
                project.StartRendering(pidList[i - 1])
            pass
        pass
        i = i + 1
    pass

    rawPath = (str(coursePath) + '/02 RAW')
    comparePath = (str(coursePath) + '/JPEG2000 10BITS FILES')
    time.sleep(3)
    scLivePath = (str(rawPath) + '/SC LIVE')
    scLivePathJPEG = (str(comparePath) + '/SC LIVE')

    if not os.path.exists(scLivePathJPEG):
        os.mkdir(scLivePathJPEG)

    for x in os.listdir(scLivePath):
        if not x.startswith('.'):
            countScLive += 1

    for x in os.listdir(scLivePathJPEG):
        if not x.startswith('.'):
            countScLiveJPEG += 1

    while countScLive != countScLiveJPEG :
        shutil.copy2(str(scLivePath), str(scLivePathJPEG))
        for x in os.listdir(scLivePath):
            if not x.startswith('.'):
                countScLive += 1
        for x in os.listdir(scLivePathJPEG):
            if not x.startswith('.'):
                countScLiveJPEG += 1
        if countScLive == countScLiveJPEG:
            break

    for x in os.listdir(rawPath):
        x = os.path.join(rawPath, x)
        if os.path.isdir(x):
            for y in os.listdir(x):
                if not y.startswith('.') and not y == 'Proxy':
                    countRaw += 1

    for x in os.listdir(comparePath):
        x = os.path.join(comparePath, x)
        if os.path.isdir(x):
            for y in os.listdir(x):
                if not y.startswith('.'):
                    countJpeg += 1

    if countRaw != countJpeg :
        clipError = 'Number of files are different'
    pass
pass

#Write a txt as a curl command to Slack and Monday
if sendSlack == True :

    def get_dir_size_old(path='.'):
        total = 0
        for p in os.listdir(path):
            full_path = os.path.join(path, p)
            if os.path.isfile(full_path):
                total += os.path.getsize(full_path)
            elif os.path.isdir(full_path):
                total += get_dir_size_old(full_path)
        return total

    def convert_size(size_bytes):
       if size_bytes == 0:
           return "0B"
       size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
       #i = int(math.floor(math.log(size_bytes, 1000)))
       p = math.pow(1000, i)
       s = round(size_bytes / p, 3)
       return "%s" % (s)

    raidPath = "/Volumes/" + str(raidName)
    jpegSize = 0
    rawSize = 0
    proxiesSize = 0
    lines = []
    raidPaths = []
    raidPaths.insert(0, str(raidPath))
    for path in raidPaths:
        for x in os.listdir(path):
            x = os.path.join(path, x)
            if not x.split('/')[3].startswith('.') :
                if os.path.isdir(x):
                    courseName = x.split('/')[3]
                    i = 4
                    courseSize = convert_size(get_dir_size_old(x))
                    for p in os.listdir(x):
                        current_path = os.path.join(x, p)
                        if os.path.isdir(current_path) and "JPEG2000 10BITS FILES" in current_path:
                            i = 4
                            jpegSize = convert_size(get_dir_size_old(current_path))
                        if os.path.isdir(current_path) and "02 RAW" in current_path:
                            i = 4
                            rawSize = convert_size(get_dir_size_old(current_path))
                        if os.path.isdir(current_path) and "04 PROXIES" in current_path:
                            i = 3
                            proxiesSize = convert_size(get_dir_size_old(current_path))
                    lines = ['board_id=$\'3194132776\'', 'raid_name=$\'' + str(raidName) + '\'', 'course_name=$\'' + str(courseName) + '\'', 'jpeg=$\'' + str(jpegSize) + '\'', 'raw=$\'' + str(rawSize) + '\'', 'proxies=$\'' + str(proxiesSize) + '\'', 'total=$\'' + str(courseSize) + '\'', 'now=$(date +%Y-%m-%d)', 'unset item_id', 'unset subitem_id', 'unset subitem_board_id', 'unset subitem_exist', 'item_id=$(curl -X POST -H "Content-Type:application/json" -H "Authorization:eyJhbGciOiJIUzI1NiJ9.eyJ0aWQiOjE3OTM4NjQxMSwidWlkIjoyNTgzOTUxOSwiaWFkIjoiMjAyMi0wOS0wNlQxNDozNzoyMC4wMDBaIiwicGVyIjoibWU6d3JpdGUiLCJhY3RpZCI6NDc3NjI4LCJyZ24iOiJ1c2UxIn0.--aptERw88eiaNW0mPe48j245zkOJa7wRJZiPQS2Iv0" \'https://api.monday.com/v2\' \\', '-d \'{"query":" {items_by_column_values(board_id:\'$board_id\', column_id:\\"name\\", column_value:\\"\'$raid_name\'\\"){id}}"}\' | grep -o \'"id":"[^"]*\' | grep -o \'[^"]*$\')', 'sleep 5', 'subitem_id=$(curl -X POST -H "Content-Type:application/json" -H "Authorization:eyJhbGciOiJIUzI1NiJ9.eyJ0aWQiOjE3OTM4NjQxMSwidWlkIjoyNTgzOTUxOSwiaWFkIjoiMjAyMi0wOS0wNlQxNDozNzoyMC4wMDBaIiwicGVyIjoibWU6d3JpdGUiLCJhY3RpZCI6NDc3NjI4LCJyZ24iOiJ1c2UxIn0.--aptERw88eiaNW0mPe48j245zkOJa7wRJZiPQS2Iv0" \'https://api.monday.com/v2\' \\', '-d \'{"query":"query { boards(ids: \'$board_id\') { items (ids: \'$item_id\') { subitems { id }}}}"}\' | grep -o \'"id":"[^"]*\' | grep -o \'[^"]*$\')', 'sleep 5', 'subitem_board_id=$(curl -X POST -H "Content-Type:application/json" -H "Authorization:eyJhbGciOiJIUzI1NiJ9.eyJ0aWQiOjE3OTM4NjQxMSwidWlkIjoyNTgzOTUxOSwiaWFkIjoiMjAyMi0wOS0wNlQxNDozNzoyMC4wMDBaIiwicGVyIjoibWU6d3JpdGUiLCJhY3RpZCI6NDc3NjI4LCJyZ24iOiJ1c2UxIn0.--aptERw88eiaNW0mPe48j245zkOJa7wRJZiPQS2Iv0" \'https://api.monday.com/v2\' \\', '-d \'{"query":"query { items (ids: [\'${subitem_id:0:10}\']) { board { id }}}"}\' | grep -o \'"id":"[^"]*\' | grep -o \'[^"]*$\')', 'sleep 5', 'subitem_exist=$(curl -X POST -H "Content-Type:application/json" -H "Authorization:eyJhbGciOiJIUzI1NiJ9.eyJ0aWQiOjE3OTM4NjQxMSwidWlkIjoyNTgzOTUxOSwiaWFkIjoiMjAyMi0wOS0wNlQxNDozNzoyMC4wMDBaIiwicGVyIjoibWU6d3JpdGUiLCJhY3RpZCI6NDc3NjI4LCJyZ24iOiJ1c2UxIn0.--aptERw88eiaNW0mPe48j245zkOJa7wRJZiPQS2Iv0" \'https://api.monday.com/v2\' \\', '-d \'{"query": "query { items_by_column_values (board_id: \'$subitem_board_id\', column_id:\\"name\\", column_value:\\"\'$course_name\'\\"){id}}"}\' | grep -o \'"id":"[^"]*\' | grep -o \'[^"]*$\')', 'sleep 5', 'if [[ ! -z "$subitem_exist" ]]; then', '    curl -X POST -H "Content-Type:application/json" -H "Authorization:eyJhbGciOiJIUzI1NiJ9.eyJ0aWQiOjE3OTM4NjQxMSwidWlkIjoyNTgzOTUxOSwiaWFkIjoiMjAyMi0wOS0wNlQxNDozNzoyMC4wMDBaIiwicGVyIjoibWU6d3JpdGUiLCJhY3RpZCI6NDc3NjI4LCJyZ24iOiJ1c2UxIn0.--aptERw88eiaNW0mPe48j245zkOJa7wRJZiPQS2Iv0" \'https://api.monday.com/v2\' \\', '   -d \'{"query":"mutation { delete_item (item_id: \'$subitem_exist\') { id }}"}\'', 'fi', 'sleep 5', 'curl -X POST -H "Content-Type:application/json" -H "Authorization:eyJhbGciOiJIUzI1NiJ9.eyJ0aWQiOjE3OTM4NjQxMSwidWlkIjoyNTgzOTUxOSwiaWFkIjoiMjAyMi0wOS0wNlQxNDozNzoyMC4wMDBaIiwicGVyIjoibWU6d3JpdGUiLCJhY3RpZCI6NDc3NjI4LCJyZ24iOiJ1c2UxIn0.--aptERw88eiaNW0mPe48j245zkOJa7wRJZiPQS2Iv0" \'https://api.monday.com/v2\' \\', '-d \'{"query":"mutation {create_subitem (parent_item_id:\'$item_id\', item_name:\\"\'$course_name\'\\", column_values:\\"{\\\\\\"numbers4\\\\\\": \\\\\\"\'$jpeg\'\\\\\\", \\\\\\"numbers1\\\\\\": \\\\\\"\'$raw\'\\\\\\", \\\\\\"numbers7\\\\\\": \\\\\\"\'$proxies\'\\\\\\", \\\\\\"numbers\\\\\\": \\\\\\"\'$total\'\\\\\\", \\\\\\"date0\\\\\\": {\\\\\\"date\\\\\\" : \\\\\\"\'$now\'\\\\\\"}}\\"){id}}"}\'', 'exit']
                    with open("/Users/dmstk/mondayupdate.sh", 'w') as f:
                        for line in lines:
                            f.write(line)
                            f.write('\n')
                    f.close()
    slackMessage = open("/Users/dmstk/slackMessage.sh", 'w')
    if clipError == "" :
        slackMessage.write('curl -X POST --data-urlencode "payload={\\"channel\\": \\"#jpeg2000-americas\\", \\"username\\": \\"' + str(computerName) + " - " + str(raidName) + '\\",\\"text\\": \\"' + str(courseName) + ' All JPEG 2000 Completed Successfully!' + '\\",\\"icon_emoji\\": \\":flag-br:\\"}" https://hooks.slack.com/services/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')
    elif clipError != "" :
        slackMessage.write('curl -X POST --data-urlencode "payload={\\"channel\\": \\"#jpeg2000-americas\\", \\"username\\": \\"' + str(computerName) + " - " + str(raidName) + '\\",\\"text\\": \\"' + str(courseName) + ' JPEG 2000 process found an error, please review logs! ' + 'Raw items: ' + str(countRaw) + ' & ' + 'JPEG2000 items: ' + str(countJpeg) + '\\",\\"icon_emoji\\": \\":no_entry:\\"}" https://hooks.slack.com/services/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')
    pass
elif sendSlack == False :
    slackMessage = open("/Users/dmstk/slackMessage.sh", 'w')
    slackMessage.write('')
    mondayupdate = open("/Users/dmstk/mondayupdate.sh", 'w')
    mondayupdate.write('')
pass