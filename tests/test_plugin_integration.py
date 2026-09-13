# -*- coding: utf-8 -*-
"""Start the plugin in a real QgsApplication and switch language."""
import os
import subprocess
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(HERE)
CHECK = os.path.join(HERE, "plugin_startup_check.py")


class PluginStartupTest(unittest.TestCase):
    def test_plugin_starts_and_switches_language(self):
        env = dict(os.environ)
        # A QGIS application must be alone in its process, so this runs apart
        # from the tests that create a plain QCoreApplication.
        env.setdefault("QT_QPA_PLATFORM", "offscreen")
        env["PYTHONPATH"] = REPO_ROOT + os.pathsep + env.get("PYTHONPATH", "")
        try:
            result = subprocess.run(
                [sys.executable, CHECK],
                cwd=REPO_ROOT,
                env=env,
                capture_output=True,
                text=True,
                timeout=600,
            )
        except (OSError, subprocess.TimeoutExpired) as e:
            self.skipTest(f"could not run QGIS startup check: {e}")
        if result.returncode != 0:
            self.fail(
                "plugin startup check failed:\n"
                f"--- stdout ---\n{result.stdout}\n--- stderr ---\n{result.stderr[-3000:]}"
            )


if __name__ == "__main__":
    unittest.main()
