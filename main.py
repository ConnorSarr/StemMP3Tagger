import os
import tkinter as tk
from tkinter import filedialog as fd
import requests
from thefuzz import fuzz
import survey
import subprocess
import music_tag as mt
import time
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(client_id="YOUR_CLIENT_ID",
                                                           client_secret="YOUR_CLIENT_SECRET"))

root = tk.Tk()
root.withdraw()

BASEPATH = os.path.dirname(os.path.realpath(__file__))

songCatalog = {}
albumImages = {}

fullFilePaths = []
fileNames = []

matchList = {}

def normalizefilename(fn):
    validchars = "-_.() "
    out = ""
    for c in fn:
      if str.isalpha(c) or str.isdigit(c) or (c in validchars):
        out += c
      else:
        out += ""
    return out
    
def get_filepaths(directory): #method is from StackOverflow
    """
    This function will generate the file names in a directory 
    tree by walking the tree either top-down or bottom-up. For each 
    directory in the tree rooted at directory top (including top itself), 
    it yields a 3-tuple (dirpath, dirnames, filenames).
    """
    file_paths = []  # List which will store all of the full filepaths.
    fileNames = []

    # Walk the tree.
    for root, directories, files in os.walk(directory):
        for filename in files:
            # Join the two strings in order to form the full filepath.
            filepath = os.path.join(root, filename)
            if "inst" in filename.lower() or "tv" in filename.lower() or "aca" in filename.lower():
                file_paths.append(filepath)  # Add it to the list.
                fileNames.append(filename)

    return file_paths,fileNames

def getArtistReleases(artistName):
    global songCatalog
    global albumImages
    
    artistResponse = sp.search(type="artist",q=artistName) #get the artist ID from a search
    artistID = artistResponse['artists']['items'][0]['id']
    
    discographyRes = sp.artist_albums(artist_id=artistID,limit=50,include_groups="album,single") #search up all albums from an artist ID
    albumIDS = []
    for album in discographyRes['items']:
        albumIDS.append(album['id'])
    
    splitRequests = [albumIDS[i:i+20] for i in range(0,len(albumIDS),20)] 

    for idList in splitRequests:
        albumRes = sp.albums(albums=idList)
        
        for album in albumRes['albums']:
            albumName = album['name']
            albumImage = album['images'][0]['url']
            albumImages[albumName] = albumImage
            
            for track in album['tracks']['items']:
                trackArtists = []
                for artist in track['artists']:
                    trackArtists.append(artist['name'])
                    
                trackName = track['name']
                trackNumber = track['track_number']
                trackTotalNumber = album['total_tracks']
                
                try:
                    trackGenre = album['genres'][0]
                except:
                    trackGenre = ""
                    
                trackLabel = album['label']
                
                songCatalog[f"{trackName} - {albumName}"] = [trackName,albumName,trackArtists,trackNumber,trackTotalNumber,trackGenre,trackLabel]
        
def findMatchesForFile():
    global matchList
    for fileName in fileNames: #go through every file name in the music selection
        resultDict = {}
        
        for songName in songCatalog.keys():
            if songName.lower() in fileName.lower().replace("_"," ").replace(".wav",""):
                nameScore = 100
            else:
                ratios = {} 
                
                nameScore1 = int(fuzz.token_sort_ratio(songName,fileName))
                ratios[nameScore1] = "tsrt"
                nameScore2 = int(fuzz.token_set_ratio(songName,fileName))
                ratios[nameScore2] = "tst"
                nameScore3 = int(fuzz.ratio(songName,fileName))
                ratios[nameScore3] = "rt"
                nameScore4 = int(fuzz.partial_ratio(songName,fileName))
                ratios[nameScore4] = "prt"
                
                myKeys = list(ratios.keys())
                myKeys.sort(reverse=True)
                sortedRatios = {i: ratios[i] for i in myKeys}
            
                match list(sortedRatios.values())[0]:
                    case "tsrt":
                        nameScore = int(fuzz.token_sort_ratio(songName,fileName))
                    case "tst":
                        nameScore = int(fuzz.token_set_ratio(songName,fileName))
                    case "rt":
                        nameScore = int(fuzz.ratio(songName,fileName))
                    case "prt":
                        nameScore = int(fuzz.partial_ratio(songName,fileName))
                
            resultDict[nameScore] = songName
            
        scoreKeys = list(resultDict.keys())
        scoreKeys.sort(reverse=True)
        sortedScores = {i: resultDict[i] for i in scoreKeys}
        
        winningresult = list(sortedScores.values())[0]
        matchList[fullFilePaths[fileNames.index(fileName)]] = winningresult
    
def changeAnySongs():
    promptOptions = []
    for filePath,result in matchList.items():
        resultDetails = songCatalog[result]
        detailsToUser = f"{result} - {','.join(resultDetails[2])}"
        promptOptions.append(f"{fileNames[fullFilePaths.index(filePath)]} => {detailsToUser}")
    
    userSelection = survey.routines.basket("Please select any changes: ", options=promptOptions)
    
    for selectionIndex in userSelection:
        filePathToChange = list(matchList)[selectionIndex]
        
        songOptions = []
        for songName, songDetails in songCatalog.items():
            songOptions.append(f"{songName} - {','.join(songDetails[2])}")
        
        selectedSongIndex = survey.routines.select(f"What song should {fileNames[fullFilePaths.index(filePathToChange)]} be?",options=songOptions)
        songKeys = list(songCatalog.keys())
        newSong = songKeys[selectedSongIndex]
        
        matchList[filePathToChange] = newSong
        
def getAllCoverArts():
    for songFilePath, songName in matchList.items():
        coverArtFolder = os.path.join(BASEPATH,"coverart")
        if os.path.exists(coverArtFolder) == False:
            os.makedirs(coverArtFolder)

        songDetails = songCatalog[songName]
        albumName = songDetails[1]
        
        coverArtPath = os.path.join(coverArtFolder,f"{normalizefilename(albumName)} - ART.jpeg")
        if os.path.exists(coverArtPath) == False:
            albumImageLink = albumImages[albumName]
            albumImageReq = requests.get(url=albumImageLink,stream=True)
            
            with open(coverArtPath,"wb+") as file:
                file.write(albumImageReq.content)

def convertSongs():
    convertedSongDirectory = fd.askdirectory(mustexist=True)
    for songFilePath, songName in matchList.items():
        songDetails = songCatalog[songName]
        artistPrettyFormat = songDetails[2][0]
        artistDirectory = os.path.join(convertedSongDirectory,artistPrettyFormat,normalizefilename(songDetails[1]))
        
        if os.path.exists(artistDirectory) == False:
            os.makedirs(artistDirectory)
        
        type = ""
        if "inst" in fileNames[fullFilePaths.index(songFilePath)].lower():
            type = "(Instrumental)"
        elif "tv" in fileNames[fullFilePaths.index(songFilePath)].lower():
            type = "(TV Track)"
        elif "aca" in fileNames[fullFilePaths.index(songFilePath)].lower():
            type = "(Acapella)"
        
        outputFileName = os.path.join(artistDirectory,f"{normalizefilename(songDetails[0])} - {normalizefilename(songDetails[1])} - {normalizefilename('-'.join(songDetails[2]))} - {type}.mp3")
        
        print(f"{normalizefilename(songDetails[0])} - {normalizefilename(songDetails[1])} - {normalizefilename('-'.join(songDetails[2]))} - {type}.mp3")
        command = f'ffmpeg -loglevel error -i "{songFilePath}" -vn -ar 44100 -ac 2 -b:a 320k "{outputFileName}"'
        subprocess.call(command,shell=True)
        
        addMetadata(outputFileName,songName,type,artistPrettyFormat)

def addMetadata(mp3Path, songName, type, artistFormat):
    songDetails = songCatalog[songName]
    coverArtPath = os.path.join(BASEPATH, "coverart", f"{normalizefilename(songDetails[1])} - ART.jpeg")
    
    mainSong = mt.load_file(mp3Path)
    mainSong['title'] = f"{songDetails[0]} {type}"
    mainSong['artist'] = songDetails[2][0]
    mainSong['album'] = f"{songDetails[1]} {type.replace(')','s)')}"
    mainSong['tracknumber'] = int(songDetails[3])
    
    with open(coverArtPath, "rb") as file:
        mainSong['artwork'] = file.read()
        
    mainSong.save()
        
def main():
    global fullFilePaths
    global fileNames
    directoryPath = fd.askdirectory(mustexist=True)
    fullFilePaths,fileNames = get_filepaths(directoryPath)

    artistList = input("What artists do you have materials for? (seperated by commas): ").split(",")
    for artist in artistList:
        getArtistReleases(artist)
    
    findMatchesForFile()
    changeAnySongs()
    getAllCoverArts()
    convertSongs()
    
if __name__ == "__main__":
    main()