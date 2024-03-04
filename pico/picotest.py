from icecream import ic
from picosdk.discover import find_all_units

scopes = find_all_units()
ic(scopes)

for scope in scopes:
    print(scope.info)
    scope.close()