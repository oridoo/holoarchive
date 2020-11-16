# holoarchive
Automatization tool written in Python with 2 modules, one for downloading videos from specified text file of YouTube channels using youtube_dl library and second daeomn that captures live streams from the same channel list text file using streamlink.

## Roadmap
- **Global**
  - [x] Status display in command-line
  - [x] Configuration file generation
  - [ ] Conversion to proper database instead of flat-file
  - [ ] Separation into multiple files
  - [ ] Web app to control the daemon and manage the database
  - [ ] REST API for the web app
  - [ ] use objects
  
- **Video downloader**
  - [x] Implementation of status progress bars
  - [ ] Download more than one video at once

- **Stream downloader**
  - [x] Implementation of running stream downloads
  - [x] Capturing video ids using web scraping (*experimental*)
  - [ ] More *proffesional* solution 
  
  