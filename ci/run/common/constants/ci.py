import os
from ci.run.common.constants import PROJECT_DIR

CI_DIR = os.path.join(PROJECT_DIR, "ci")
CI_TESTS_DIR = os.path.join(CI_DIR, "tests")
CI_TEST_JOB_NAME = "bamachrn-python"
CI_RUN_DIR = os.path.join(CI_DIR, "run")
CI_TEMPLATES_DIR = os.path.join(CI_RUN_DIR, "templates")
CI_OUT_DIR = os.path.join(CI_RUN_DIR, "out")


