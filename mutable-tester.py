#!/usr/bin/python3
################################################################
#              Projects: mutable-tester
#              Author:   Sébastien Valat
#              Date:     01/2019
#              License:  CeCILL-C
#              Version:  0.0
################################################################

#imports
import configparser
import glob
import os
import re
import random

#Config class
class Config:
    def __init__(self, path: str):
        config = configparser.ConfigParser()
        config.read(path)
        self.projectName = config["project"]["name"]
        self.sourcesPaths = config["sources"]["paths"]
        self.sourcesPatterns = config["sources"]["patterns"]
        self.coverageFile = config["coverage"]["file"]
        self.buildDirectory = config["build"]["directory"]
        self.buildCommand = config["build"]["command"]
        self.testDirectory = config["test"]["directory"]
        self.testCommand = config["test"]["command"]

#class to track coverage stats
class Coverage:
    def __init__(self):
        self.maps = {}
        self.loaded = False

    def load(self, path: str):
        self.maps = {}
        regexpFile = re.compile("^SF:(.*)\n")
        regexpLine = re.compile("^DA:([0-9]+),[0-9]+")
        filename = ''
        with open(path, 'r') as fp:
            content = fp.readlines()
            for line in content:
                resFile = regexpFile.match(line)
                resLine = regexpLine.match(line)
                if resFile:
                    filename = resFile.group(1)
                    self.maps[filename] = {}
                elif resLine:
                    lineno = resLine.group(1)
                    self.maps[filename][lineno] = True
            self.loaded = True

    def hasFile(self, filename) -> bool:
        if self.loaded:
            return (filename in self.maps)
        else:
            return True

    def hasFileLine(self, filename: str, line: int) -> bool:
        if not self.loaded:
            return True
        elif not filename in self.maps:
            return False
        elif not str(line) in self.maps[filename]:
            return False
        else:
            return True

class Mutator:
    def __init__(self):
        self.locusList = []
        self.mutations = {
            " == ": [" != ", " <= ", " < ", " >= ", " > "],
            " != ": [" == ", " <= ", " < ", " >= ", " > "],
            " <= ": [" == ", " != ", " < ", " >= ", " > "],
            " >= ": [" == ", " <= ", " < ", " != ", " > "],
            " < ": [" == ", " != ", " <= ", " >= ", " > "],
            " > ": [" == ", " <= ", " < ", " != ", " >= "],
            " && ": [" || "],
            " || ": [" && "],
            "++": ['--'],
            "--": ["++"],
            "+=": ["-="],
            "-=": ["+="],
            " + ": [" - ", " * ", " / "],
            " - ": [" + ", " * ", " / "],
            # " * ": [" + ", " - ", " / "],
            # " / ": [" + ", " - ", " * "],
            "0":['1', '2', '3', '4', '5', '6', '7', '8', '9'],
            "1":['0', '2', '3', '4', '5', '6', '7', '8', '9'],
            "2":['1', '0', '3', '4', '5', '6', '7', '8', '9'],
            "3":['1', '2', '0', '4', '5', '6', '7', '8', '9'],
            "4":['1', '2', '3', '0', '5', '6', '7', '8', '9'],
            "5":['1', '2', '3', '4', '0', '6', '7', '8', '9'],
            "6":['1', '2', '3', '4', '5', '0', '7', '8', '9'],
            "7":['1', '2', '3', '4', '5', '6', '0', '8', '9'],
            "8":['1', '2', '3', '4', '5', '6', '7', '0', '9'],
            "9":['1', '2', '3', '4', '5', '6', '7', '8', '0'],
        }

    def parseLocus(self, filename: str, lineno: int, line: str, pattern: str):
        cursor = 0
        while cursor >= 0:
            cursor = line.find(pattern, cursor)
            if cursor >= 0:
                self.locusList.append({
                    'pattern': pattern,
                    'cursor': cursor,
                    'lineno': lineno,
                    'filename': filename,
                })
                cursor += 1

    def loadFile(self, filename: str, coverage: Coverage):
        #if present in coverage
        if not coverage.hasFile(filename):
            return

        #load
        with open(filename, "r") as fp:
            lineno = 0
            for line in fp.readlines():
                lineno += 1
                if coverage.hasFileLine(filename, lineno):
                    for mut in self.mutations:
                        self.parseLocus(filename, lineno, line, mut)
            print(self.locusList)

    def mutate_file(self, locus, dest):
        print(locus['filename'], locus['lineno'], locus['pattern'], dest)
        
        #backup
        with open(locus['filename'], 'r') as fp:
            self.backup_filename = locus['filename']
            self.backup = fp.read()

        #patch
        lines = self.backup.split('\n')

        #loop
        with open(locus['filename'], 'w') as fp:
            cursor = 0
            for line in lines:
                cursor += 1
                if cursor == locus['lineno']:
                    print(line)
                    line = line[0:locus['cursor']] + dest + line[locus['cursor'] + len(locus['pattern']):]
                    print(line)
                fp.write(line + "\n")

    def mutate(self):
        #select source
        sel = random.randrange(0, len(self.locusList))

        #extract info
        locus = self.locusList[sel]
        pattern = locus['pattern']
        mutations = self.mutations[pattern]

        #select dest
        dest = random.randrange(0, len(mutations))

        #apply
        self.mutate_file(locus, mutations[dest])

    def restore(self):
        with open(self.backup_filename, 'w') as fp:
            fp.write(self.backup)

#main
if __name__== "__main__":
    config = Config("config.ini")
    coverage = Coverage()
    coverage.load(config.coverageFile)
    mutator = Mutator()
    for path in config.sourcesPaths.split(','):
        for ext in config.sourcesPatterns.split(','):
            for fname in glob.glob(path+"/**/"+ext, recursive=True):
                mutator.loadFile(fname, coverage)

    mutator.mutate()
    mutator.restore()