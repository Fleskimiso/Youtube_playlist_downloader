import os, sys
from bs4 import BeautifulSoup
import requests
import pytube
import re
import moviepy.editor as moviepy_editor
import logging, time ,threading, concurrent.futures
import  eyed3

logging.basicConfig(level=logging.INFO)
#using debug not advised

def download(x_vid):
    print("Downloading")
    path= None
    try:
        path = x_vid[0].download("..\\videos")
    except Exception:
        print(Exception)
        print("Error occured during the download")
        time.sleep(5)
    print("download complete. Path: ")
    print(path)


def scrape_then_download(Youtube_playlist_video_url):
    start_time = time.time()
    video_url = Youtube_playlist_video_url
    videos_titles_and_urls = []
    response = requests.get(video_url)
    threads = []
    failure_titles_and_urls = []
    for i in range(1):
        if response.status_code == requests.codes.ok:
            soup = BeautifulSoup(response.text,'html.parser')
            domain = 'https://www.youtube.com'
            for link in soup.find_all("a", {"dir": "ltr"}):
                href = link.get('href')
                if href.startswith('/watch?'):
                    title = link.string.strip()
                    url = domain + href
                    print(title)
                    print(url + '\n')
                    videos_titles_and_urls.append({
                        'title': title,
                        'url': url
                    })
            response = requests.get(video_url)
    #after getting all the urls, download the video from them
    for dict_elem in videos_titles_and_urls:
        title = dict_elem['title']
        url = dict_elem['url']
        print(" " + title)
        youtube_video = None
        try:
            youtube_video = pytube.YouTube(url)
        except Exception:
            print("Exception occured")
            print("Traceback")
            logging.error("Error during getting the youtube video")
            print(Exception)
            failure_titles_and_urls.append({
                'title': title,
                'url': url
            })
            continue
        youtube_video_audio_only = youtube_video.streams.filter(only_audio = True).all()
        try:
            threads.append(threading.Thread(target=download,args=(youtube_video_audio_only,)))
            threads[len(threads)-1].start()
        except Exception:
            print(Exception)
            failure_titles_and_urls.append({
                'title': title,
                'url': url
            })
            print("Exception occured during download of the url:  " + url)
    are_threads_running = True
    while are_threads_running:
        are_threads_running = False
        for thread in threads:
            if thread.is_alive():
                are_threads_running = True
                break;
    print("Failure urls and their video titles likewise: ")
    for failure in failure_titles_and_urls:
        print(failure)
    print("Total time of downloading:  " + str(time.time() - start_time))

def write_to_drive_mp3_file(path_elem):
    start_time = time.time()
    print("Converting to mp3 started") #TODO exception handling
    audio_clip = moviepy_editor.AudioFileClip(path_elem['source_path'])
    audio_clip.write_audiofile(path_elem['destination_path'])
    print("File : " + path_elem['destination_path'])
    print('Converting finished, Total time of this file:  ' + str(time.time() - start_time))

def change_tags(path_elem, mannual_tags_rename):
    print('\n')
    print("Renaming: ")
    print(path_elem)
    filename = os.path.splitext(os.path.split(path_elem)[1])[0]
    index = filename.rfind('-')
    author = filename[0:index]
    title = filename[index+1:]

    if author.find('&amp') is not -1:
        logging.info(author.replace('&amp', '&'))
        author = author.replace('&amp', '&')

        # title check
    if title.find('&amp') is not -1:
        logging.info(title.replace('&amp', '&'))
        title = title.replace('&amp', '&')

    print( "Default Author: "  + author)
    print( "Default title: " +  title)


    audiofile = None
    try:
        audiofile = eyed3.load(path_elem)
        if mannual_tags_rename == False:

            audiofile.tag.artist = author
            audiofile.tag.title = title

        elif mannual_tags_rename == True:
            temp_author = input("Author (n to left default):  ")
            if temp_author != 'n':
                author = temp_author
            temp_title = input("Title (n to left default):  ")
            if temp_title != 'n':
                title = temp_title
            audiofile.tag.artist = author
            audiofile.tag.title = title
        audiofile.tag.save()
        print("Renaming ended")
        # now setting the track titles and artist names, - is probably the delimeter TODO advanced analysis of the track
    except Exception:
        logging.error("ERROR Could not load the Audio file")
    finally:
        logging.info(filename)


def convert(absolute_path: str = None):
    start_time = time.time()
    converting_time = 0
    mp3_path = '..\\music' #default path
    if absolute_path != None:
        mp3_path = absolute_path #not granted to be valid path
        logging.info(absolute_path)
        logging.info("Is absolute? " + str(os.path.isabs(absolute_path)))

        if os.path.isabs(absolute_path):
            #can download path should be valid
            mp3_path = absolute_path
    mp4_path = "..\\videos"
    music_files_paths = []
    for file in os.listdir(mp4_path):
        if re.search('.mp4', file):
            music_files_paths.append({
                'source_path': os.path.join(mp4_path, file),
                'destination_path': None
            })
            print(os.path.join(mp4_path, file)) #debugging purposes
    for paths_elem in music_files_paths:
        file_name = os.path.split(paths_elem['source_path'])[1]
        paths_elem['destination_path'] = os.path.join(mp3_path, os.path.splitext(file_name)[0] + '.mp3' )
        print( "destination path: " + paths_elem['destination_path'])
    #actually converting the elements
    convert_to_mp3 = input("Convert to mp3  y/n")
    manuall_tag_rename_bool = False
    if convert_to_mp3 == 'y':
        futures = []
        if len(music_files_paths) > 40:
            rest_of_futures = []
            end_index = 40

            # will do it using concurennt.futuree.ProcessPoolExecutor
            with concurrent.futures.ProcessPoolExecutor(max_workers=end_index) as executor:
                for i in range(end_index):
                    futures.append(executor.submit(write_to_drive_mp3_file, music_files_paths[i]))
                    print("File to  convert:  " + music_files_paths[i]['destination_path'])
            logging.info("First 40 files should be converted. ")
            with concurrent.futures.ProcessPoolExecutor(max_workers=len(music_files_paths) - end_index) as executor:
                for i in range(len(music_files_paths) - end_index):
                    rest_of_futures.append(executor.submit(write_to_drive_mp3_file,music_files_paths[i+end_index]))
                    print("File to  convert:  " + music_files_paths[i+end_index]['destination_path'])
        else:
            with concurrent.futures.ProcessPoolExecutor(max_workers=len(music_files_paths)) as executor:
                for paths_elem in music_files_paths:
                    futures.append(executor.submit(write_to_drive_mp3_file, paths_elem))
                    print("File to  convert:  " + paths_elem['destination_path'])

        print("Converting should ended. ")
        converting_time = time.time() - start_time
        print("Converting took " + str(converting_time))
        start_time = time.time() #now it will check the converting time
        #Renaming the tags
        manuall_tag_rename = input("Do you want to rename tags by yourself? y/n (will set the default - not granted to be right) ")
        if manuall_tag_rename == 'y':
            manuall_tag_rename_bool = True
        music_files_paths_to_edit = []
        for paths_elem in music_files_paths:
            music_files_paths_to_edit.append(paths_elem['destination_path']) #TODO clean the code
        #calling the change tags function
        for path in music_files_paths_to_edit:
            change_tags(path, manuall_tag_rename_bool)
        #the code below is basically the same
    elif convert_to_mp3 == 'n':
        logging.info("Converting function did basically nothing")
    print("Renaming  took " + str(time.time() - start_time))
    print("While converting took " + str(converting_time))

#function that deletes videos in relative ..\\videos directory
def remove_videos():
    path = '..\\videos'
    temporary_path = None
    for file in os.listdir(path):
        temporary_path= os.path.join(path,file)
        print("Deleting ", temporary_path)
        os.remove(temporary_path)
    print("Deleting completed")

def edit_tags(path):
    temporary_path = None
    if path == None:
        path = '..\\music'
    else:
        pass
        # TODO path validation thought it is not necessary
    auto_rename = input("Do you want to rename automatically (in case it wasn't done earlier) ?  (y/n) ")
    manuall_rename_bool = True
    if auto_rename == 'y':
        manuall_rename_bool = False
    else:
        manuall_rename_bool = True
    for file in os.listdir(path):
        temporary_path = os.path.join(path, file)
        if temporary_path.endswith('.mp3'):
            change_tags(temporary_path, manuall_rename_bool)

def main():
    print("Type 1 to download videos")
    print("Type 2 to convert videos to mp3.  ")
    print("Type 3 to remove all videos from  ..\\videos directory")
    print("Type 4 to only edit tags of mp3 files in given directory")
    decision = int(input())
    if decision == 1:
        print("Paste youtube playlist URL: ")
        url = input()
        scrape_then_download(url)
    elif decision == 2:
        print("Do you want to specify target path(absolute)? \n0-no (default) , 1-yes \n(where converted files are going to be in the end )  ")
        path_bool = int(input())
        if path_bool == 0:
            convert()
        elif path_bool == 1:
            print("Type valid absolute path: ")
            path = input()
            convert(path)
    elif decision == 3:
        remove_videos()
    elif decision == 4:
        path = input("Give path to directory containing mp3 files. (n - will use the default ..\\music dir ) ")
        if path == 'n':
            path = '..\\music'
        edit_tags(path)

if __name__ == '__main__':
    logging.info("Using info")
    logging.debug("Using debug")
    main()

