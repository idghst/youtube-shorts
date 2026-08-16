from __future__ import annotations

import os
import unittest
from pathlib import Path

from shorts.config import (
    channel_from_job,
    supabase_key,
    supabase_url,
    youtube_channel_id,
)


class ConfigHelperTests(unittest.TestCase):
    def test_channel_from_job(self):
        job = Path("/workspace/out/돈이웃/20260816-job")
        self.assertEqual(channel_from_job(job), "돈이웃")
        self.assertEqual(channel_from_job(Path("/tmp/other/job")), "돈이웃")

    def test_youtube_channel_id(self):
        cfg = {"channels": {"돈이웃": {"youtube_channel_id": "UCHUxp49IFZlHHCcg_LnL66A"}}}
        self.assertEqual(youtube_channel_id(cfg, "돈이웃"), "UCHUxp49IFZlHHCcg_LnL66A")
        self.assertEqual(youtube_channel_id(cfg, "offscn"), "")

    def test_supabase_env_overrides_config(self):
        cfg = {"supabase": {"url": "https://cfg.example", "publishable_key": "cfgkey"}}
        os.environ["SUPABASE_URL"] = "https://env.example"
        os.environ["SUPABASE_PUBLISHABLE_KEY"] = "envkey"
        self.addCleanup(os.environ.pop, "SUPABASE_URL", None)
        self.addCleanup(os.environ.pop, "SUPABASE_PUBLISHABLE_KEY", None)
        self.assertEqual(supabase_url(cfg), "https://env.example")
        self.assertEqual(supabase_key(cfg), "envkey")


if __name__ == "__main__":
    unittest.main()
