"""L3 · Workload/duration estimator của NurseFlow (chủ: Tiệp).

Seam theo docs/module-contract.md §3.3: estimate_duration(instance) -> instance'.
Production nội trú: given → Simmons Table 3 lookup → need_info. Không nạp model OR thực nghiệm.
"""
from .estimator import (DurationNeedInfo, InvalidInstance, assess_durations,
                        estimate_duration)
from .models import (SIMMONS_SOURCE, DurationEstimator, LookupTableEstimator, MedianBaseline,
                     SimmonsLookupEstimator, SourceTableError)

__all__ = ["estimate_duration", "assess_durations", "DurationNeedInfo", "InvalidInstance",
           "SourceTableError", "DurationEstimator", "LookupTableEstimator", "MedianBaseline",
           "SimmonsLookupEstimator", "SIMMONS_SOURCE"]
