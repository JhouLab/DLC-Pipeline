import tkinter
from tkinter import filedialog
import os
import multiprocessing
import keyboard

VIDEO_TYPE = ".avi"
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


def subprocess_video(pauseEvent, config, queue):
    import deeplabcut
    while True:
        if pauseEvent.is_set():
            pauseEvent.wait()
        else:
            if len(queue) != 0:
                video = queue.pop(0)
                deeplabcut.analyze_videos(config= config, videos= video[1], save_as_csv= True, videotype=VIDEO_TYPE)
                deeplabcut.plot_trajectories(config, video[1])
                deeplabcut.create_labeled_video(config=config, videos=video[1], videotype= VIDEO_TYPE, draw_skeleton=True)
                print(len(queue), " More videos to analyze...")
            else:
                print("all videos analyzed, analysis can be closed now with 'q'...")
                exit(0)



if __name__ == "__main__":
    print("Starting DLC Analysis pipeline...")
    print("Select model config file: ")
    config = get_file()
    print("Select videos to analyze: ")
    fpath = get_filepath()

    queue = []
    analyzed = []
    print("Finding videos...")
    for root, dirs, files in os.walk(fpath):
        for name in files:
            if name.endswith(VIDEO_TYPE):
                nName = name.split('.')
                nName = nName[0]
                queue.append([nName, os.path.join(root, name)])
            if name.endswith(".csv"):
                analyzed.append(name)

    print("Found ", len(queue), " videos to analyze")

    if REANALYZE == False:
        if len(analyzed) != 0:
            tmp = []
            for a in range(len(queue)):
                flg = False
                for b in range(len(analyzed)):
                    if (queue[a][0] in analyzed[b]) and ("DLC" in analyzed[b]):
                        print("Eliminated: ", queue[a][0])
                        flg = True
                        break
                if flg == False:
                    tmp.append(queue[a])
            queue = tmp


    print("Analyzing ", len(queue), " video files...")

    if len(queue) != 0:
        pauseEvent = multiprocessing.Event()
        print("Starting Analysis...")
        p = multiprocessing.Process(target=subprocess_video, args=(pauseEvent, config, queue), daemon = True)
        p.start()
        print("==Press 'p' to pause processing, 'r' to restart, and 'q' to quit==")
        while p.is_alive():
            if keyboard.is_pressed('p'):
                pauseEvent.set()
            if keyboard.is_pressed('r'):
                pauseEvent.clear()
            if keyboard.is_pressed('q'):
                p.terminate()
                break


    else:
        print("No videos to analyze!")
