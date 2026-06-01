import paramiko
from genie.testbed import load
import json

# --- Patch Paramiko to support legacy Cisco SSH algorithms ---
paramiko.Transport._preferred_kex = (
    'diffie-hellman-group14-sha1',
    'diffie-hellman-group-exchange-sha256',
    'diffie-hellman-group-exchange-sha1',
    'diffie-hellman-group14-sha256',
)
paramiko.Transport._preferred_ciphers = (
    'aes128-cbc',
    '3des-cbc',
    'aes128-ctr',
    'aes256-ctr',
)

# --- Load testbed file ---
testbed = load("testbed.yaml")

# --- Select first device from testbed and connect (learn hostname) ---
device = next(iter(testbed.devices.values()))
device.connect(log_stdout=True, learn_hostname=True)

# --- Parse a command ---
parsed_output = device.parse("show ip interface brief")

# --- Pretty-print the parsed JSON ---
print("\n✅ Parsed 'show ip interface brief' (as JSON):\n")
print(json.dumps(parsed_output, indent=2))
