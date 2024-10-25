import time as Time
from datetime import datetime, time
import os
import deeplabcut

class Analyzer:
    def __init__(self, root, started_bar, progress_bar):
        self.root = root
        self.started_bar = started_bar
        self.progress_bar = progress_bar
        self.completed = 0
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
            if self.config is not None:
                self.running = True
                started_bar.start()
                self.main()
            else:
                print("Error: No DLC Config file selected, cannot proceed with analysis")


    def stop(self):
        self.running = False
        started_bar.stop()

    def add_videos(self):
        currdir = os.getcwd()
        tempdir = filedialog.askopenfilename(parent=self.root, initialdir=currdir,
                                             title='Please select more video files to add to queue', filetypes=[('Video Files','*.avi')])
        if len(tempdir) > 0:
            print("You chose: %s" % tempdir)
            nName = tempdir.split('/')
            nName = nName[-1]
            nName = nName.split('.')
            nName = nName[0]
            tmp = [nName, tempdir]
            self.QUEUE.append(tmp)
            print("Added ", nName ,"to processing queue at location: ", tempdir)
            print("Length of queue is now: ", len(self.QUEUE))
            progress_bar.step(100)
            progress = (self.completed / len(self.QUEUE)) * 100
            progress = round(progress)
            self.progress_bar.step(progress)



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

                    self.completed += 1
                    progress = (self.completed / len(self.QUEUE)) * 100
                    progress = round(progress)
                    self.progress_bar.step(progress)
                    print(len(self.QUEUE), " More videos to analyze...")
                else:
                    print("all videos analyzed, select more to continue analysis...")
                    break
            else:
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
            if flg == False and new not in self.QUEUE:
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

            if self.REORGANIZE_SUBFOLDERS is True and self.fpath is not None:
                print("Reorganizing files with the same name as videos into subfolders...")
                self.reorganize_subfolders(self.fpath)
            else:
                print("Error: No folder selected. Cannot reorganize subfolders")

            print("Finding videos...")
            if self.fpath is not None:
                self.find_videos()

            if len(self.QUEUE) != 0:
                print("Analyzing ", len(self.QUEUE), " video files...")
                if self.LISTENER_ACTIVE is True and self.fpath is not None:
                    old = len(self.QUEUE)
                    self.find_videos()
                    new = len(self.QUEUE)
                    if new > old:
                        #more videos found to analyze, need to reset progress bar
                        progress_bar.step(100)
                        progress = (self.completed / len(self.QUEUE)) * 100
                        progress = round(progress)
                        self.progress_bar.step(progress)
                        print("found ", new - old, "more videos to analyze...")

                self.subprocess_video()
            else:
                print("No videos to analyze!")
                self.stop()




if __name__ == '__main__':
    import tkinter as tk
    from tkinter import filedialog
    from tkinter import ttk

    root = tk.Tk()
    root.wm_attributes('-topmost', 1)
    root.geometry("350x350")
    root.title("DeepLabCut Smart Video Analyzer")
    started_bar = ttk.Progressbar(mode="indeterminate", length=200)
    started_bar.place(x=75, y=140)
    progress_bar = ttk.Progressbar(orient=tk.HORIZONTAL, length=200)
    progress_bar.place(x=75, y=290)

    app = Analyzer(root, started_bar, progress_bar)

    start_button = tk.Button(root, text="Run Analysis", command=app.start).pack()
    stop_button = tk.Button(root, text="Stop Analysis", command=app.stop).pack()
    config_button = tk.Button(root, text="Select DLC Config File", command=app.get_file).pack()
    dir_button = tk.Button(root, text="Select Directory of videos to analyze", command=app.get_filepath).pack()
    add_button = tk.Button(root, text="Add more videos to queue", command=app.add_videos).pack()
    root.mainloop()