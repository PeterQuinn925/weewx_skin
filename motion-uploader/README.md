# motion-uploader
~~Motion Google Drive Uploader
~~http://jeremyblythe.blogspot.com ~~
No longer using Motion Uploader. I couldn't get it to work right with Ubuntu on Raspi3. It kept running out of memory when uploading large files, like the weewx db. Small files were fine. So, I found the pyDrive library and used that instead.

Updated weewx_backup to use the new script and it's good to go. 

https://pythonhosted.org/PyDrive/
sudo pip install --upgrade google-api-python-client


For weewx to run daily use a CRON job such as:

7 2 * * *  /home/pi/motion-uploader/weewx_backup
