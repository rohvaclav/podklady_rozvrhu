import os
import sources.config as config

def makeFolder(path):
    if not os.path.exists(path):
        os.mkdir(path)

def setupDirectory():
    makeFolder(config.folder)
    makeFolder(config.folder_programy)
    makeFolder(config.folder_obory)
    makeFolder(config.folder_predmety)
    makeFolder(config.folder_vysledky)
    makeFolder(config.folder_predmetInfo)
    makeFolder(config.folder_ucitele)
    makeFolder(config.folder_rozvrhy)