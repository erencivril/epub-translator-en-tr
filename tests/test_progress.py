import json
import os
import tempfile
from progress import ProgressTracker


def test_create_tracker():
    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, "test.progress.json")
        tracker = ProgressTracker(path, total=10, source="book.epub", model="test-model")
        assert tracker.total == 10
        assert len(tracker.completed) == 0


def test_mark_completed():
    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, "test.progress.json")
        tracker = ProgressTracker(path, total=10, source="book.epub", model="test-model")
        tracker.mark_completed("chapter1.xhtml")
        assert "chapter1.xhtml" in tracker.completed


def test_save_and_load():
    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, "test.progress.json")
        tracker = ProgressTracker(path, total=5, source="book.epub", model="test-model")
        tracker.mark_completed("ch1.xhtml")
        tracker.mark_completed("ch2.xhtml")
        tracker.save()

        tracker2 = ProgressTracker.load(path)
        assert tracker2.total == 5
        assert "ch1.xhtml" in tracker2.completed
        assert "ch2.xhtml" in tracker2.completed


def test_is_completed():
    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, "test.progress.json")
        tracker = ProgressTracker(path, total=3, source="book.epub", model="test-model")
        tracker.mark_completed("ch1.xhtml")
        assert tracker.is_completed("ch1.xhtml")
        assert not tracker.is_completed("ch2.xhtml")


def test_progress_percentage():
    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, "test.progress.json")
        tracker = ProgressTracker(path, total=4, source="book.epub", model="test-model")
        tracker.mark_completed("ch1.xhtml")
        tracker.mark_completed("ch2.xhtml")
        assert tracker.percentage == 50.0
