#!/bin/bash


DATA_FOLDER=eth
dir_prefix=node
num_of_node=4
ACCOUNTS=accounts

port=30303
rpcport=8545

mkdir -p $DATA_FOLDER

bash create_accounts.sh

files=(accounts/keystore/*) # files is an array

# account addresses
addresses=(`cat ${files[*]} | jq -r '.address'`)

# build master node
datadir=$DATA_FOLDER/${dir_prefix}0
mkdir -p ${datadir}/keystore
cp ${files[0]} ${datadir}/keystore
geth --datadir $datadir init genesis.json #>/dev/null 2>&1 
#geth --datadir $datadir >/dev/null 2>&1 
nohup geth --datadir $datadir --unlock ${addresses[0]} --password <(echo "") --mine --miner.threads 8 --miner.gastarget 9999999999999999999 --networkid 1 --rpc --rpcaddr '0.0.0.0' --rpccorsdomain "*" --nodiscover --rpcapi "admin,db,eth,debug,miner,net,shh,txpool,personal,web3" --allow-insecure-unlock & 


# create data folder for each node
for ((i=1; i < $num_of_node; i++))
do
    datadir=${DATA_FOLDER}/${dir_prefix}${i}
    mkdir -p ${datadir}/keystore
    cp ${files[$i]} ${datadir}/keystore
    geth init --datadir $datadir genesis.json >/dev/null 2>&1 
    #geth --datadir $datadir >/dev/null 2>&1 # Added JD
    nohup geth --datadir $datadir --unlock ${addresses[$i]} --password <(echo "") --networkid 1 --rpc --rpcaddr '0.0.0.0' --rpccorsdomain "*" --nodiscover --rpcapi "admin,db,eth,debug,miner,net,shh,txpool,personal,web3" --port $[$port+$i] --rpcport $[$rpcport+$i] --allow-insecure-unlock >/dev/null 2>&1 &    
done

echo -n "The blockchain is under construction."
sp='/-\|'
printf ' '
for i in {1..20}; do
    printf '\b%.1s' "$sp"
    sp=${sp#?}${sp%???}
    sleep 0.1
done

echo -e "Tstep 1"

# connects all nodes
enodes=()
for ((i=0; i < $num_of_node; i++))
do
    enodes+=(`echo '{"jsonrpc":"2.0","method": "admin_nodeInfo", "params":[],"id":1}' | nc -U ${DATA_FOLDER}/${dir_prefix}${i}/geth.ipc |jq '.result.enode'`)
done


for ((i=0; i < $num_of_node; i++))
do
    for ((j=$[$i+1];j< $num_of_node;j++))
    do
	# command=
	printf '{"jsonrpc":"2.0","method": "admin_addPeer", "params":[%s],"id":1}' ${enodes[$j]} | nc -U ${DATA_FOLDER}/${dir_prefix}${i}/geth.ipc >/dev/null 2>&1
    done
done

echo -e "\033[2K\rThe blockchain is ready."
