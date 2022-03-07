from enum import IntEnum
import os
import pandas as pd
from pathlib import Path
import time
import json


class outcome(IntEnum):
    UNCHANGED = 0
    IMPROVED = 1
    DETERIORATED = -1


class attribute:
    geneName = str
    variantNumber = int
    drugName = str
    outcome = str
    relation = bool
    sideEffect = bool

    def _type(self):
        return [_type for name, _type in (vars(self.__class__).items()) if not name.startswith("_")]

    def _name(self):
        return [name for name, _type in (vars(self.__class__).items()) if not name.startswith("_")]
    # def __init__(self):
    # self.geneName = str


class fileReader:
    def __init__(self, input_dir, suffix=None):
        self.files = []
        self.input_dir = input_dir
        self.suffix = suffix
        self.buffs = {}
        self.__loadfiles()
        self.data = None

    def __loadfiles(self):
        with os.scandir(self.input_dir) as it:
            for entry in it:
                if entry.is_file() and (os.path.splitext(entry.name)[1] == self.suffix or self.suffix == None):
                    self.files.append(entry)

    def readfiles(self):
        # self.loadfiles()
        for f in self.files:
            with open(f, "r") as ifile:
                self.buffs[f.name] = ifile.readlines()
        return self.buffs

    def getFileNames(self):
        return [f.name for f in self.files]

    def getFilePathes(self):
        return [f.path for f in self.files]


class database:
    def __init__(self, input_dir):
        freader = fileReader(input_dir, '.txt')
        buffs = freader.readfiles()
        col_names = attribute()._name()
        self.data = []
        for f in freader.getFilePathes():
            self.data.append(pd.read_csv(f, sep='\t', names=col_names))
        self.data = pd.concat(self.data, ignore_index=True)


def load_contracts(contract_dir, suffix='.sol'):
    result = []
    with os.scandir(contract_dir) as it:
        for entry in it:
            if Path(entry).suffix == suffix:
                result.append(Path(entry).absolute())
    return result

# load query file
def loadQueries(query_file):
    print('loading query file')
    records = []
    f = open(query_file, 'r')
    data = f.readlines()
    for d in data:
        line = d.strip('\n')
        record_json = json.loads(line)
        record = [record_json['study_id'], record_json['requested_site_preferences']]
        records.append(record)
    f.close()
    return records

#load data from training dataset to dict
def load_data(data_file, size=None):
    f = open(data_file, 'r')
    data = f.readlines()

    records = []
    for d in data:
        line = d.strip('\n')
        record_json = json.loads(line)
        record = [record_json['patient_id'], record_json['study_id'],record_json['record_time'],['DEMOGRAPHICS','MENTAL_HEALTH','BIOSPECIMEN','FAMILY_HISTORY','GENETIC','GENERAL_CLINICAL_INFORMATION','SEXUAL_AND_REPRODUCTIVE_HEALTH'],[record_json['patient_preferences']['DEMOGRAPHICS'], record_json['patient_preferences']['MENTAL_HEALTH'], record_json['patient_preferences']['BIOSPECIMEN'], record_json['patient_preferences']['FAMILY_HISTORY'], record_json['patient_preferences']['GENETIC'], record_json['patient_preferences']['GENERAL_CLINICAL_INFORMATION'], record_json['patient_preferences']['SEXUAL_AND_REPRODUCTIVE_HEALTH'] ]]
        records.append(record)
    return records[:size]


def possibleKeys(key):
    result = []
    size = len(key)
    for i in range(2**size):
        tmp = []
        for j in range(size):
            if i & (1 << j) == (1 << j):
                tmp.append(str(key[j]))
            else:
                tmp.append("*")
        result.append(tmp)
    return result[1:]


def timer(fn, *args):
    start = time.time()
    fn(*args)
    return time.time() - start
