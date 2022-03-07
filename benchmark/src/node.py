from interface import interface
from pathlib import Path


class Node:
    def __init__(self, libraries, contract, **kwargs):
        self.interface = interface(**kwargs)
        self.interface.deploy_libraries(libraries) # return because libraries=NONE right now
        self.interface.publish(contract, Path(contract).stem)

    def insert(self, *args):
        return self.interface.send("addPreferences", *args)

    def query(self, *args):
        return self.interface.retrieve("getConsentingPatientIds", *args)

    def wait_all(self, tx_hashs):
        return self.interface.wait_all(tx_hashs)

    def estimateGas(self, *args):
        return self.interface.estimateGas("getConsentingPatientIds", *args)

    def setBlocking(self, value):
        self.interface.blocking = value
