import re
import os

try:
    import rpm
    BASED_RPM = True
except ImportError:
    BASED_RPM = False


def get_files(match=None,
              include_paths=[],
              exclude_paths=[],
              ):
    if BASED_RPM:
        ts = rpm.TransactionSet()
        for header in ts.dbMatch():
            if include_paths:
                paths = [p for p in header["filenames"] if any(re.match(pm, p) for pm in include_paths)]
            else:
                paths = header["filenames"]
            if exclude_paths:
                paths = [p for p in paths if not any(re.match(pm, p) for pm in exclude_paths)]
            if paths:
                yield header["name"], [p for p in paths if os.path.isfile(p)]


# import json
# include = [r"^/etc*"]
# print(json.dumps({n: f for n, f in get_files(None, include)}))

