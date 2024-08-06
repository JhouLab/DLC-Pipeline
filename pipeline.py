import time as Time
from datetime import datetime, time
import tkinter
from tkinter import filedialog
import os
import multiprocessing
from multiprocessing import Manager
import keyboard

VIDEO_TYPE = ".avi"
#Boolean flag to set the processing mode. When active, the script will listen for changes in the given directory and analyze only new videos which havent been analyzed yet
#forces REANALYZE to False
LISTENER_ACTIVE = True
#Pauses the analysis during working hours (9am-5pm). For use on machines which are also used as workstations. Will resume analysis after the pause.
PAUSE_WORK_HOURS = True
REANALYZE = False

if LISTENER_ACTIVE == True:
    REANALYZE = False

root = tkinter.Tk()
root.withdraw()

def get_filepath():
    try:
        currdir = os.getcwd()
        tempdir = filedialog.askdirectory(parent=root, initialdir=currdir, title='Please select DeepLabCut directory')
        if len(tempdir) > 0:
            print("You chose: %s" % tempdir)
        else:
            raise Exception("Error: No file was selected")
    except:
        tempdir = get_file()
    return tempdir


def get_file():
    try:
        currdir = os.getcwd()
        tempdir = filedialog.askopenfilename(parent=root, initialdir=currdir, title='Please select the DeepLabCut model config')
        if len(tempdir) > 0:
            print("You chose: %s" % tempdir)
        else:
            raise Exception("Error: No file was selected")
    except:
        tempdir = get_file()
    return tempdir


def subprocess_video(QUEUE, pauseEvent, config):
    import deeplabcut
    while True:
        if pauseEvent.is_set():
            pauseEvent.wait()
        else:
            if len(QUEUE) != 0:
                print("==Press 'p' to pause processing, 'r' to restart, and 'q' to quit==")
                print("Analyzing ", QUEUE[0][0])
                video = QUEUE.pop(0)
                deeplabcut.analyze_videos(config= config, videos= video[1], save_as_csv= True, videotype=VIDEO_TYPE)
                deeplabcut.plot_trajectories(config, video[1])
                deeplabcut.create_labeled_video(config=config, videos=video[1], videotype= VIDEO_TYPE, draw_skeleton=True)
                Time.sleep(20)
                print(len(QUEUE), " More videos to analyze...")
            else:
                print("all videos analyzed, analysis can be closed now with 'q'...")
                exit(0)

def find_videos(QUEUE, VIDEO_LIST, CSV_LIST, fpath):
    #look for new videos to add to list
    new = []
    for root, dirs, files in os.walk(fpath):
        for name in files:
            if name.endswith(VIDEO_TYPE) and (name not in VIDEO_LIST):
                nName = name.split('.')
                nName = nName[0]
                tmp = [nName, os.path.join(root, name)]
                new.append(tmp)
                VIDEO_LIST.append(name)
            if (name.endswith(".csv")) and (name not in CSV_LIST):
                CSV_LIST.append(name)

    #cross refrence new videos to our complete list of CSV files. If no corresponding CSV file is found, add to queue for analysis
    for a in range(len(new)):
        flg = False
        if REANALYZE == False:
            for b in range(len(CSV_LIST)):
                if (new[a][0] in CSV_LIST[b]) and ("DLC" in CSV_LIST[b]):
                    flg = True
                    break
        if flg == False:
            QUEUE.append(new[a])


def subprocess_listener(QUEUE, VIDEO_LIST, CSV_LIST, pauseEvent, fpath):
    while True:
        if LISTENER_ACTIVE == True:
            prev = len(QUEUE)
            find_videos(QUEUE, VIDEO_LIST, CSV_LIST, fpath)
            rec = len(QUEUE)
            if (rec > prev):
                print("Found ", (rec-prev), " more videos to analyze")
            Time.sleep(5)
        if PAUSE_WORK_HOURS == True:
            now = datetime.now()
            if time(9, 0) <= now.time() <= time(17, 0):
                print("Suspending analysis during working hours...")
                pauseEvent.set()
            elif pauseEvent.is_set():
                print("Restarting analysis...")
                pauseEvent.clear()
            Time.sleep(60)


if __name__ == "__main__":
    print("Starting DLC Analysis pipeline...")
    print("Select model config file: ")
    config = get_file()
    print("Select videos to analyze: ")
    fpath = get_filepath()

    manager = multiprocessing.Manager()
    QUEUE = manager.list()
    VIDEO_LIST = manager.list()
    CSV_LIST = manager.list()
    print("Finding videos...")
    find_videos(QUEUE, VIDEO_LIST, CSV_LIST, fpath)
    print("Analyzing ", len(QUEUE), " video files...")

    if len(QUEUE) != 0:
        pauseEvent = multiprocessing.Event()
        print("Starting Analysis...")
        if LISTENER_ACTIVE == True or PAUSE_WORK_HOURS == True:
            l = multiprocessing.Process(target=subprocess_listener, args=(QUEUE, VIDEO_LIST, CSV_LIST, pauseEvent, fpath), daemon= True)
            l.start()
        p = multiprocessing.Process(target=subprocess_video, args=(QUEUE, pauseEvent, config), daemon= True)
        p.start()
        while p.is_alive():
            if keyboard.is_pressed('p'):
                pauseEvent.set()
            if keyboard.is_pressed('r'):
                pauseEvent.clear()
            if keyboard.is_pressed('q'):
                if LISTENER_ACTIVE == True or PAUSE_WORK_HOURS == True:
                    l.terminate()
                p.terminate()
                break

    else:
        print("No videos to analyze!")
