#!/usr/bin/python3
################################################################
#              Projects: mutable-tester
#              Author:   Sébastien Valat
#              Date:     01/2019
#              License:  CeCILL-C
#              Version:  0.1.0
################################################################

#imports
import configparser
import glob
import os
import re
import random
from subprocess import STDOUT, check_output, CalledProcessError, TimeoutExpired

#Config class
class Config:
    def __init__(self, path: str):
        config = configparser.ConfigParser()
        config.read(path)
        self.project_name = config["project"]["name"]
        self.sources_paths = config["sources"]["paths"]
        self.sources_patterns = config["sources"]["patterns"]
        self.sources_exclude_patterns = config["sources"]["exclude_patterns"]
        self.coverage_file = config["coverage"]["file"]
        self.build_directory = config["build"]["directory"]
        self.build_command = config["build"]["command"]
        self.test_directory = config["test"]["directory"]
        self.test_command = config["test"]["command"]
        self.test_max_time = int(config["test"]["maxtime"])
        self.runner_count = int(config["runner"]["count"])
    
    def is_excluded(self, path):
        for pattern in self.sources_exclude_patterns.split(','):
            if pattern in path:
                return True
        return False

#class to track coverage stats
class Coverage:
    def __init__(self):
        self.maps = {}
        self.loaded = False

    def load(self, path: str):
        #vars
        self.maps = {}

        #regex
        regexp_file = re.compile("^SF:(.*)\n")
        regexp_line = re.compile("^DA:([0-9]+),[0-9]+")
        filename = ''

        #load
        with open(path, 'r') as fp:
            content = fp.readlines()
            for line in content:
                res_file = regexp_file.match(line)
                res_line = regexp_line.match(line)
                if res_file:
                    filename = res_file.group(1)
                    self.maps[filename] = {}
                elif res_line:
                    lineno = res_line.group(1)
                    self.maps[filename][lineno] = True
            self.loaded = True

    def has_file(self, filename) -> bool:
        if self.loaded:
            return (filename in self.maps)
        else:
            return True

    def has_file_line(self, filename: str, line: int) -> bool:
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
        self.locus_list = []
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
            #" * ": [" + ", " - ", " / "],
            #" / ": [" + ", " - ", " * "],
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

    def parse_locus(self, filename: str, lineno: int, line: str, pattern: str):
        cursor = 0
        while cursor >= 0:
            cursor = line.find(pattern, cursor)
            if cursor >= 0:
                self.locus_list.append({
                    'pattern': pattern,
                    'cursor': cursor,
                    'lineno': lineno,
                    'filename': filename,
                })
                cursor += 1

    def load_file(self, filename: str, coverage: Coverage):
        #if present in coverage
        if not coverage.has_file(filename):
            return

        #load
        with open(filename, "r") as fp:
            lineno = 0
            for line in fp.readlines():
                lineno += 1
                if coverage.has_file_line(filename, lineno):
                    for mut in self.mutations:
                        self.parse_locus(filename, lineno, line, mut)

    def mutate_file(self, locus, dest):
        print("%s:%s ('%s' => '%s')"%(locus['filename'], locus['lineno'], locus['pattern'], dest))
        
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
        sel = random.randrange(0, len(self.locus_list))

        #extract info
        locus = self.locus_list[sel]
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
    #load config
    config = Config("config.ini")

    #load coverage
    coverage = Coverage()
    if config.coverage_file != '':
        coverage.load(config.coverage_file)

    #build mutator
    mutator = Mutator()

    #load sources
    for path in config.sources_paths.split(','):
        #reset
        os.chdir(path)
        os.system("git reset --hard")

        #list files
        for ext in config.sources_patterns.split(','):
            for fname in glob.glob(path+"/**/"+ext, recursive=True):
                if not config.is_excluded(fname):
                    mutator.load_file(fname, coverage)

    #loop
    cnt = config.runner_count
    score = 0
    for i in range(1, cnt+1):
        #mutate
        mutator.mutate()

        #build
        os.chdir(config.build_directory)
        build_status = os.system(config.build_command + " 1>/dev/null 2>/dev/null")

        #run tests
        if build_status == 0:
            os.chdir(config.test_directory)
            try:
                check_output(config.test_command + " 1>/dev/null 2>/dev/null", shell=True, stderr=STDOUT, timeout=config.test_max_time)
                test_status = 0
            except CalledProcessError:
                test_status = 1
            except TimeoutExpired:
                print("TIMEOUT after %d seconds"%(config.test_max_time))
                test_status = 1

        #score
        if test_status == 0 and build_status == 0:
            score += 1
            print("SUCCESS %d / %d (%0.1f %%)"%(score, i, 100 * score / i))
        else:
            print("FAILED %d / %d (%0.1f %%)"%(score, i, 100 * score / i))

        #restore
        mutator.restore()

    #final
    print("SCORE %d / %d (%0.1f %%)"%(score, cnt, 100 * score / cnt))