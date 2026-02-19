import json
import sys
import time


class ProgressTracker:
    def __init__(self, filepath: str, total: int, source: str, model: str):
        self.filepath = filepath
        self.total = total
        self.source = source
        self.model = model
        self.completed: list[str] = []
        self.failed: list[str] = []
        self._start_time = time.time()
        self._last_line_length = 0
        self._line_active = False

    def mark_completed(self, chapter_name: str):
        if chapter_name not in self.completed:
            self.completed.append(chapter_name)
            self.save()

    def mark_failed(self, chapter_name: str):
        if chapter_name not in self.failed:
            self.failed.append(chapter_name)
            self.save()

    def is_completed(self, chapter_name: str) -> bool:
        return chapter_name in self.completed

    @property
    def percentage(self) -> float:
        if self.total == 0:
            return 100.0
        return (len(self.completed) / self.total) * 100

    def save(self):
        data = {
            "source": self.source,
            "model": self.model,
            "total_chapters": self.total,
            "completed": self.completed,
            "failed": self.failed,
        }
        with open(self.filepath, "w") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    @classmethod
    def load(cls, filepath: str) -> "ProgressTracker":
        with open(filepath) as f:
            data = json.load(f)
        tracker = cls(
            filepath=filepath,
            total=data["total_chapters"],
            source=data["source"],
            model=data["model"],
        )
        tracker.completed = data.get("completed", [])
        tracker.failed = data.get("failed", [])
        return tracker

    def print_progress(self, current_chapter: str = ""):
        done = len(self.completed)
        bar_width = 30
        filled = int(bar_width * done / max(self.total, 1))
        bar = "\u2588" * filled + "\u2591" * (bar_width - filled)

        elapsed = time.time() - self._start_time
        if done > 0:
            eta = (elapsed / done) * (self.total - done)
            eta_str = _format_time(eta)
        else:
            eta_str = "calculating..."

        line = f"[{bar}] {done}/{self.total} ({self.percentage:.0f}%)"
        if current_chapter:
            line += f" - {current_chapter}"
        line += f" - ETA: {eta_str}"

        # Pad with spaces when the new line is shorter to avoid stale tail text.
        pad = max(self._last_line_length - len(line), 0)
        sys.stdout.write("\r" + line + (" " * pad))
        sys.stdout.flush()
        self._last_line_length = len(line)
        self._line_active = True

    def finish_line(self):
        """Finalize the current progress line and move to a clean new line."""
        if not self._line_active:
            return
        sys.stdout.write("\n")
        sys.stdout.flush()
        self._line_active = False
        self._last_line_length = 0


def _format_time(seconds: float) -> str:
    if seconds < 60:
        return f"{seconds:.0f}s"
    elif seconds < 3600:
        return f"{seconds / 60:.0f}m"
    else:
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        return f"{h}h {m}m"
