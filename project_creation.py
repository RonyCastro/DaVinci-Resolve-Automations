#!/usr/bin/env python

#   Import the API
import DaVinciResolveScript as dvr
import sys
import os, os.path
from subprocess import call
import re
import time
import subprocess
from datetime import datetime, timedelta
import getpass
import fnmatch
import datetime

coursePath = sys.argv[1]
courseName = os.path.basename(os.path.normpath(coursePath))
edlPath = str(coursePath) + '/07 EDITING/CAMERA REPORTS/' + courseName[0:4] + '_EDL'
projectPath = str(coursePath) + '/00 DOMESTIKA CORP/00 DAVINCI BASE PROJECTS/0000 BASE PROJECT UHD 221017(Auto).drp'
rawPath = str(coursePath) + '/02 RAW'
proxiesPath = str(coursePath) + '/04 PROXIES'

#   Load Davinci
resolve = dvr.scriptapp("Resolve")
project_manager = resolve.GetProjectManager()
ProjectName = str(courseName)
ProjectCurrentName = project_manager.GetCurrentProject()
project_manager.CloseProject(ProjectCurrentName)
project = project_manager.DeleteProject(ProjectName)
project_manager.ImportProject(projectPath)

#   Load base project
project = project_manager.LoadProject('0000 BASE PROJECT UHD 221017(Auto)')

#   Object of MediaPool is gotten from project.
mediaPool = project.GetMediaPool()
rootFolder = mediaPool.GetRootFolder()

#   Declare variables
edlList = []
counter = 0
unitListNames = []
unitList = []
lessonList = []
lessonListNames = []
importedList = []

#   Get object name from folders already created in project
subFolderList = rootFolder.GetSubFolderList()
for x in subFolderList:
    subFolderName = x.GetName()
    if subFolderName == "07 EDITING":
        subSubFolderList = x.GetSubFolderList()
        for y in subSubFolderList:
            subSubFolderName = y.GetName()
            if subSubFolderName == "B-ROLL":
                subSubFolderClipList = y.GetClipList()
                mediaPool.DeleteClips(subSubFolderClipList)
                bRollFolder = y
            elif subSubFolderName == "+_PLEASE CHECK":
                subSubFolderClipList = y.GetClipList()
                mediaPool.DeleteClips(subSubFolderClipList)
                notImportedFolder = y
            elif subSubFolderName == "COURSE EDITING":
                subSubFolderClipList = y.GetSubFolderList()
                mediaPool.DeleteFolders(subSubFolderClipList)
                rootFolder = y
            pass
        pass
    pass
pass

#   Get EDL List
i = 0
for x in os.listdir(edlPath):
    if not x.endswith('.txt') and not x.startswith('.'):
        x = os.path.join(edlPath, x)
        edlList.insert(i, x)
        i += 1
        counter += 1
    pass
pass

#   Start to compare each EDL timestamp with each RAW file time creation to import Proxies
i = 0
while i != counter :
    addHour = 0
    addMinute = 0
    f = open(str(edlList[i]), 'r')
    lesson = f.readline()
    courseUnit = lesson[6:9]
    unitLesson = lesson[9:11]
    unitList = rootFolder.GetSubFolderList()
    txtFile = str(edlList[i])
    txtFile = txtFile.replace('_EDL.edl', '_TXT.txt')
    txtFile = txtFile.replace('_EDL', '_TXT')
    t = open(txtFile, 'r')
    edlTxtFile = t.readline()
    timestamp = edlTxtFile[0:19]
    edlTxtFileLines = t.readlines()
    try:
        edlTxtFile = edlTxtFileLines[-2]
    except:
        f.close()
        i += 1
        continue
    
    timestampDate = timestamp[0:11]
    
    finalSecond = int(timestamp[17:19]) + int(edlTxtFile[6:8])
    
    if finalSecond > 59:
        finalSecond = finalSecond - 60
        addMinute = 1
    pass
    if finalSecond < 10:
        finalSecond = '0' + str(finalSecond)
    pass
    
    finalMinute = int(timestamp[14:16]) + int(edlTxtFile[3:5]) + addMinute

    if finalMinute > 59:
        finalMinute = finalMinute - 60
        addHour = 1
    pass
    if finalMinute < 10:
        finalMinute = '0' + str(finalMinute)
    pass

    finalHour = int(timestamp[11:13]) + int(edlTxtFile[0:2]) + addHour
    if finalHour < 10:
        finalHour = '0' + str(finalHour)
    pass

    timestampFinal = str(timestampDate) + str(finalHour) + ':' + str(finalMinute) + ':' + str(finalSecond)
    convertedTimestampFinal = datetime.datetime.strptime(timestampFinal, '%Y-%m-%d %H:%M:%S')
    date_select = datetime.datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
    delta = timedelta(hours=int(time.tzname[0]))
    timestamp = date_select + delta
    timestamp = timestamp.strftime("%Y-%m-%d %H:%M:%S")
    timestampFinal = convertedTimestampFinal + delta
    timestampFinal = timestampFinal.strftime("%Y-%m-%d %H:%M:%S")

    y = 0
    for x in unitList :
        folderName = x.GetName()
        unitListNames.insert(y, folderName)
        y += 1
    pass
    if not str(courseUnit) in unitListNames :
        mediaPool.AddSubFolder(rootFolder, courseUnit)
        mediaPool.SetCurrentFolder(str(courseUnit))
        currentFolder = mediaPool.GetCurrentFolder()
        lessonList = currentFolder.GetSubFolderList()
        mediaPool.AddSubFolder(currentFolder, unitLesson)
        mediaPool.SetCurrentFolder(str(unitLesson))
        currentFolder = mediaPool.GetCurrentFolder()
        for x in os.listdir(rawPath):
            x = os.path.join(rawPath, x)
            if not x.startswith('.') and os.path.isdir(x):
                for y in os.listdir(x):
                    if not y.startswith('R') and not y.startswith('.'):
                        mediaPath = x + '/' + y
                        mediaCreation = datetime.datetime.fromtimestamp(os.stat(mediaPath).st_birthtime)
                        mediaCreation = str(mediaCreation)[0:19]
                        mediaCreationNumber = time.mktime(datetime.datetime.strptime(mediaCreation,
                                                 "%Y-%m-%d %H:%M:%S").timetuple())
                        timestampNumber = time.mktime(datetime.datetime.strptime(timestamp,
                                                 "%Y-%m-%d %H:%M:%S").timetuple())
                        timestampFinalNumber = time.mktime(datetime.datetime.strptime(timestampFinal,
                                                 "%Y-%m-%d %H:%M:%S").timetuple())
                        if timestampNumber <  mediaCreationNumber :
                            difference = mediaCreationNumber - timestampNumber
                        elif timestampNumber >  mediaCreationNumber :
                            difference = timestampNumber - mediaCreationNumber
                        pass
                        if difference < 200 or timestampNumber <= mediaCreationNumber <= timestampFinalNumber:
                            mediaPath = mediaPath.replace('02 RAW', '04 PROXIES')
                            mediaPath = mediaPath.replace('.braw', '.mov')
                            mediaPool.ImportMedia(mediaPath)
                            importedList.append(mediaPath)
                            difference = 0
                        else :
                            difference = 0

                            debug = open("/Users/dmstk/debug.sh", 'a+')
                            debug.write('EDL: ' + str(edlList[i]) + '\n' + 'Start: ' + str(timestamp) + '\n' + 'Clip:  ' + str(mediaCreation) + '\n' + 'End:   ' + str(timestampFinal) + '\n')

                        pass
                    pass
                pass
            pass
        pass
    else :
        for x in unitList :
            folderName = x.GetName()
            if str(folderName) == str(courseUnit) :
                mediaPool.SetCurrentFolder(x)
                currentFolder = mediaPool.GetCurrentFolder()
                lessonList = currentFolder.GetSubFolderList()
                y = 0
                for x in lessonList :
                    lessonName = x.GetName()
                    lessonListNames.insert(y, lessonName)
                    y += 1
                pass
                if not str(unitLesson) in lessonListNames :
                    mediaPool.AddSubFolder(currentFolder, unitLesson)
                    mediaPool.SetCurrentFolder(str(unitLesson))
                    currentFolder = mediaPool.GetCurrentFolder()
                    for x in os.listdir(rawPath):
                        x = os.path.join(rawPath, x)
                        if not x.startswith('.') and os.path.isdir(x):
                            for y in os.listdir(x):
                                if not y.startswith('R') and not y.startswith('.'):
                                    mediaPath = x + '/' + y
                                    mediaCreation = datetime.datetime.fromtimestamp(os.stat(mediaPath).st_birthtime)
                                    mediaCreation = str(mediaCreation)[0:19]
                                    mediaCreationNumber = time.mktime(datetime.datetime.strptime(mediaCreation,
                                                             "%Y-%m-%d %H:%M:%S").timetuple())
                                    timestampNumber = time.mktime(datetime.datetime.strptime(timestamp,
                                                             "%Y-%m-%d %H:%M:%S").timetuple())
                                    timestampFinalNumber = time.mktime(datetime.datetime.strptime(timestampFinal,
                                                             "%Y-%m-%d %H:%M:%S").timetuple())
                                    if timestampNumber <  mediaCreationNumber :
                                        difference = mediaCreationNumber - timestampNumber
                                    elif timestampNumber >  mediaCreationNumber :
                                        difference = timestampNumber - mediaCreationNumber
                                    pass
                                    if difference < 200 or timestampNumber <= mediaCreationNumber <= timestampFinalNumber:
                                        mediaPath = mediaPath.replace('02 RAW', '04 PROXIES')
                                        mediaPath = mediaPath.replace('.braw', '.mov')
                                        mediaPool.ImportMedia(mediaPath)
                                        importedList.append(mediaPath)
                                        difference = 0
                                    else :
                                        difference = 0

                                        debug = open("/Users/dmstk/debug.sh", 'a+')
                                        debug.write('EDL: ' + str(edlList[i])  + '\n' + 'Start: ' + str(timestamp) + '\n' + 'Clip:  ' + str(mediaCreation) + '\n' + 'End:   ' + str(timestampFinal) + '\n')

                                    pass
                                pass
                            pass
                        pass
                    pass
                else :
                    for x in lessonList :
                        lessonName = x.GetName()
                        if str(lessonName) == str(unitLesson) :
                            mediaPool.SetCurrentFolder(x)
                            currentFolder = mediaPool.GetCurrentFolder()
                            for x in os.listdir(rawPath):
                                x = os.path.join(rawPath, x)
                                if not x.startswith('.') and os.path.isdir(x):
                                    for y in os.listdir(x):
                                        if not y.startswith('R') and not y.startswith('.'):
                                            mediaPath = x + '/' + y
                                            mediaCreation = datetime.datetime.fromtimestamp(os.stat(mediaPath).st_birthtime)
                                            mediaCreation = str(mediaCreation)[0:19]
                                            mediaCreationNumber = time.mktime(datetime.datetime.strptime(mediaCreation,
                                                                     "%Y-%m-%d %H:%M:%S").timetuple())
                                            timestampNumber = time.mktime(datetime.datetime.strptime(timestamp,
                                                                     "%Y-%m-%d %H:%M:%S").timetuple())
                                            timestampFinalNumber = time.mktime(datetime.datetime.strptime(timestampFinal,
                                                                     "%Y-%m-%d %H:%M:%S").timetuple())
                                            if timestampNumber <  mediaCreationNumber :
                                                difference = mediaCreationNumber - timestampNumber
                                            elif timestampNumber >  mediaCreationNumber :
                                                difference = timestampNumber - mediaCreationNumber
                                            pass
                                            if difference < 200 or timestampNumber <= mediaCreationNumber <= timestampFinalNumber:
                                                mediaPath = mediaPath.replace('02 RAW', '04 PROXIES')
                                                mediaPath = mediaPath.replace('.braw', '.mov')
                                                mediaPool.ImportMedia(mediaPath)
                                                importedList.append(mediaPath)
                                                difference = 0
                                            else :
                                                difference = 0


                                                debug = open("/Users/dmstk/debug.sh", 'a+')
                                                debug.write('EDL: ' + str(edlList[i]) + '\n' + 'Start: ' + str(timestamp) + '\n' + 'Clip:  ' + str(mediaCreation) + '\n' + 'End:   ' + str(timestampFinal) + '\n')

                                            pass
                                        pass
                                    pass
                                pass
                            pass
                        pass
                    pass
                pass    
            pass
        pass
        currentFolder = mediaPool.GetCurrentFolder()
    pass
    f.close()
    i += 1
    unitListNames = []
    lessonListNames = []
pass

#   Import all files that wasn't imported by the time EDL comparison to "+_PLEASE CHECK"
#   and all the files that starts with R in "B-ROLL" folder
for x in os.listdir(proxiesPath):
    x = os.path.join(proxiesPath, x)
    if not x.startswith('.') and os.path.isdir(x):
        for y in os.listdir(x):
            if not y.startswith('.') and not y.startswith('R'):
                mediaPath = x + '/' + y
                if not mediaPath in importedList:
                    mediaPool.SetCurrentFolder(notImportedFolder)
                    mediaPath = mediaPath.replace('02 RAW', '04 PROXIES')
                    mediaPath = mediaPath.replace('.braw', '.mov')
                    mediaPool.ImportMedia(mediaPath)
                pass
            pass
            if y.startswith('R'):
                mediaPath = x + '/' + y
                if not mediaPath in importedList:
                    mediaPool.SetCurrentFolder(bRollFolder)
                    mediaPath = mediaPath.replace('02 RAW', '04 PROXIES')
                    mediaPath = mediaPath.replace('.braw', '.mov')
                    mediaPool.ImportMedia(mediaPath)
                pass
            pass
        pass
    pass
pass