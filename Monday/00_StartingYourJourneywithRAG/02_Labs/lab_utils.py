import os
import sys
from typing import Optional

def discover_device(testbed, preferred_name: Optional[str] = None):
    """Choose a device from a pyATS testbed using a few fallbacks:

    Order of precedence:
    1. explicit `preferred_name` argument (if provided and exists in testbed)
    2. `TARGET_DEVICE` environment variable
    3. first CLI argument
    4. heuristic match on common platform/name fragments
    5. first device in testbed

    Returns the chosen device object. Prints the selected device name.
    """
    pref = preferred_name or os.getenv("TARGET_DEVICE")
    if not pref and len(sys.argv) > 1:
        pref = sys.argv[1]

    if pref and pref in testbed.devices:
        chosen = testbed.devices[pref]
        print(f"Using device from preference: {pref}")
        return chosen

    # Heuristic matching for common Cisco device name fragments
    heuristics = ("cat", "catalyst", "csr", "nxos", "ios", "asa", "rtr", "sw", "leaf", "spine", "core")
    for name, dev in testbed.devices.items():
        low = name.lower()
        if any(h in low for h in heuristics):
            print(f"Discovered device by heuristic: {name}")
            return dev

    # Fallback to the first device in the testbed
    try:
        first_name = next(iter(testbed.devices))
        print(f"No preference found; using first device: {first_name}")
        return testbed.devices[first_name]
    except StopIteration:
        raise RuntimeError("Testbed contains no devices")
