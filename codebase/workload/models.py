"""Giao diện estimator của L3 và các cài đặt nhẹ (chỉ thư viện chuẩn).

Production nội trú mặc định dùng SimmonsLookupEstimator, đọc data/reference/ward_task_duration.csv
(module-contract §3.3). Model OR thực nghiệm (scripts/l3/) KHÔNG được nạp mặc định.
"""
import csv
import hashlib
import json
import math
import statistics
from decimal import Decimal, InvalidOperation
from pathlib import Path

from .features import forbidden_in

METADATA_KEYS = ("model_version", "algorithm", "target", "features",
                 "trained_on", "trained_at", "data_card")

REPO_ROOT = Path(__file__).resolve().parents[2]
SIMMONS_CSV = REPO_ROOT / "data" / "reference" / "ward_task_duration.csv"
SIMMONS_SOURCE = "lookup:simmons-2025-table3"
SIMMONS_COLUMNS = ("task_type", "source_task", "mean_duration_min", "unit", "source_table",
                   "source_doi", "context", "data_kind", "staffing_note")
SIMMONS_UNIT = "minutes_per_patient_episode"
SIMMONS_CONTEXT = "US_ACE_older_acute_inpatients"

# Trường điều kiện TÙY CHỌN trên task — ĐỀ XUẤT, chưa có trong contract (cần Khoa/Kiên chốt).
# L3 chỉ đọc, không bao giờ tự điền các trường này.
SINGLE_STAFF_FIELD = "staff_required"        # int: số nhân viên cần đồng thời
MOBILITY_SCOPE_FIELD = "mobility_scope"      # "bed_to_chair" | "walking" | khác
SETTING_FIELD = "setting"                    # "inpatient_ward" | "operating_room" | …
COMPLEXITY_FIELD = "complexity"              # "standard" | khác
INPATIENT_SETTINGS = {"inpatient_ward"}
SIMMONS_MOBILITY_SCOPES = {"bed_to_chair", "walking"}


class SourceTableError(RuntimeError):
    """Bảng nguồn thiếu hoặc sai cấu trúc: lỗi kỹ thuật, không phải need_info."""


class DurationEstimator:
    """Hợp đồng nội bộ của L3.

    source: chuỗi ghi vào duration_source, dạng "model:<ver>" hoặc "lookup:<tên>".
    required_features: feature bắt buộc; thiếu thì L3 báo need_info, không đoán.
    """
    source = ""
    required_features = ()

    def __init__(self):
        if not isinstance(self.source, str) or not self.source.startswith(("model:", "lookup:")):
            raise ValueError("source phải có dạng 'model:<ver>' hoặc 'lookup:<tên>'")
        bad = forbidden_in(self.required_features)
        if bad:
            raise ValueError("feature bị cấm (log timestamp/target/kết quả phân công): " + ", ".join(bad))

    def supports(self, task_type):
        raise NotImplementedError

    def blockers(self, task):
        """Lý do KHÔNG được áp dụng estimator cho task này (điều kiện nguồn). Mặc định: không có."""
        return []

    def predict(self, features):
        """Trả số phút (int > 0) hoặc None nếu không đủ căn cứ cho case này."""
        raise NotImplementedError


class LookupTableEstimator(DurationEstimator):
    """Bảng tra task_type (× một feature phân tầng, vd acuity) → phút, bắt buộc có nguồn."""

    def __init__(self, name, citation, table, by=None):
        if not isinstance(citation, str) or not citation.strip():
            raise ValueError("bảng tra cần citation; không nhận số phút không có nguồn")
        self.source = "lookup:" + name
        self.citation = citation
        self.by = by
        self.required_features = ("task_type",) + ((by,) if by else ())
        self.table = table
        super().__init__()

    @classmethod
    def from_json(cls, path):
        """File JSON: {"name", "citation", "by"?, "rows": [{"task_type", "<by>"?, "minutes"}]}."""
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        by = data.get("by")
        table = {}
        for row in data["rows"]:
            key = (row["task_type"], row[by]) if by else row["task_type"]
            table[key] = row["minutes"]
        return cls(data["name"], data.get("citation"), table, by)

    def supports(self, task_type):
        keys = (k[0] if self.by else k for k in self.table)
        return task_type in set(keys)

    def predict(self, features):
        key = (features["task_type"], features[self.by]) if self.by else features["task_type"]
        return self.table.get(key)


class MedianBaseline(DurationEstimator):
    """Baseline: trung vị thời lượng theo task_type, làm tròn LÊN để tránh đánh giá thiếu tải.

    Chỉ fit từ thời lượng thao tác đã xác minh, không fit từ mốc ghi log.
    """
    required_features = ("task_type",)

    def __init__(self, version, medians):
        self.source = "model:median-" + version
        self.medians = dict(medians)
        super().__init__()

    @classmethod
    def fit(cls, rows, version):
        """rows: iterable (task_type, duration_min) với duration là số dương."""
        groups = {}
        for task_type, minutes in rows:
            if not isinstance(minutes, (int, float)) or isinstance(minutes, bool) or minutes <= 0:
                raise ValueError("duration huấn luyện phải là số dương: %r" % (minutes,))
            groups.setdefault(task_type, []).append(minutes)
        if not groups:
            raise ValueError("không có dữ liệu để fit")
        return cls(version, {t: math.ceil(statistics.median(v)) for t, v in groups.items()})

    def supports(self, task_type):
        return task_type in self.medians

    def predict(self, features):
        return self.medians.get(features["task_type"])


def load_metadata(path):
    """Đọc metadata của artifact mô hình; thiếu khóa hoặc dùng feature cấm thì báo lỗi."""
    meta = json.loads(Path(path).read_text(encoding="utf-8"))
    missing = [k for k in METADATA_KEYS if k not in meta]
    if missing:
        raise ValueError("metadata thiếu: " + ", ".join(missing))
    bad = forbidden_in(meta["features"])
    if bad:
        raise ValueError("artifact dùng feature bị cấm: " + ", ".join(bad))
    return meta


def ceil_minutes(text):
    """Làm tròn LÊN số phút từ chuỗi CSV, dùng Decimal để tránh sai số float (2.54 → 3)."""
    return int(Decimal(text).to_integral_value(rounding="ROUND_CEILING"))


def lf_sha256(path):
    """SHA-256 sau khi chuẩn hóa CRLF → LF, để so được với checksum Lam ghi trong bundle."""
    return hashlib.sha256(Path(path).read_bytes().replace(b"\r\n", b"\n")).hexdigest()


class SimmonsLookupEstimator(DurationEstimator):
    """Tra mean phút theo đúng task_type trong Simmons et al. 2025, Table 3 (DOI 10.1111/jgs.19507).

    Chỉ khớp chính xác task_type, không suy từ tên gần giống. Không hiệu chỉnh theo acuity/ADL
    (nguồn là aggregate, không có chiều này). Kiểm điều kiện staffing/phạm vi trước khi tra.
    """
    required_features = ("task_type",)

    def __init__(self, path=SIMMONS_CSV):
        self.source = SIMMONS_SOURCE
        self.path = Path(path)
        self.rows = self._load(self.path)
        self.sha256 = lf_sha256(self.path)
        super().__init__()

    @staticmethod
    def _load(path):
        try:
            with open(path, encoding="utf-8-sig", newline="") as handle:
                reader = csv.DictReader(handle)
                missing = [c for c in SIMMONS_COLUMNS if c not in (reader.fieldnames or [])]
                if missing:
                    raise SourceTableError("%s thiếu cột: %s" % (path.name, ", ".join(missing)))
                rows = list(reader)
        except OSError as error:
            raise SourceTableError("không đọc được bảng Simmons: %s" % error) from error
        if not rows:
            raise SourceTableError(path.name + " rỗng")
        table = {}
        for line, row in enumerate(rows, start=2):
            task_type = (row["task_type"] or "").strip()
            if not task_type or task_type in table:
                raise SourceTableError("%s dòng %d: task_type rỗng/trùng" % (path.name, line))
            if row["unit"] != SIMMONS_UNIT or row["context"] != SIMMONS_CONTEXT:
                raise SourceTableError("%s dòng %d: unit/context khác nguồn đã kiểm" % (path.name, line))
            try:
                minutes = ceil_minutes(row["mean_duration_min"])
            except (InvalidOperation, ValueError, TypeError):
                raise SourceTableError("%s dòng %d: mean_duration_min không phải số" % (path.name, line))
            if minutes <= 0:
                raise SourceTableError("%s dòng %d: mean_duration_min phải > 0" % (path.name, line))
            table[task_type] = dict(row, minutes=minutes)
        return table

    def supports(self, task_type):
        return task_type in self.rows

    def blockers(self, task):
        row = self.rows[task["task_type"]]
        prefix = "tasks." + task["task_id"]
        note = row["staffing_note"]
        staff = task.get(SINGLE_STAFF_FIELD)
        reasons = []
        if staff is not None and staff != 1:
            reasons.append("%s.%s: task cần %r nhân viên đồng thời, schema hiện chưa hỗ trợ; "
                           "cần thời lượng/điều kiện đã xác nhận" % (prefix, SINGLE_STAFF_FIELD, staff))
        elif "may_require_two_staff" in note and staff != 1:
            reasons.append("%s.%s: %s có thể cần hai nhân viên (Simmons Table 3); cần xác nhận "
                           "số người hỗ trợ trước khi tra" % (prefix, SINGLE_STAFF_FIELD, row["source_task"]))
        if "bed_to_chair_or_walking_only" in note and task.get(MOBILITY_SCOPE_FIELD) not in SIMMONS_MOBILITY_SCOPES:
            reasons.append("%s.%s: Simmons chỉ đo hỗ trợ giường–ghế hoặc đi lại; cần xác nhận loại "
                           "hỗ trợ (bed_to_chair/walking)" % (prefix, MOBILITY_SCOPE_FIELD))
        setting = task.get(SETTING_FIELD)
        if setting is not None and setting not in INPATIENT_SETTINGS:
            reasons.append("%s.%s: '%s' ngoài phạm vi nguồn (nội trú ACE); cần thời lượng đã xác nhận"
                           % (prefix, SETTING_FIELD, setting))
        complexity = task.get(COMPLEXITY_FIELD)
        if complexity is not None and complexity != "standard":
            reasons.append("%s.%s: task phức tạp hơn phạm vi mean nguồn; cần thời lượng đã xác nhận"
                           % (prefix, COMPLEXITY_FIELD))
        if task.get("synchronization"):
            reasons.append(prefix + ".synchronization: cần đồng bộ nhân viên, schema chưa hỗ trợ")
        return reasons

    def predict(self, features):
        row = self.rows.get(features["task_type"])
        return row["minutes"] if row else None


_DEFAULT = None


def default_estimators():
    """Estimator production nội trú. Nạp lười: chỉ đọc CSV khi có task cần tra."""
    global _DEFAULT
    if _DEFAULT is None:
        _DEFAULT = (SimmonsLookupEstimator(),)
    return _DEFAULT
