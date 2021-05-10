import json
from datetime import datetime
import os
from ruamel.yaml import YAML
from pathlib import Path
from eth2spec.config import config_util

def load_conf():
    yaml = YAML(typ='base')
    loaded_config = yaml.load(Path('./eth2_config.yaml'))
    out: Dict[str, Any] = dict()
    for k, v in loaded_config.items():
        if isinstance(v, list):
            # Clean up integer values. YAML parser renders lists of ints as list of str
            out[k] = [int(item) if item.isdigit() else item for item in v]
        elif isinstance(v, str) and v.startswith("0x"):
            out[k] = bytes.fromhex(v[2:])
        elif k != 'CONFIG_NAME':
            out[k] = int(v)
    out['CONFIG_NAME'] = 'nocturne'
    return out
config_util.config = load_conf()

from eth2spec.merge.spec import *

with open('./genesis.ssz', 'rb') as f:
    genesis_state = BeaconState.deserialize(f, os.stat('./genesis.ssz').st_size)

with open('./eth1_config.json') as f:
    eth1_config = json.load(f)

header_copy = genesis_state.latest_block_header.copy()
assert header_copy.state_root == Root()
header_copy.state_root = genesis_state.hash_tree_root()

print(f"""
genesis_time: {genesis_state.genesis_time}   # {datetime.utcfromtimestamp(int(genesis_state.genesis_time)).strftime('%Y-%m-%d %H:%M:%S')} UTC
genesis_state_root: 0x{genesis_state.hash_tree_root().hex()}
genesis_block_root_with_zero_state_root: 0x{genesis_state.latest_block_header.hash_tree_root().hex()}
genesis_block_root_with_good_state_root: 0x{header_copy.hash_tree_root().hex()}
genesis_validators_root: 0x{genesis_state.validators.hash_tree_root().hex()}
genesis_validators_count: {genesis_state.validators.length()}
genesis_active_validators_count: {len(get_active_validator_indices(genesis_state, Epoch(0)))}
genesis_total_active_stake_gwei: {get_total_active_balance(genesis_state)}
genesis_total_balance_gwei: {sum(genesis_state.balances.readonly_iter())}
eth1_data:
  deposit_root: 0x{genesis_state.eth1_data.deposit_root.hex()}
  deposit_count: {genesis_state.eth1_data.deposit_count}
  block_hash: 0x{genesis_state.eth1_data.block_hash.hex()}
eth1_chain_id: {eth1_config['config']['chainId']}
deposit_contract_address: 0x{config_util.config['DEPOSIT_CONTRACT_ADDRESS'].hex()}
genesis_fork_version: 0x{genesis_state.fork.current_version.hex()}
genesis_fork_digest: 0x{compute_fork_digest(genesis_state.fork.current_version, genesis_state.validators.hash_tree_root()).hex()}
pre_genesis_fork_digest: 0x{compute_fork_digest(genesis_state.fork.current_version, Root()).hex()}
execution_payload:
    block_hash: 0x{genesis_state.latest_execution_payload_header.block_hash.hex()}
    parent_hash: 0x{genesis_state.latest_execution_payload_header.parent_hash.hex()}
    coinbase: 0x{genesis_state.latest_execution_payload_header.coinbase.hex()}
    state_root: 0x{genesis_state.latest_execution_payload_header.state_root.hex()}
    number: {genesis_state.latest_execution_payload_header.number}
    gas_limit: {genesis_state.latest_execution_payload_header.gas_limit}
    gas_used: {genesis_state.latest_execution_payload_header.gas_used}
    timestamp: {genesis_state.latest_execution_payload_header.timestamp}   # {datetime.utcfromtimestamp(int(genesis_state.latest_execution_payload_header.timestamp)).strftime('%Y-%m-%d %H:%M:%S')} UTC
    receipt_root: 0x{genesis_state.latest_execution_payload_header.receipt_root.hex()}
    logs_bloom: 0x{genesis_state.latest_execution_payload_header.logs_bloom.hex()}
    transactions_root: 0x{genesis_state.latest_execution_payload_header.transactions_root.hex()}
""")
