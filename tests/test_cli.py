import unittest
from unittest.mock import patch

from ctrlsolar.cli import main


class CliTests(unittest.TestCase):
    def test_main_defaults_to_run_with_default_config(self):
        with patch("ctrlsolar.cli.run") as run_mock:
            exit_code = main([])

        self.assertEqual(exit_code, 0)
        run_mock.assert_called_once_with("config.yaml")

    def test_main_run_subcommand_uses_given_config(self):
        with patch("ctrlsolar.cli.run") as run_mock:
            exit_code = main(["run", "--config", "custom.yaml"])

        self.assertEqual(exit_code, 0)
        run_mock.assert_called_once_with("custom.yaml")


if __name__ == "__main__":
    unittest.main()
