from os import environ
from sys import exit

from .base import *

SETTINGS_MODE = environ.get("YAPTBDJANGO_ENV_EXEC_MODE", 'DEV')

if SETTINGS_MODE == 'DEV':
    print("YAPTBDJANGO Environment DEV")
    from .settings_dev import *

elif SETTINGS_MODE == 'PROD':
    print("YAPTBDJANGO Environment PROD")
    from .settings_prod import *

else:
    print("MISSING: ENVIRONMENT YAPTBDJANGO_ENV_EXEC_MODE")
    exit()
