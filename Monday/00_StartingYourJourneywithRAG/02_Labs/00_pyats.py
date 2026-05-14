from genie.testbed import load
import json

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
