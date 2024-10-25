import time as Time
from datetime import datetime, time
import tkinter
from tkinter import filedialog
import os
import multiprocessing
from multiprocessing import Manager
import keyboard

#list of filetypes to ignore
IGNORE_LIST = [".plx", ".fig", ".jpg"]
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

#looks at all files in a given level, and combines them into new or existing folders at the same level
def reorganize_subfolders(fpath):
    for root, dirs, files in os.walk(fpath):
        for file in files:
            incorrect = False

            #ignore files that end any of the ignored file types
            for a in IGNORE_LIST:
                if file.endswith(a):
                    incorrect = True

            nName = file.split("_")
            nName = nName[0:4]
            #if any part of the string does not contain any of the correct information
            for a in nName:
                if a == "" or a == " ":
                    incorrect = True

            if incorrect == False:
                nName = '_'.join(nName)
                #see if folder exists at this level or the file is already in correct directory
                if nName not in root:
                    dirPath = os.path.join(root, nName)
                    if not os.path.exists(dirPath):
                        os.makedirs(dirPath)
                    os.rename(os.path.join(root, file), os.path.join(root, nName, file))





def main():
    fpath = get_filepath()
    reorganize_subfolders(fpath)

main()