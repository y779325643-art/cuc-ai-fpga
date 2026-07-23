import os
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from sr2fpga_agent.local_tools import (
    discover_tool_statuses,
    executable_env,
    resolve_executable,
)


class LocalToolsTest(unittest.TestCase):
    def test_resolve_executable_uses_path_before_fallback_dirs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path_dir = root / "path"
            fallback_dir = root / "fallback"
            path_dir.mkdir()
            fallback_dir.mkdir()
            _touch_executable(path_dir / _exe_name("yosys"))
            _touch_executable(fallback_dir / _exe_name("yosys"))

            resolved = resolve_executable("yosys", path_env=str(path_dir), fallback_dirs=[fallback_dir])

            self.assertEqual(resolved, path_dir / _exe_name("yosys"))

    def test_resolve_executable_falls_back_to_local_tool_dirs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fallback_dir = Path(tmp) / "oss-cad-suite" / "bin"
            fallback_dir.mkdir(parents=True)
            _touch_executable(fallback_dir / _exe_name("verilator"))

            resolved = resolve_executable("verilator", path_env="", fallback_dirs=[fallback_dir])

            self.assertEqual(resolved, fallback_dir / _exe_name("verilator"))

    def test_executable_env_prepends_fallback_dir_without_dropping_existing_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fallback_dir = Path(tmp)
            base_env = {"PATH": "original"}

            env = executable_env(base_env, fallback_dirs=[fallback_dir])

            self.assertEqual(env["PATH"].split(os.pathsep)[0], str(fallback_dir))
            self.assertIn("original", env["PATH"].split(os.pathsep))

    def test_executable_env_sets_oss_cad_suite_runtime_variables(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            suite_root = Path(tmp) / "oss-cad-suite"
            bin_dir = suite_root / "bin"
            lib_dir = suite_root / "lib"
            verilator_root = suite_root / "share" / "verilator"
            bin_dir.mkdir(parents=True)
            lib_dir.mkdir()
            verilator_root.mkdir(parents=True)

            env = executable_env({"PATH": "original"}, fallback_dirs=[bin_dir])

            path_parts = env["PATH"].split(os.pathsep)
            self.assertEqual(path_parts[0], str(bin_dir))
            self.assertEqual(path_parts[1], str(lib_dir))
            self.assertEqual(env["YOSYSHQ_ROOT"], str(suite_root) + os.sep)
            self.assertEqual(env["VERILATOR_ROOT"], str(verilator_root))

    def test_discover_tool_statuses_uses_fallback_dirs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fallback_dir = Path(tmp)
            _touch_executable(fallback_dir / _exe_name("yosys"))

            statuses = discover_tool_statuses(("yosys", "missing_tool"), path_env="", fallback_dirs=[fallback_dir])

            self.assertEqual(statuses["yosys"], "found")
            self.assertEqual(statuses["missing_tool"], "missing")

    def test_windows_defaults_include_oss_cad_suite_and_git_bash_locations(self) -> None:
        with mock.patch("sr2fpga_agent.local_tools.Path.exists", return_value=True):
            env = executable_env({"PATH": ""})

        self.assertIn("D:\\Tools\\oss-cad-suite\\bin", env["PATH"])
        self.assertIn("D:\\Program Files (x86)\\Git\\bin", env["PATH"])


def _touch_executable(path: Path) -> None:
    path.write_text("", encoding="utf-8")
    path.chmod(0o755)


def _exe_name(name: str) -> str:
    return f"{name}.exe" if os.name == "nt" else name


if __name__ == "__main__":
    unittest.main()
