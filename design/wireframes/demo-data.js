window.NURSEFLOW_DEMO = {
 "generated_at": "2026-11-28T12:54:39+07:00",
 "data_kind": "synthetic",
 "seed": 7,
 "display_start_min": 420,
 "model": {
  "provider": "openai",
  "name": "gpt-4o-mini",
  "tokens_in": 168,
  "tokens_out": 120
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
  "census": 20
 },
 "nurses": [
  {
   "nurse_id": "N1",
   "name": "Nguyễn Thị An"
  },
  {
   "nurse_id": "N2",
   "name": "Trần Văn Bình"
  },
  {
   "nurse_id": "N3",
   "name": "Lê Thị Cúc"
  },
  {
   "nurse_id": "N4",
   "name": "Phạm Minh Dũng"
  },
  {
   "nurse_id": "N5",
   "name": "Hoàng Thị Hoa"
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
  },
  {
   "patient_id": "P13",
   "room": "R1",
   "zone": "W1",
   "acuity_score": 1,
   "adl_dependency": 2,
   "care_category": "medical",
   "isolation_precaution": false
  },
  {
   "patient_id": "P14",
   "room": "R2",
   "zone": "W1",
   "acuity_score": 1,
   "adl_dependency": 2,
   "care_category": "medical",
   "isolation_precaution": false
  },
  {
   "patient_id": "P15",
   "room": "R3",
   "zone": "W1",
   "acuity_score": 3,
   "adl_dependency": 4,
   "care_category": "medical",
   "isolation_precaution": true
  },
  {
   "patient_id": "P16",
   "room": "R4",
   "zone": "W1",
   "acuity_score": 2,
   "adl_dependency": 1,
   "care_category": "medical",
   "isolation_precaution": false
  },
  {
   "patient_id": "P17",
   "room": "R1",
   "zone": "W1",
   "acuity_score": 5,
   "adl_dependency": 3,
   "care_category": "medical",
   "isolation_precaution": false
  },
  {
   "patient_id": "P18",
   "room": "R2",
   "zone": "W1",
   "acuity_score": 5,
   "adl_dependency": 2,
   "care_category": "medical",
   "isolation_precaution": false
  },
  {
   "patient_id": "P19",
   "room": "R3",
   "zone": "W1",
   "acuity_score": 1,
   "adl_dependency": 2,
   "care_category": "medical",
   "isolation_precaution": false
  },
  {
   "patient_id": "P20",
   "room": "R4",
   "zone": "W1",
   "acuity_score": 3,
   "adl_dependency": 1,
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
   "priority": 3,
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
   "priority": 3,
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
   "priority": 3,
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
   "priority": 1,
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
   "priority": 2,
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
   "priority": 3,
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
   "priority": 2,
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
   "patient_id": "P13",
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
   "priority": 2,
   "frequency": "once"
  },
  {
   "task_id": "T14",
   "patient_id": "P14",
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
   "patient_id": "P15",
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
   "task_id": "T16",
   "patient_id": "P16",
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
   "priority": 2,
   "frequency": "once"
  },
  {
   "task_id": "T17",
   "patient_id": "P17",
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
   "priority": 2,
   "frequency": "once"
  },
  {
   "task_id": "T18",
   "patient_id": "P18",
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
   "task_id": "T19",
   "patient_id": "P19",
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
   "task_id": "T20",
   "patient_id": "P20",
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
   "task_id": "T21",
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
   "priority": 1,
   "frequency": "once"
  },
  {
   "task_id": "T22",
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
   "priority": 1,
   "frequency": "once"
  },
  {
   "task_id": "T23",
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
   "priority": 3,
   "frequency": "once"
  },
  {
   "task_id": "T24",
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
   "priority": 2,
   "frequency": "once"
  }
 ],
 "plan": {
  "status": "draft",
  "approval_required": true,
  "method": "cp_sat",
  "validation": {
   "valid": true,
   "violations": [],
   "metrics": {
    "workload_minutes": {
     "N1": 52,
     "N2": 53,
     "N3": 52,
     "N4": 53,
     "N5": 53
    },
    "overhead_minutes": 14,
    "utilization_cv": 0.009313649212103306,
    "peak_utilization": 0.1261904761904762
   }
  },
  "unassigned_tasks": [],
  "assignments": [
   {
    "task_id": "T19",
    "nurse_id": "N1",
    "start": 0,
    "end": 12
   },
   {
    "task_id": "T23",
    "nurse_id": "N1",
    "start": 20,
    "end": 40
   },
   {
    "task_id": "T15",
    "nurse_id": "N1",
    "start": 40,
    "end": 60
   },
   {
    "task_id": "T24",
    "nurse_id": "N2",
    "start": 3,
    "end": 18
   },
   {
    "task_id": "T16",
    "nurse_id": "N2",
    "start": 18,
    "end": 33
   },
   {
    "task_id": "T2",
    "nurse_id": "N2",
    "start": 35,
    "end": 40
   },
   {
    "task_id": "T12",
    "nurse_id": "N2",
    "start": 42,
    "end": 49
   },
   {
    "task_id": "T20",
    "nurse_id": "N2",
    "start": 49,
    "end": 56
   },
   {
    "task_id": "T7",
    "nurse_id": "N3",
    "start": 2,
    "end": 22
   },
   {
    "task_id": "T3",
    "nurse_id": "N3",
    "start": 22,
    "end": 34
   },
   {
    "task_id": "T14",
    "nurse_id": "N3",
    "start": 36,
    "end": 42
   },
   {
    "task_id": "T22",
    "nurse_id": "N3",
    "start": 42,
    "end": 48
   },
   {
    "task_id": "T6",
    "nurse_id": "N3",
    "start": 50,
    "end": 56
   },
   {
    "task_id": "T18",
    "nurse_id": "N4",
    "start": 0,
    "end": 5
   },
   {
    "task_id": "T10",
    "nurse_id": "N4",
    "start": 5,
    "end": 10
   },
   {
    "task_id": "T17",
    "nurse_id": "N4",
    "start": 12,
    "end": 20
   },
   {
    "task_id": "T1",
    "nurse_id": "N4",
    "start": 20,
    "end": 28
   },
   {
    "task_id": "T9",
    "nurse_id": "N4",
    "start": 28,
    "end": 36
   },
   {
    "task_id": "T8",
    "nurse_id": "N4",
    "start": 38,
    "end": 53
   },
   {
    "task_id": "T4",
    "nurse_id": "N5",
    "start": 3,
    "end": 10
   },
   {
    "task_id": "T5",
    "nurse_id": "N5",
    "start": 50,
    "end": 60
   },
   {
    "task_id": "T13",
    "nurse_id": "N5",
    "start": 60,
    "end": 70
   },
   {
    "task_id": "T21",
    "nurse_id": "N5",
    "start": 70,
    "end": 80
   },
   {
    "task_id": "T11",
    "nurse_id": "N5",
    "start": 82,
    "end": 94
   }
  ],
  "breaks": [
   {
    "nurse_id": "N1",
    "start": 150,
    "end": 180
   },
   {
    "nurse_id": "N2",
    "start": 120,
    "end": 150
   },
   {
    "nurse_id": "N3",
    "start": 120,
    "end": 150
   },
   {
    "nurse_id": "N4",
    "start": 120,
    "end": 150
   },
   {
    "nurse_id": "N5",
    "start": 150,
    "end": 180
   }
  ],
  "metrics": {
   "workload_minutes": {
    "N1": 52,
    "N2": 53,
    "N3": 52,
    "N4": 53,
    "N5": 53
   },
   "overhead_minutes": 14,
   "utilization_cv": 0.009313649212103306,
   "peak_utilization": 0.1261904761904762
  },
  "explanation": "Bản nháp phân công điều dưỡng cho ca S1 đã được lập với 5 y tá (N1, N2, N3, N4, N5) và các nhiệm vụ cho bệnh nhân từ P1 đến P20. Các nhiệm vụ đã được phân công dựa trên kỹ năng phù hợp của y tá với từng loại nhiệm vụ, đảm bảo mọi y tá đều có thể thực hiện các công việc được giao. Cụ thể, y tá N1 chịu trách nhiệm chính cho các nhiệm vụ về điều trị vết thương (T19, T23, T15) và có khung giờ làm việc hợp lý. Căn cứ vào khả năng cân bằng tải giữa các y tá, mỗi người đều có khối lượng công việc tương đương (được thể hiện qua số phút làm việc). Bản phân công này đang chờ trưởng ca duyệt."
 },
 "taxonomy": {
  "P1": {
   "tier": 2,
   "workload_weight": 6,
   "care_category": "medical",
   "basis": "KMeans taxonomy v1.9.1 (workload_score) — trọng số tương đối, không phải phút."
  },
  "P2": {
   "tier": 2,
   "workload_weight": 5,
   "care_category": "medical",
   "basis": "KMeans taxonomy v1.9.1 (workload_score) — trọng số tương đối, không phải phút."
  },
  "P3": {
   "tier": 1,
   "workload_weight": 2,
   "care_category": "medical",
   "basis": "KMeans taxonomy v1.9.1 (workload_score) — trọng số tương đối, không phải phút."
  },
  "P4": {
   "tier": 1,
   "workload_weight": 4,
   "care_category": "medical",
   "basis": "KMeans taxonomy v1.9.1 (workload_score) — trọng số tương đối, không phải phút."
  },
  "P5": {
   "tier": 3,
   "workload_weight": 7,
   "care_category": "medical",
   "basis": "KMeans taxonomy v1.9.1 (workload_score) — trọng số tương đối, không phải phút."
  },
  "P6": {
   "tier": 1,
   "workload_weight": 2,
   "care_category": "medical",
   "basis": "KMeans taxonomy v1.9.1 (workload_score) — trọng số tương đối, không phải phút."
  },
  "P7": {
   "tier": 3,
   "workload_weight": 8,
   "care_category": "medical",
   "basis": "KMeans taxonomy v1.9.1 (workload_score) — trọng số tương đối, không phải phút."
  },
  "P8": {
   "tier": 1,
   "workload_weight": 4,
   "care_category": "medical",
   "basis": "KMeans taxonomy v1.9.1 (workload_score) — trọng số tương đối, không phải phút."
  },
  "P9": {
   "tier": 2,
   "workload_weight": 5,
   "care_category": "medical",
   "basis": "KMeans taxonomy v1.9.1 (workload_score) — trọng số tương đối, không phải phút."
  },
  "P10": {
   "tier": 1,
   "workload_weight": 2,
   "care_category": "medical",
   "basis": "KMeans taxonomy v1.9.1 (workload_score) — trọng số tương đối, không phải phút."
  },
  "P11": {
   "tier": 1,
   "workload_weight": 3,
   "care_category": "medical",
   "basis": "KMeans taxonomy v1.9.1 (workload_score) — trọng số tương đối, không phải phút."
  },
  "P12": {
   "tier": 3,
   "workload_weight": 9,
   "care_category": "medical",
   "basis": "KMeans taxonomy v1.9.1 (workload_score) — trọng số tương đối, không phải phút."
  },
  "P13": {
   "tier": 1,
   "workload_weight": 3,
   "care_category": "medical",
   "basis": "KMeans taxonomy v1.9.1 (workload_score) — trọng số tương đối, không phải phút."
  },
  "P14": {
   "tier": 1,
   "workload_weight": 3,
   "care_category": "medical",
   "basis": "KMeans taxonomy v1.9.1 (workload_score) — trọng số tương đối, không phải phút."
  },
  "P15": {
   "tier": 3,
   "workload_weight": 8,
   "care_category": "medical",
   "basis": "KMeans taxonomy v1.9.1 (workload_score) — trọng số tương đối, không phải phút."
  },
  "P16": {
   "tier": 1,
   "workload_weight": 3,
   "care_category": "medical",
   "basis": "KMeans taxonomy v1.9.1 (workload_score) — trọng số tương đối, không phải phút."
  },
  "P17": {
   "tier": 3,
   "workload_weight": 8,
   "care_category": "medical",
   "basis": "KMeans taxonomy v1.9.1 (workload_score) — trọng số tương đối, không phải phút."
  },
  "P18": {
   "tier": 3,
   "workload_weight": 7,
   "care_category": "medical",
   "basis": "KMeans taxonomy v1.9.1 (workload_score) — trọng số tương đối, không phải phút."
  },
  "P19": {
   "tier": 1,
   "workload_weight": 3,
   "care_category": "medical",
   "basis": "KMeans taxonomy v1.9.1 (workload_score) — trọng số tương đối, không phải phút."
  },
  "P20": {
   "tier": 1,
   "workload_weight": 4,
   "care_category": "medical",
   "basis": "KMeans taxonomy v1.9.1 (workload_score) — trọng số tương đối, không phải phút."
  }
 },
 "ai_text": "Trong ca S1, có 5 điều dưỡng được phân bổ 24 việc, với số việc phân công tương đối đều: Nguyễn Thị An 3 việc, Trần Văn Bình 5 việc, Lê Thị Cúc 5 việc, Phạm Minh Dũng 6 việc và Hoàng Thị Hoa 5 việc. Chỉ số CV là 0.009 cho thấy sự ổn định trong phân bố công việc, trong khi chỉ số peak là 0.126 cho thấy một số điều dưỡng có khối lượng công việc nhẹ hơn so với người khác.",
 "baselines": {
  "count": {
   "workload_minutes": {
    "N1": 48,
    "N2": 57,
    "N3": 38,
    "N4": 81,
    "N5": 55
   },
   "overhead_minutes": 30,
   "utilization_cv": 0.2553118827026255,
   "peak_utilization": 0.19285714285714287
  },
  "weight": {
   "workload_minutes": {
    "N1": 51,
    "N2": 39,
    "N3": 55,
    "N4": 57,
    "N5": 63
   },
   "overhead_minutes": 16,
   "utilization_cv": 0.1509433962264151,
   "peak_utilization": 0.15
  },
  "nurseflow": {
   "workload_minutes": {
    "N1": 52,
    "N2": 53,
    "N3": 52,
    "N4": 53,
    "N5": 53
   },
   "overhead_minutes": 14,
   "utilization_cv": 0.009313649212103306,
   "peak_utilization": 0.1261904761904762
  }
 }
};
