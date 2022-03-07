from web3 import Web3, EthereumTesterProvider
from solcx import compile_standard, compile_files
from pathlib import Path
import json
from utils import attribute, outcome
from logger import log
import logging
from eth_tester import PyEVMBackend, EthereumTester
# log.setLevel(logging.DEBUG)


class interface:
    def __init__(self, ipcfile=None, blocking=True, **kwargs):
        if ipcfile is None:
            genesis_overrides = {'gas_limit': int(1e15), 'difficulty': 1}
            custom_genesis_params = PyEVMBackend._generate_genesis_params(
                overrides=genesis_overrides)
            pyevm_backend = PyEVMBackend(
                genesis_parameters=custom_genesis_params)
            t = EthereumTester(backend=pyevm_backend)
            self.web3 = Web3(EthereumTesterProvider(t))
        else:
            self.web3 = Web3(Web3.IPCProvider(ipcfile, **kwargs))
        self.web3.eth.defaultAccount = self.web3.eth.accounts[0]
        self.web3.eth.default_account = self.web3.eth.accounts[0]
        self.libraries = {}
        self.contract_interface = None
        self.blocking = blocking

    def deploy_libraries(self, libraries, remappings=None):
        if libraries == None:
            return
        compiled_libraries = compile_files(
            libraries, import_remappings=remappings)
        for name, compiled_library in compiled_libraries.items():
            deployment = self.web3.eth.contract(
                abi=compiled_library['abi'], bytecode=compiled_library['bin'])
            tx_hash = deployment.constructor().transact()
            tx_receipt = self.web3.eth.waitForTransactionReceipt(tx_hash)
            library_address = tx_receipt['contractAddress']
            self.libraries[name] = library_address
        with open('library_address.json', 'w') as wf:
            json.dump(self.libraries, wf, indent=4)

    def load_lib_add(self):
        tmp = '''{
                "language": "Solidity",
                "sources": {
                  "%s": {
                    "urls": ["%s"]}},
                "settings": {
                    "remappings": [ ],
                    "libraries": {
                    },
                  "evmVersion": "byzantium",
                  "outputSelection": {
                     "*": {
                                   "*": [
                                        "metadata", "evm.bytecode"
                                         , "evm.bytecode.sourceMap"
                                    ]
                           }
                    }
                }}
                '''
        tmp = json.loads(tmp)
        for lib, add in self.libraries.items():
            filename, libname = lib.split(':')
            # log.debug(Path(filename).resolve())
            tmp['settings']['remappings'].append(
                f"{Path(filename).name}={Path(filename).resolve()}")
            log.debug(tmp)
            tmp['settings']['libraries'][filename] = {libname: add}
        return tmp

    def publish(self, scfile, name):
        path = Path(scfile).resolve()
        tmp = self.load_lib_add()
        tmp['sources'] = {path.name: {"urls": [str(path)]}}
        sc = tmp
        log.debug(str(path.parent))
        compiled_sol = compile_standard(sc, allow_paths=str(path.parent))
        contract_interface = compiled_sol['contracts'][path.name][name]
        w3 = self.web3
        w3.eth.defaultAccount = w3.eth.accounts[0]
        bytecode = contract_interface['evm']['bytecode']['object']
##        print(bytecode)
        abi = json.loads(contract_interface['metadata'])['output']['abi']
        tester = w3.eth.contract(abi=abi, bytecode=bytecode)
        tx_hash = tester.constructor().transact() # submit the transaction that deploys the contract 
        tx_receipt = w3.eth.waitForTransactionReceipt(tx_hash) # wait for the transaction to be mined, and get the transaction receipt
        # contract = {scfile: tx_receipt.contractAddress}
        # with open('contract_address.json', 'w') as wf:
        #     json.dump(contract, wf, indent=4)
        # print(tx_receipt)
        self.contract_instance = self.contract(tx_receipt, contract_interface)
        return tx_receipt, contract_interface

    def contract(self, tx_receipt, contract_interface):
        contract = self.web3.eth.contract(
            address=tx_receipt.contractAddress, abi=json.loads(contract_interface['metadata'])['output']['abi'])
        return contract

    def send(self, function_, *tx_args, event=None):
        fxn_to_call = getattr(self.contract_instance.functions, function_)
##        print(fxn_to_call)
        built_fxn = fxn_to_call(*tx_args)
##        print(built_fxn)
##        print('Before tx_hash')
##        print(self.web3.eth.getBalance(self.web3.eth.defaultAccount))
##        print(self.estimateGas(function_, *tx_args))
        tx_hash = built_fxn.transact({'gas':100000000})
##        print(*tx_args)
##        tx_hash = self.contract_instance.functions.insertObservation(*tx_args).transact()
##        print('After tx_hash')
        if not self.blocking:
            log.debug('not blocking', type(tx_hash))
            return tx_hash
        receipt = self.web3.eth.waitForTransactionReceipt(tx_hash)
        if event is not None:
            event_to_call = getattr(self.contract_instance.events, event)
            raw_log_output = event_to_call().processReceipt(receipt)
            indexed_events = clean_logs(raw_log_output)
            return receipt, indexed_events
        else:
            return receipt

    def retrieve(self, function_, *call_args, tx_params=None):
        """Contract.function.call() with cleaning"""

        fxn_to_call = getattr(self.contract_instance.functions, function_)
        built_fxn = fxn_to_call(*call_args)

        return_values = built_fxn.call(transaction=tx_params)

        if type(return_values) == bytes:
            return_values = return_values.decode('utf-8').rstrip("\x00")

        return return_values

    def wait_all(self, tx_hashs):
        receipts = []
        for tx_hash in tx_hashs:
            receipt = self.web3.eth.waitForTransactionReceipt(tx_hash)
            receipts.append(receipt)
        return receipts

    def estimateGas(self, function_, *call_args, tx_params=None):
##        print('EstimateGas!')
        fxn_to_call = getattr(self.contract_instance.functions, function_)
        built_fxn = fxn_to_call(*call_args)
##        print(built_fxn)
##        print(tx_params)
##        return built_fxn.estimateGas(transaction=tx_params)
        return self.web3.eth.estimateGas(built_fxn)


def clean_logs(log_output):
    indexed_events = log_output[0]['args']
    cleaned_events = {}
    for key, value in indexed_events.items():
        if type(value) == bytes:
            try:
                cleaned_events[key] = value.decode('utf-8').rstrip("\x00")
            except UnicodeDecodeError:
                cleaned_events[key] = Web3.toHex(value)
        else:
            cleaned_events[key] = value
    print(f"Indexed Events: {cleaned_events}")
    return cleaned_events
