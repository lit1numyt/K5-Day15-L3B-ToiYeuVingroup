window.NURSEFLOW_DEMO = {
 "generated_at": "2026-11-28T09:59:30",
 "model": {
  "provider": "openai",
  "name": "gpt-4o-mini",
  "tokens_in": 150,
  "tokens_out": 88
 },
 "shift": {
  "shift_id": "S1",
  "ward_id": "W1",
  "shift_length_min": 480,
  "room_switch_min": 2,
  "break_policy": {
   "duration_min": 30,
   "window": [
    120,
    300
   ]
  },
  "coverage_rules": [
   {
    "start": 0,
    "end": 480,
    "zone": "W1",
    "required_skill": null,
    "min_staff": 2
   }
  ],
  "census": 12
 },
 "nurses": [
  {
   "nurse_id": "N1",
   "name": "An"
  },
  {
   "nurse_id": "N2",
   "name": "Bình"
  },
  {
   "nurse_id": "N3",
   "name": "Chi"
  },
  {
   "nurse_id": "N4",
   "name": "Dũng"
  },
  {
   "nurse_id": "N5",
   "name": "Em"
  }
 ],
 "patients": [
  {
   "patient_id": "P1",
   "room": "R1",
   "zone": "W1",
   "acuity_score": 3,
   "adl_dependency": 2,
   "care_category": "medical",
   "isolation_precaution": true
  },
  {
   "patient_id": "P2",
   "room": "R2",
   "zone": "W1",
   "acuity_score": 4,
   "adl_dependency": 1,
   "care_category": "medical",
   "isolation_precaution": false
  },
  {
   "patient_id": "P3",
   "room": "R3",
   "zone": "W1",
   "acuity_score": 1,
   "adl_dependency": 1,
   "care_category": "medical",
   "isolation_precaution": false
  },
  {
   "patient_id": "P4",
   "room": "R4",
   "zone": "W1",
   "acuity_score": 3,
   "adl_dependency": 1,
   "care_category": "medical",
   "isolation_precaution": false
  },
  {
   "patient_id": "P5",
   "room": "R1",
   "zone": "W1",
   "acuity_score": 5,
   "adl_dependency": 2,
   "care_category": "medical",
   "isolation_precaution": false
  },
  {
   "patient_id": "P6",
   "room": "R2",
   "zone": "W1",
   "acuity_score": 1,
   "adl_dependency": 1,
   "care_category": "medical",
   "isolation_precaution": false
  },
  {
   "patient_id": "P7",
   "room": "R3",
   "zone": "W1",
   "acuity_score": 4,
   "adl_dependency": 4,
   "care_category": "medical",
   "isolation_precaution": false
  },
  {
   "patient_id": "P8",
   "room": "R4",
   "zone": "W1",
   "acuity_score": 1,
   "adl_dependency": 2,
   "care_category": "medical",
   "isolation_precaution": true
  },
  {
   "patient_id": "P9",
   "room": "R1",
   "zone": "W1",
   "acuity_score": 1,
   "adl_dependency": 4,
   "care_category": "medical",
   "isolation_precaution": false
  },
  {
   "patient_id": "P10",
   "room": "R2",
   "zone": "W1",
   "acuity_score": 1,
   "adl_dependency": 1,
   "care_category": "medical",
   "isolation_precaution": false
  },
  {
   "patient_id": "P11",
   "room": "R3",
   "zone": "W1",
   "acuity_score": 2,
   "adl_dependency": 1,
   "care_category": "medical",
   "isolation_precaution": false
  },
  {
   "patient_id": "P12",
   "room": "R4",
   "zone": "W1",
   "acuity_score": 5,
   "adl_dependency": 4,
   "care_category": "medical",
   "isolation_precaution": false
  }
 ],
 "tasks": [
  {
   "task_id": "T1",
   "patient_id": "P1",
   "task_type": "med_admin",
   "required_skill": [
    "med_admin"
   ],
   "est_duration_min": 8,
   "duration_source": "given",
   "earliest_start": 0,
   "deadline": 480,
   "mandatory": true,
   "required_skill_level": 1,
   "priority": 1,
   "frequency": "once"
  },
  {
   "task_id": "T2",
   "patient_id": "P2",
   "task_type": "vitals",
   "required_skill": [
    "vitals"
   ],
   "est_duration_min": 5,
   "duration_source": "given",
   "earliest_start": 0,
   "deadline": 480,
   "mandatory": true,
   "required_skill_level": 1,
   "priority": 1,
   "frequency": "once"
  },
  {
   "task_id": "T3",
   "patient_id": "P3",
   "task_type": "wound_care",
   "required_skill": [
    "wound_care"
   ],
   "est_duration_min": 12,
   "duration_source": "given",
   "earliest_start": 0,
   "deadline": 480,
   "mandatory": true,
   "required_skill_level": 1,
   "priority": 1,
   "frequency": "once"
  },
  {
   "task_id": "T4",
   "patient_id": "P4",
   "task_type": "lab_collection",
   "required_skill": [
    "lab_collection"
   ],
   "est_duration_min": 7,
   "duration_source": "given",
   "earliest_start": 0,
   "deadline": 480,
   "mandatory": true,
   "required_skill_level": 1,
   "priority": 3,
   "frequency": "once"
  },
  {
   "task_id": "T5",
   "patient_id": "P5",
   "task_type": "iv_care",
   "required_skill": [
    "iv_care"
   ],
   "est_duration_min": 10,
   "duration_source": "given",
   "earliest_start": 0,
   "deadline": 480,
   "mandatory": true,
   "required_skill_level": 1,
   "priority": 1,
   "frequency": "once"
  },
  {
   "task_id": "T6",
   "patient_id": "P6",
   "task_type": "catheter_care",
   "required_skill": [
    "catheter_care"
   ],
   "est_duration_min": 6,
   "duration_source": "given",
   "earliest_start": 0,
   "deadline": 480,
   "mandatory": true,
   "required_skill_level": 1,
   "priority": 2,
   "frequency": "once"
  },
  {
   "task_id": "T7",
   "patient_id": "P7",
   "task_type": "procedure_care",
   "required_skill": [
    "procedure_care"
   ],
   "est_duration_min": 20,
   "duration_source": "given",
   "earliest_start": 0,
   "deadline": 480,
   "mandatory": true,
   "required_skill_level": 1,
   "priority": 2,
   "frequency": "once"
  },
  {
   "task_id": "T8",
   "patient_id": "P8",
   "task_type": "hygiene",
   "required_skill": [
    "hygiene"
   ],
   "est_duration_min": 15,
   "duration_source": "given",
   "earliest_start": 0,
   "deadline": 480,
   "mandatory": true,
   "required_skill_level": 1,
   "priority": 1,
   "frequency": "once"
  },
  {
   "task_id": "T9",
   "patient_id": "P9",
   "task_type": "med_admin",
   "required_skill": [
    "med_admin"
   ],
   "est_duration_min": 8,
   "duration_source": "given",
   "earliest_start": 0,
   "deadline": 480,
   "mandatory": true,
   "required_skill_level": 1,
   "priority": 3,
   "frequency": "once"
  },
  {
   "task_id": "T10",
   "patient_id": "P10",
   "task_type": "vitals",
   "required_skill": [
    "vitals"
   ],
   "est_duration_min": 5,
   "duration_source": "given",
   "earliest_start": 0,
   "deadline": 480,
   "mandatory": true,
   "required_skill_level": 1,
   "priority": 1,
   "frequency": "once"
  },
  {
   "task_id": "T11",
   "patient_id": "P11",
   "task_type": "wound_care",
   "required_skill": [
    "wound_care"
   ],
   "est_duration_min": 12,
   "duration_source": "given",
   "earliest_start": 0,
   "deadline": 480,
   "mandatory": true,
   "required_skill_level": 1,
   "priority": 3,
   "frequency": "once"
  },
  {
   "task_id": "T12",
   "patient_id": "P12",
   "task_type": "lab_collection",
   "required_skill": [
    "lab_collection"
   ],
   "est_duration_min": 7,
   "duration_source": "given",
   "earliest_start": 0,
   "deadline": 480,
   "mandatory": true,
   "required_skill_level": 1,
   "priority": 2,
   "frequency": "once"
  },
  {
   "task_id": "T13",
   "patient_id": "P1",
   "task_type": "iv_care",
   "required_skill": [
    "iv_care"
   ],
   "est_duration_min": 10,
   "duration_source": "given",
   "earliest_start": 0,
   "deadline": 480,
   "mandatory": true,
   "required_skill_level": 1,
   "priority": 3,
   "frequency": "once"
  },
  {
   "task_id": "T14",
   "patient_id": "P2",
   "task_type": "catheter_care",
   "required_skill": [
    "catheter_care"
   ],
   "est_duration_min": 6,
   "duration_source": "given",
   "earliest_start": 0,
   "deadline": 480,
   "mandatory": true,
   "required_skill_level": 1,
   "priority": 3,
   "frequency": "once"
  },
  {
   "task_id": "T15",
   "patient_id": "P3",
   "task_type": "procedure_care",
   "required_skill": [
    "procedure_care"
   ],
   "est_duration_min": 20,
   "duration_source": "given",
   "earliest_start": 0,
   "deadline": 480,
   "mandatory": true,
   "required_skill_level": 1,
   "priority": 1,
   "frequency": "once"
  },
  {
   "task_id": "T16",
   "patient_id": "P4",
   "task_type": "hygiene",
   "required_skill": [
    "hygiene"
   ],
   "est_duration_min": 15,
   "duration_source": "given",
   "earliest_start": 0,
   "deadline": 480,
   "mandatory": true,
   "required_skill_level": 1,
   "priority": 1,
   "frequency": "once"
  },
  {
   "task_id": "T17",
   "patient_id": "P5",
   "task_type": "med_admin",
   "required_skill": [
    "med_admin"
   ],
   "est_duration_min": 8,
   "duration_source": "given",
   "earliest_start": 0,
   "deadline": 480,
   "mandatory": true,
   "required_skill_level": 1,
   "priority": 3,
   "frequency": "once"
  },
  {
   "task_id": "T18",
   "patient_id": "P6",
   "task_type": "vitals",
   "required_skill": [
    "vitals"
   ],
   "est_duration_min": 5,
   "duration_source": "given",
   "earliest_start": 0,
   "deadline": 480,
   "mandatory": true,
   "required_skill_level": 1,
   "priority": 3,
   "frequency": "once"
  },
  {
   "task_id": "T19",
   "patient_id": "P7",
   "task_type": "wound_care",
   "required_skill": [
    "wound_care"
   ],
   "est_duration_min": 12,
   "duration_source": "given",
   "earliest_start": 0,
   "deadline": 480,
   "mandatory": true,
   "required_skill_level": 1,
   "priority": 3,
   "frequency": "once"
  },
  {
   "task_id": "T20",
   "patient_id": "P8",
   "task_type": "lab_collection",
   "required_skill": [
    "lab_collection"
   ],
   "est_duration_min": 7,
   "duration_source": "given",
   "earliest_start": 0,
   "deadline": 480,
   "mandatory": true,
   "required_skill_level": 1,
   "priority": 1,
   "frequency": "once"
  }
 ],
 "plan": {
  "status": "draft",
  "approval_required": true,
  "assignments": [
   {
    "task_id": "T5",
    "nurse_id": "N1",
    "start": 0,
    "end": 10
   },
   {
    "task_id": "T13",
    "nurse_id": "N1",
    "start": 10,
    "end": 20
   },
   {
    "task_id": "T1",
    "nurse_id": "N1",
    "start": 20,
    "end": 28
   },
   {
    "task_id": "T9",
    "nurse_id": "N1",
    "start": 28,
    "end": 36
   },
   {
    "task_id": "T17",
    "nurse_id": "N2",
    "start": 0,
    "end": 8
   },
   {
    "task_id": "T6",
    "nurse_id": "N3",
    "start": 0,
    "end": 6
   },
   {
    "task_id": "T14",
    "nurse_id": "N3",
    "start": 6,
    "end": 12
   },
   {
    "task_id": "T2",
    "nurse_id": "N3",
    "start": 12,
    "end": 17
   },
   {
    "task_id": "T10",
    "nurse_id": "N3",
    "start": 17,
    "end": 22
   },
   {
    "task_id": "T18",
    "nurse_id": "N3",
    "start": 22,
    "end": 27
   },
   {
    "task_id": "T7",
    "nurse_id": "N4",
    "start": 0,
    "end": 20
   },
   {
    "task_id": "T15",
    "nurse_id": "N4",
    "start": 20,
    "end": 40
   },
   {
    "task_id": "T3",
    "nurse_id": "N5",
    "start": 0,
    "end": 12
   },
   {
    "task_id": "T11",
    "nurse_id": "N5",
    "start": 12,
    "end": 24
   },
   {
    "task_id": "T19",
    "nurse_id": "N5",
    "start": 24,
    "end": 36
   },
   {
    "task_id": "T8",
    "nurse_id": "N2",
    "start": 10,
    "end": 25
   },
   {
    "task_id": "T16",
    "nurse_id": "N2",
    "start": 25,
    "end": 40
   },
   {
    "task_id": "T4",
    "nurse_id": "N2",
    "start": 40,
    "end": 47
   },
   {
    "task_id": "T12",
    "nurse_id": "N2",
    "start": 47,
    "end": 54
   },
   {
    "task_id": "T20",
    "nurse_id": "N2",
    "start": 54,
    "end": 61
   }
  ],
  "breaks": [
   {
    "nurse_id": "N1",
    "start": 120,
    "end": 150
   },
   {
    "nurse_id": "N2",
    "start": 150,
    "end": 180
   },
   {
    "nurse_id": "N3",
    "start": 180,
    "end": 210
   },
   {
    "nurse_id": "N4",
    "start": 210,
    "end": 240
   },
   {
    "nurse_id": "N5",
    "start": 240,
    "end": 270
   }
  ],
  "metrics": {
   "workload_minutes": {
    "N1": 36,
    "N2": 61,
    "N3": 27,
    "N4": 40,
    "N5": 36
   },
   "overhead_minutes": 2,
   "utilization_cv": 0.283284309484306,
   "peak_utilization": 0.14523809523809525
  },
  "explanation": "Đã kiểm kỹ năng, cửa giờ, tải, chuyển phòng, nghỉ và coverage theo input; trưởng ca duyệt trước khi áp dụng."
 },
 "taxonomy": {
  "P1": {
   "tier": 2,
   "workload_weight": 6,
   "care_category": "medical",
   "basis": "rule fallback (điểm cắt học ≤4/≤6, đồng bộ model) — không phải phút."
  },
  "P2": {
   "tier": 2,
   "workload_weight": 5,
   "care_category": "medical",
   "basis": "rule fallback (điểm cắt học ≤4/≤6, đồng bộ model) — không phải phút."
  },
  "P3": {
   "tier": 1,
   "workload_weight": 2,
   "care_category": "medical",
   "basis": "rule fallback (điểm cắt học ≤4/≤6, đồng bộ model) — không phải phút."
  },
  "P4": {
   "tier": 1,
   "workload_weight": 4,
   "care_category": "medical",
   "basis": "rule fallback (điểm cắt học ≤4/≤6, đồng bộ model) — không phải phút."
  },
  "P5": {
   "tier": 3,
   "workload_weight": 7,
   "care_category": "medical",
   "basis": "rule fallback (điểm cắt học ≤4/≤6, đồng bộ model) — không phải phút."
  },
  "P6": {
   "tier": 1,
   "workload_weight": 2,
   "care_category": "medical",
   "basis": "rule fallback (điểm cắt học ≤4/≤6, đồng bộ model) — không phải phút."
  },
  "P7": {
   "tier": 3,
   "workload_weight": 8,
   "care_category": "medical",
   "basis": "rule fallback (điểm cắt học ≤4/≤6, đồng bộ model) — không phải phút."
  },
  "P8": {
   "tier": 1,
   "workload_weight": 4,
   "care_category": "medical",
   "basis": "rule fallback (điểm cắt học ≤4/≤6, đồng bộ model) — không phải phút."
  },
  "P9": {
   "tier": 2,
   "workload_weight": 5,
   "care_category": "medical",
   "basis": "rule fallback (điểm cắt học ≤4/≤6, đồng bộ model) — không phải phút."
  },
  "P10": {
   "tier": 1,
   "workload_weight": 2,
   "care_category": "medical",
   "basis": "rule fallback (điểm cắt học ≤4/≤6, đồng bộ model) — không phải phút."
  },
  "P11": {
   "tier": 1,
   "workload_weight": 3,
   "care_category": "medical",
   "basis": "rule fallback (điểm cắt học ≤4/≤6, đồng bộ model) — không phải phút."
  },
  "P12": {
   "tier": 3,
   "workload_weight": 9,
   "care_category": "medical",
   "basis": "rule fallback (điểm cắt học ≤4/≤6, đồng bộ model) — không phải phút."
  }
 },
 "ai_text": "Kế hoạch phân bổ công việc cho ca S1 gồm 5 điều dưỡng với tổng số 20 việc đã được thực hiện. Cụ thể: An 4 việc, Bình 6 việc, Chi 5 việc, Dũng 2 việc, và Em 3 việc. Chỉ số CV là 0.283 và peak là 0.145, cho thấy mức độ cân bằng tải trong phân công công việc.",
 "baselines": {
  "count": {
   "workload_minutes": {
    "N1": 55,
    "N2": 56,
    "N3": 42,
    "N4": 39,
    "N5": 20
   },
   "overhead_minutes": 14,
   "utilization_cv": 0.3088091944025077,
   "peak_utilization": 0.13333333333333333
  },
  "weight": {
   "workload_minutes": {
    "N1": 14,
    "N2": 44,
    "N3": 42,
    "N4": 55,
    "N5": 55
   },
   "overhead_minutes": 12,
   "utilization_cv": 0.357301552043887,
   "peak_utilization": 0.13095238095238096
  },
  "nurseflow": {
   "workload_minutes": {
    "N1": 36,
    "N2": 61,
    "N3": 27,
    "N4": 40,
    "N5": 36
   },
   "overhead_minutes": 2,
   "utilization_cv": 0.283284309484306,
   "peak_utilization": 0.14523809523809525
  }
 }
};
