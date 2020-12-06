#!/usr/bin/python3

from pydrive.drive import GoogleDrive 
from pydrive.auth import GoogleAuth
from pydrive.files import GoogleDriveFileList 
   
# For using listdir() 
import os 
   
  
# Below code does the authentication 
# part of the code 
gauth = GoogleAuth() 
  
# Creates local webserver and auto 
# handles authentication. 
#gauth.LocalWebserverAuth()        
gauth.CommandLineAuth()
drive = GoogleDrive(gauth) 
   
# replace the value of this variable 
# with the absolute path of the directory 
fname = 'weewx_backup.sdb'
#fname = 'test.txt'
fullpath = "/var/lib/weewx/" + fname
#fullpath = "/home/pi/gdrive_backup/" + fname

folderid='0B3LVMohPW7riNE91T1ZuU2pJeFk' #weewx database backup


f = drive.CreateFile({'title':fname, 'parents': [{"id": folderid}]}) 
f.SetContentFile(fullpath) 
f.Upload() 
  
    # Due to a known bug in pydrive if we  
    # don't empty the variable used to 
    # upload the files to Google Drive the 
    # file stays open in memory and causes a 
    # memory leak, therefore preventing its  
    # deletion 
f = None
