import time as Time
from datetime import datetime, time
import os
import multiprocessing
from multiprocessing import Manager
import keyboard
import deeplabcut

class Analyzer:
    def __init__(self, root):
        self.root = root
        self.running = False
        self.config = None
        self.fpath = None
        self.main()
        self.QUEUE = []
        self.VIDEO_LIST = []
        self.CSV_LIST = []

    VIDEO_TYPE = ".avi"
    # Boolean flag to set the processing mode. When active, the script will listen for changes in the given directory and analyze only new videos which havent been analyzed yet
    # forces REANALYZE to False
    LISTENER_ACTIVE = True
    # Pauses the analysis during working hours (9am-5pm). For use on machines which are also used as workstations. Will resume analysis after the pause.
    PAUSE_WORK_HOURS = False
    REANALYZE = False
    REORGANIZE_SUBFOLDERS = True
    # list of filetypes to ignore when reorganization is True
    IGNORE_LIST = [".plx", ".fig", ".jpg"]

    if LISTENER_ACTIVE == True:
        REANALYZE = False

    def start(self):
        if not self.running:
            self.running = True
            self.main()

    def stop(self):
        self.running = False

    def get_filepath(self):
        try:
            currdir = os.getcwd()
            tempdir = filedialog.askdirectory(parent=self.root, initialdir=currdir,
                                              title='Please select the directory of files to process')
            if len(tempdir) > 0:
                print("You chose: %s" % tempdir)
            else:
                raise Exception("Error: No file was selected")
        except:
            tempdir = self.get_file()
        self.fpath = tempdir

    def get_file(self):
        try:
            currdir = os.getcwd()
            tempdir = filedialog.askopenfilename(parent=self.root, initialdir=currdir,
                                                 title='Please select the DeepLabCut model config')
            if len(tempdir) > 0:
                print("You chose: %s" % tempdir)
            else:
                raise Exception("Error: No file was selected")
        except:
            tempdir = self.get_file()
        self.config = tempdir

    def subprocess_video(self):
        import deeplabcut
        while True:
            if self.running is True:
                if len(self.QUEUE) != 0:
                    print("Analyzing ", self.QUEUE[0][0])
                    video = self.QUEUE.pop(0)
                    deeplabcut.analyze_videos(config=self.config, videos=video[1], save_as_csv=True, videotype=self.VIDEO_TYPE)
                    deeplabcut.plot_trajectories(self.config, video[1])
                    deeplabcut.create_labeled_video(config=self.config, videos=video[1], videotype=self.VIDEO_TYPE, draw_skeleton=True)
                    print(len(self.QUEUE), " More videos to analyze...")
                else:
                    print("all videos analyzed, select more to continue analysis...")
                    break
<<<<<<< Updated upstream
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
=======
            else:
>>>>>>> Stashed changes
                break

    def find_videos(self):
        # look for new videos to add to list
        new = []
        for root, dirs, files in os.walk(self.fpath):
            for name in files:
                if name.endswith(self.VIDEO_TYPE) and (name not in self.VIDEO_LIST):
                    nName = name.split('.')
                    nName = nName[0]
                    tmp = [nName, os.path.join(root, name)]
                    new.append(tmp)
                    self.VIDEO_LIST.append(name)
                if (name.endswith(".csv")) and (name not in self.CSV_LIST):
                    self.CSV_LIST.append(name)

        # cross refrence new videos to our complete list of CSV files. If no corresponding CSV file is found, add to queue for analysis
        for a in range(len(new)):
            flg = False
            if self.REANALYZE == False:
                for b in range(len(self.CSV_LIST)):
                    if (new[a][0] in self.CSV_LIST[b]) and ("DLC" in self.CSV_LIST[b]):
                        flg = True
                        break
            if flg == False:
                self.QUEUE.append(new[a])

    def reorganize_subfolders(self, fpath):
        for root, dirs, files in os.walk(fpath):
            for file in files:
                incorrect = False

                # ignore files that end any of the ignored file types
                for a in self.IGNORE_LIST:
                    if file.endswith(a):
                        incorrect = True

                nName = file.split("_")
                nName = nName[0:4]
                # if any part of the string does not contain any of the correct information
                for a in nName:
                    if a == "" or a == " ":
                        incorrect = True

                if incorrect == False:
                    nName = '_'.join(nName)
                    # see if folder exists at this level or the file is already in correct directory
                    if nName not in root:
                        dirPath = os.path.join(root, nName)
                        if not os.path.exists(dirPath):
                            os.makedirs(dirPath)
                        os.rename(os.path.join(root, file), os.path.join(root, nName, file))

    def main(self):
        if self.running:
            print("Starting DLC Analysis pipeline...")

            if self.REORGANIZE_SUBFOLDERS == True:
                print("Reorganizing files with the same name as videos into subfolders...")
                self.reorganize_subfolders(self.fpath)

            print("Finding videos...")
            self.find_videos()
            print("Analyzing ", len(self.QUEUE), " video files...")

            if len(self.QUEUE) != 0:
                print("Starting Analysis...")
                print("Analyzing ")
                if self.LISTENER_ACTIVE is True:
                    old = len(self.QUEUE)
                    self.find_videos()
                    new = len(self.QUEUE)
                    if new > old:
                        print("found ", new - old, "more videos to analyze...")

                self.subprocess_video()
            else:
                print("No videos to analyze!")

if __name__ == '__main__':
    import tkinter as tk
    from tkinter import filedialog

    root = tk.Tk()
    root.wm_attributes('-topmost', 1)
    root.geometry("350x350")
    root.title("DeepLabCut Smart Video Analyzer")
    app = Analyzer(root)
    start_button = tk.Button(root, text="Run Analysis", command=app.start).pack()
    stop_button = tk.Button(root, text="Stop Analysis", command=app.stop).pack()
    config_button = tk.Button(root, text="Select DLC Config File", command=app.get_file).pack()
    dir_button = tk.Button(root, text="Select Directory of videos to analyze", command=app.get_filepath).pack()
    root.mainloop()