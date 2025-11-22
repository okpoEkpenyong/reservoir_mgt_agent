import os
import sys

# Ensure the project root (parent of `reservoir_mgt_agent`) is on sys.path
# so tests can import the package as `reservoir_mgt_agent` during collection.
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
