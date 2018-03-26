import os
from ci.run.common.constants import CI_TEMPLATES_DIR, CI_OUT_DIR

CI_PROVISION_INVENTORY_TEMPL = os.path.join(CI_TEMPLATES_DIR, "inventory.yml.j2")
CI_PROVISION_INVENTORY = os.path.join(CI_OUT_DIR, "inventory.yml")
