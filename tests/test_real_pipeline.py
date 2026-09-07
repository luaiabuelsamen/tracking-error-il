"""Hardware-free checks for trial scheduling and applied-action feedback."""
import ast
import json
import sys
from pathlib import Path
from unittest import TestCase, main
from unittest.mock import patch

import numpy as np

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
import trial_runner
from run_policy_real import send_target


class RealPipelineTests(TestCase):
    def test_trajectory_saved_when_disconnect_raises(self):
        import tempfile
        import time
        from types import SimpleNamespace
        tree = ast.parse((SCRIPTS / "run_policy_real.py").read_text())
        function = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "main")
        cleanup = next(n.finalbody for n in function.body if isinstance(n, ast.Try) and n.finalbody)
        code = compile(ast.fix_missing_locations(ast.Module(body=cleanup, type_ignores=[])), "cleanup", "exec")
        class Robot:
            def disconnect(self):
                raise RuntimeError("Overload error")
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "trajectory.npz"
            frame = (np.zeros(6), np.ones(6), np.ones(6), np.zeros(12), .1)
            scope = dict(robot=Robot(), traj=[frame], np=np, time=time, Path=Path, FPS=30,
                         t_start=time.perf_counter(), args=SimpleNamespace(out_traj=str(out)),
                         rollout_complete=True)
            with self.assertRaisesRegex(RuntimeError, "Overload"):
                exec(code, scope)
            with np.load(out) as z:
                self.assertTrue(z["rollout_complete"])
                np.testing.assert_array_equal(z["applied_action"], np.ones((1, 6)))

    def test_feedback_uses_clamped_command_in_joint_order(self):
        class Robot:
            def send_action(self, action):
                return {key: min(value, 8.0) for key, value in reversed(list(action.items()))}
        np.testing.assert_array_equal(send_target(Robot(), ["jaw", "wrist"], [20, 3]), [8, 3])

    def test_counterbalanced_pairs_use_observation_names(self):
        import tempfile
        from types import SimpleNamespace
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            # The manifest includes these source paths and __file__.
            (root / "scripts").mkdir()
            for name in ("trial_runner.py", "run_policy_real.py"):
                (root / "scripts" / name).write_text("# fixture")
            ckpt = {"base_v2": "base", "delta_v3": "delta"}
            for name in ckpt.values():
                (root / name).mkdir()
                (root / name / "train_summary.json").write_text("{}")
            argv = ["trial_runner", "--arms", "base_v2,delta_v3", "--paired", "--trials", "4"]
            with patch.object(trial_runner, "REPO", root), patch.object(trial_runner, "CKPT", ckpt), \
                 patch.object(trial_runner, "__file__", str(root / "scripts/real/trial_runner.py")), \
                 patch.object(sys, "argv", argv), patch("builtins.input", side_effect=["", "s"] * 4), \
                 patch.object(trial_runner.subprocess, "run", return_value=SimpleNamespace(returncode=0)) as run:
                trial_runner.main()
            records = json.loads((root / "results/hardware/real_trials.json").read_text())
            self.assertEqual([r["arm"] for r in records], ["base_v2", "delta_v3", "delta_v3", "base_v2"])
            self.assertEqual([r["pair"] for r in records], [0, 0, 1, 1])
            self.assertEqual([c.args[0][c.args[0].index("--arm") + 1] for c in run.call_args_list],
                             ["base", "delta", "delta", "base"])
            # Emulate shutdown fault on trial 3: recover its outcome, never rerun it.
            result_path = root / "results/hardware/real_trials.json"
            result_path.write_text(json.dumps(records[:2]))
            pending = root / "results/hardware/real_trials_pending.json"
            pending.write_text(json.dumps(dict(session=records[0]["session"], trial=2,
                                                arm="delta_v3", rollout_complete=True, returncode=-6)))
            with patch.object(trial_runner, "REPO", root), patch.object(trial_runner, "CKPT", ckpt), \
                 patch.object(trial_runner, "__file__", str(root / "scripts/real/trial_runner.py")), \
                 patch.object(sys, "argv", argv + ["--resume"]), \
                 patch("builtins.input", side_effect=["f", "", "s"]), \
                 patch.object(trial_runner.subprocess, "run", return_value=SimpleNamespace(returncode=0)) as run:
                trial_runner.main()
            recovered = json.loads(result_path.read_text())
            self.assertEqual(len(recovered), 4)
            self.assertEqual(recovered[:2], records[:2])
            self.assertFalse(recovered[2]["success"])
            self.assertTrue(recovered[2]["recovered_outcome"])
            self.assertTrue(recovered[2]["shutdown_error"])
            self.assertEqual(run.call_count, 1)
            self.assertFalse(pending.exists())


if __name__ == "__main__":
    main()
