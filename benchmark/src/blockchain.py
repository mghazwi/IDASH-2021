from database import Database
from node import Node
from typing import List


class Blockchain(Database):
    def __init__(self, **kwargs):
        self.proxy = Node(**kwargs)

    def insert(self, _patientId: int, _studyId: int, _recordTime: int, _preferenceNames: List[str], _preferenceValues: List[bool]):
        return self.proxy.insert(_patientId, _studyId, _recordTime, 
                                 _preferenceNames, _preferenceValues)

    def query(self, _studyId: int, _requestedSitePreferences: List[str]) -> List[int]:
        return self.proxy.query(_studyId, _requestedSitePreferences)

    def wait_all(self, tx_hashs):
        return self.proxy.wait_all(tx_hashs)

    def estimateQueryGas(self, _studyId: int, _requestedSitePreferences: List[str]):
        return self.proxy.estimateGas(_studyId, _requestedSitePreferences)

    def setBlocking(self, value):
        self.proxy.blocking = value
