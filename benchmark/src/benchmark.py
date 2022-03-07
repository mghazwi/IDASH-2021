import time
import os
from pathlib import Path
from tqdm import tqdm
from utils import *
from blockchain import Blockchain
from localDB import LocalDB
import json

from logger import log
import logging
# log.setLevel(logging.DEBUG)
# log.setLevel(logging.ERROR)


# Edit the following two line to the correct file location.
data_file = '/home/idash2021/benchmark/dataset/small-training.txt'
query_file = '/home/idash2021/benchmark/query/query.txt'

TRANSACTION_GAS = 21000

BLOCKING = False

def benchmark(contract, size):
    contract_dir = f"./contract/{contract}"
    contracts = load_contracts(contract_dir)
    main_contract = f"{contract}.sol"
    main_contract = Path(contract_dir).joinpath(main_contract).resolve()
    contracts.remove(main_contract)
    records = load_data(data_file)[:size]
    
    f2 = open("outcome2.txt","w")
    for rec in records:
        str1 = json.dumps(rec)
        f2.write(str1)
        f2.write("\n")
    f2.close()

    bc = Blockchain(blocking=BLOCKING, libraries=None, #contracts,
                    contract=main_contract,
                    # Edit the following line to the correct ipcfile location
                    ipcfile='/home/eth/node0/geth.ipc',
                    timeout=120)

    result = {}

    # insert records into the contract
    tx_hashs = []
    elapsed = 0
    time_start = time.time()
    for record in tqdm(records):
        tx_hash = bc.insert(*record)
        tx_hashs.append(tx_hash)
    time_end = time.time()
    elapsed = time_end-time_start

    receipts = bc.wait_all(tx_hashs)

    totalGas = sum([r['gasUsed'] for r in receipts])

    # Measured by gas
    result['Storage'] = {'Unit': 'gas',
                         'Total': totalGas, 'Average': totalGas // size}

    # Measured by time
    result['Insertion'] = {'Unit': 'second',
                           'Total': elapsed, 'Average': elapsed / size}

    #query the contract
    queries = loadQueries(query_file)
    outcome = []
    f = open("outcome.txt","w")
    elapsed = 0
    time_start = time.time()
    for query in tqdm(queries):
        response = bc.query(*query)
        str1 = json.dumps(response)
        f.write(str1)
        f.write("\n")
    time_end = time.time()
    elapsed = time_end-time_start
    f.close()
    # Measured by time
    result['Query'] = {'Unit': 'second',
                           'Total': elapsed, 'Average': elapsed / size}

    return result


def main():
    #sizes = [100 * (4**i) for i in range(4)]
    #size of training dataset
    size = 1000
    final = {size: {}}
    
    #baselines = [f"baseline{i}" for i in [5]] #[2, 3, 4, 5]]
    # for now only benchmark baseline1
    baseline = "baseline1"
    print(baseline)
    final[size][baseline] = benchmark(baseline, size)
    with open('benchmark.json', 'w') as f:
        json.dump(final, f)
    #for size in sizes:
    #    for baseline in baselines:
    #        print(baseline)
    #        final[size][baseline] = benchmark(baseline, size)
    #        with open('benchmark.json', 'w') as f:
    #            json.dump(final, f)


if __name__ == '__main__':
    main()
