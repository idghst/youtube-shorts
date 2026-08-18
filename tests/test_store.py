from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from shorts.models import Headline
from shorts.news import claimed_hashes, headline_hash, pick_job, write_job
from shorts.store import connect, mark_used, recent_titles, try_claim, used_hashes


def _h(title: str, source: str = "hankyung_finance") -> Headline:
    return Headline(
        source=source,
        title=title,
        summary="",
        link="https://example.com/%s" % title,
        published="",
        hash=headline_hash(title),
    )


class SqliteStoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Path(self.tmp.name) / "shorts.db"
        os.environ["SHORTS_SKIP_SUPABASE"] = "1"
        self.addCleanup(os.environ.pop, "SHORTS_SKIP_SUPABASE", None)

    def tearDown(self):
        self.tmp.cleanup()

    def test_mark_used_is_per_channel(self):
        a = _h("국민연금 개혁")
        mark_used(a, "uploaded", channel="돈이웃", video_id="abcdefghijk", path=self.db)
        self.assertIn(a.hash, used_hashes("돈이웃", path=self.db))
        self.assertNotIn(a.hash, used_hashes("offscn", path=self.db))

    def test_old_sqlite_without_channel_still_reads(self):
        conn = connect(self.db)
        conn.execute("DROP TABLE used_headlines")
        conn.execute(
            """
            CREATE TABLE used_headlines (
                hash TEXT PRIMARY KEY,
                title TEXT,
                source TEXT,
                used_at TEXT,
                video_path TEXT,
                video_id TEXT,
                status TEXT
            )
            """
        )
        conn.execute(
            "INSERT INTO used_headlines (hash, title, status) VALUES (?, ?, ?)",
            ("abc", "old", "uploaded"),
        )
        conn.commit()
        conn.close()
        conn = connect(self.db)
        cols = {row[1] for row in conn.execute("PRAGMA table_info(used_headlines)")}
        conn.close()
        self.assertIn("channel", cols)


class RpcStoreTests(unittest.TestCase):
    def setUp(self):
        os.environ.pop("SHORTS_SKIP_SUPABASE", None)
        self.calls = []

        def fake(name, payload):
            self.calls.append((name, payload))
            if name == "youtube_claimed_hashes":
                return ["aa" * 32]
            if name == "youtube_recent_titles":
                return ["국민연금 9600억 매도, 내 노후는?", "4대은행 없는 섬, 노후는 누가?"]
            if name == "youtube_try_claim":
                return payload["p_headline_hash"] != "aa" * 32
            if name == "youtube_upsert_upload":
                return "00000000-0000-0000-0000-000000000001"
            raise AssertionError(name)

        import shorts.store as store

        store.rpc_impl = fake
        self.addCleanup(setattr, store, "rpc_impl", None)

    def test_recent_titles_merges_remote(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "shorts.db"
            titles = recent_titles(
                "돈이웃",
                path=db,
                cfg={"supabase": {"url": "http://x", "publishable_key": "k"}},
            )
        self.assertIn("국민연금 9600억 매도, 내 노후는?", titles)
        self.assertEqual(self.calls[0][0], "youtube_recent_titles")
        self.assertEqual(self.calls[0][1]["p_channel_key"], "돈이웃")

    def test_used_hashes_merges_remote(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "shorts.db"
            hashes = used_hashes("돈이웃", path=db, cfg={"supabase": {"url": "http://x", "publishable_key": "k"}})
        self.assertIn("aa" * 32, hashes)
        self.assertEqual(self.calls[0][0], "youtube_claimed_hashes")
        self.assertEqual(self.calls[0][1]["p_channel_key"], "돈이웃")

    def test_try_claim_false_when_taken(self):
        taken = _h("x")
        taken.hash = "aa" * 32
        ok = try_claim(
            taken,
            channel="돈이웃",
            cfg={"supabase": {"url": "http://x", "publishable_key": "k"}},
        )
        self.assertFalse(ok)

    def test_mark_used_uploaded_calls_upsert(self):
        h = _h("기초연금 인상")
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "shorts.db"
            mark_used(
                h,
                "uploaded",
                channel="돈이웃",
                video_id="CPymleX6Jrw",
                job_path="/tmp/job",
                youtube_channel_id="UCHUxp49IFZlHHCcg_LnL66A",
                path=db,
                cfg={"supabase": {"url": "http://x", "publishable_key": "k"}},
            )
        name, payload = self.calls[-1]
        self.assertEqual(name, "youtube_upsert_upload")
        self.assertEqual(payload["p_channel_key"], "돈이웃")
        self.assertEqual(payload["p_status"], "uploaded")
        self.assertEqual(payload["p_video_id"], "CPymleX6Jrw")
        self.assertEqual(payload["p_headline_hash"], h.hash)


class PickJobTests(unittest.TestCase):
    def setUp(self):
        os.environ["SHORTS_SKIP_SUPABASE"] = "1"
        self.addCleanup(os.environ.pop, "SHORTS_SKIP_SUPABASE", None)
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.claims = []

    def tearDown(self):
        self.tmp.cleanup()

    def test_skips_headline_already_claimed_remotely(self):
        first = _h("이미 올린 국민연금")
        second = _h("새 기초연금 소식")

        def fake_claim(headline, **kwargs):
            self.claims.append(headline.title)
            return headline.hash == second.hash

        with (
            patch("shorts.news.OUT_DIR", self.root),
            patch("shorts.config.OUT_DIR", self.root),
            patch("shorts.news.channel_dir", lambda ch: self.root / ch),
            patch("shorts.news.ensure_dirs"),
            patch("shorts.news.collect", return_value=[first, second]),
            patch("shorts.news.claimed_hashes", return_value=set()),
            patch("shorts.news.try_claim", side_effect=fake_claim),
            patch("shorts.news.mark_used"),
        ):
            job = pick_job({"rss": [{"name": "x", "url": "http://x"}]}, channel="돈이웃")
        self.assertTrue((job / "headline.json").is_file())
        self.assertEqual(self.claims, [first.title, second.title])
        self.assertIn(second.hash, job.joinpath("headline.json").read_text(encoding="utf-8"))

    def test_claimed_hashes_reads_channel_jobs_only(self):
        don = self.root / "돈이웃" / "job-a"
        off = self.root / "offscn" / "job-b"
        don.mkdir(parents=True)
        off.mkdir(parents=True)
        h1 = _h("돈이웃만")
        h2 = _h("offscn만")
        (don / "headline.json").write_text(
            '{"source":"a","title":"%s","summary":"","link":"","published":"","hash":"%s"}\n'
            % (h1.title, h1.hash),
            encoding="utf-8",
        )
        (off / "headline.json").write_text(
            '{"source":"a","title":"%s","summary":"","link":"","published":"","hash":"%s"}\n'
            % (h2.title, h2.hash),
            encoding="utf-8",
        )
        with (
            patch("shorts.news.used_hashes", return_value=set()),
            patch("shorts.news.channel_dir", lambda ch: self.root / ch),
        ):
            got = claimed_hashes("돈이웃")
        self.assertIn(h1.hash, got)
        self.assertNotIn(h2.hash, got)


class WriteJobTests(unittest.TestCase):
    def test_write_job_under_channel(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with (
                patch("shorts.news.channel_dir", lambda ch: root / ch),
                patch("shorts.news.ensure_dirs"),
            ):
                job = write_job(_h("주택연금 신청"), channel="돈이웃")
            self.assertEqual(job.parent.name, "돈이웃")
            self.assertTrue((job / "headline.json").is_file())
            self.assertTrue((job / "used-topics.json").is_file())


if __name__ == "__main__":
    unittest.main()
