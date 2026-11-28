# team info:

## Members

Đồng Hữu Nguyên Khoa - 2A202604000 - lit1numyt - leader

Nguyễn Đức Khương Lam
2A202604020
Github RachalHys

Trần Trung Kiên
2A202604014
ttkien0710

Nguyễn Quang Tiệp
2A202603946
nguyenquangtiep

## Track B - Healthcare

# NurseFlow — Product Requirements Document

**Version:** 0.1  
**Status:** Initial Draft  
**Hackathon:** VinAI Talent Program  
**Checkpoint:** 1 — Track & Problem Selection  
**Domain:** Healthcare  
**Focus:** Nursing Workforce Optimization

---

## 1. Product Overview

**NurseFlow** is an intelligent nursing workforce orchestration system that helps hospitals distribute nursing workloads more effectively, coordinate patient-care tasks, and protect nurses' rest periods while maintaining continuous patient coverage.

Rather than assigning nurses based solely on patient counts, NurseFlow considers patient acuity, required care activities, task deadlines, nurse qualifications, staff availability, and workload fluctuations throughout a shift.

**Core idea:** Optimize how nursing work is distributed over time—not simply how many patients each nurse receives.

## 2. Problem Statement

Traditional nurse allocation approaches often rely on patient-to-nurse ratios or static shift assignments. However, these approaches may overlook important workload differences:

- **Unequal patient acuity:** Two nurses caring for the same number of patients may face very different workloads.
- **Temporal workload peaks:** Medication rounds, procedures, admissions, and handovers can create periods of concentrated demand.
- **Insufficient rest opportunities:** Nurses may have unoccupied intervals without having enough coverage to take a genuine break.
- **Static scheduling:** Unexpected events, such as patient deterioration or staff absence, can invalidate the original schedule.

This can result in workload imbalance, missed scheduling opportunities, interrupted breaks, and inefficient workforce utilization.

## 3. Target Users

| User | Primary Need |
|---|---|
| Nurse-in-charge / Ward Manager | Monitor workload and approve staffing adjustments |
| Staff Nurses | Receive balanced assignments and protected breaks |
| Hospital Operations Management | Understand staffing utilization and workload distribution |

## 4. Proposed Solution

NurseFlow consists of three core modules.

### 4.1 Acuity & Workforce Intelligence

Estimate nursing workload using:

- Patient acuity and care requirements.
- Expected nursing task durations.
- Nurse qualifications and skills.
- Staff availability and shift constraints.

### 4.2 Intelligent Shift Orchestrator

- Generate nurse-patient assignments.
- Schedule time-sensitive care tasks.
- Coordinate compatible nursing activities.
- Allocate protected breaks.
- Balance workloads across nurses and time slots.

### 4.3 Live Ward Operations

- Display workload distribution and scheduling conflicts.
- Monitor changes in ward conditions.
- Detect unexpected events, such as patient deterioration or staff absence.
- Propose updated schedules for nurse-in-charge approval.

## 5. Core Workflow

1. **Input ward information:** Patient census, acuity levels, care requirements, nursing staff, qualifications, and shift availability.
2. **Estimate workload:** Convert patient-care requirements into time-dependent nursing tasks, including durations, priorities, and deadlines.
3. **Generate optimized schedule:** Allocate nurses, distribute tasks, coordinate compatible activities, and identify protected break opportunities.
4. **Monitor ward operations:** Track workload changes and identify unexpected events.
5. **Re-optimize and approve:** Generate updated recommendations while preserving patient-care coverage. The nurse-in-charge reviews and approves changes.

## 6. MVP Scope

For the hackathon, prioritize a working prototype over a comprehensive hospital management system.

### 6.1 Must Have

- Synthetic general acute-care ward scenario generator.
- Patient acuity and nursing workload estimation.
- Nurse availability and skill-based assignment.
- Time-dependent task scheduling.
- Protected break allocation with coverage constraints.
- Optimization engine that generates a feasible shift schedule.
- Dashboard displaying workload distribution and schedule results.

### 6.2 Should Have

- Event-driven re-optimization when patient acuity changes or a nurse becomes unavailable.
- Workload heatmap across time slots.
- Nurse-in-charge approval workflow.
- Comparison against conventional patient-count-based allocation.

### 6.3 Out of Scope for MVP

- Integration with real hospital information systems.
- Autonomous clinical decision-making.
- Predicting patient deterioration using trained ML models.
- Production deployment or claims of improved clinical outcomes.

## 7. Technical Direction

| Component | Proposed Technology |
|---|---|
| Frontend | React + TypeScript |
| Backend | Python + FastAPI |
| Optimization | Google OR-Tools CP-SAT |
| Database | SQLite initially |
| Visualization | Recharts / ECharts |
| AI Assistance | Optional LLM for natural-language input and schedule explanations |

**Optimization principle:** Patient safety and required clinical coverage are hard constraints. Workload balance, scheduling efficiency, and rest opportunities are optimization objectives—not reasons to violate safety requirements.

## 8. Data Strategy

Adopt a **hybrid approach**: use real-world datasets to inform the model, then generate unified synthetic ward scenarios for experimentation.

| Dataset / Source | Intended Use |
|---|---|
| [MatchRN — University of Basel](https://zenodo.org/records/15248072) | Real nurse shift patterns, staffing, and perceived workload |
| [McGill Nursing Workload Tool](https://borealisdata.ca/dataset.xhtml?persistentId=doi:10.5683/SP4/L1ZBLT) | Workload categories and scoring methodology |
| [Nurse Rostering Benchmarks](https://www.schedulingbenchmarks.org/nrp/) | Scheduling constraints and optimization benchmarks |
| [KU Leuven Nurse Rostering Datasets](https://gent.cs.kuleuven.be/nurserostering.html) | Staffing scenarios and absence-related scheduling tests |
| [CMS Payroll-Based Journal](https://data.cms.gov/quality-of-care/payroll-based-journal-daily-nurse-staffing) | Optional contextual staffing statistics |

The synthetic generator will combine:

- Patient acuity and care requirements.
- Nurse availability and qualifications.
- Nursing tasks and estimated durations.
- Task priorities and deadlines.
- Shift schedules and protected breaks.
- Operational events such as patient deterioration and staff absence.

**Data limitation:** No single identified dataset provides all required patient acuity, individual nurse schedules, time-dependent nursing tasks, and break information. Real-world datasets will therefore inform individual components rather than serve as a complete unified ground truth.

## 9. Evaluation Criteria

NurseFlow will be evaluated against simpler allocation and scheduling approaches.

| Metric | What It Measures |
|---|---|
| Workload Imbalance (CV) | How unevenly workload is distributed |
| Peak Workload | Maximum workload experienced across nurses and time slots |
| Task Deadline Compliance | Percentage of required tasks completed within their scheduling windows |
| Protected Break Fulfillment | Percentage of planned breaks successfully delivered |
| Coverage Violations | Violations of required staffing, skill, or monitoring coverage |
| Re-optimization Time | Time needed to produce an updated schedule |
| Solver Performance | Time to first feasible solution and final solution quality |

### 9.1 Baseline Comparisons

1. **Patient-count-based allocation:** Assign nurses based primarily on patient counts.
2. **Acuity-based allocation:** Consider patient acuity without temporal scheduling.
3. **Static optimized scheduling:** Optimize the initial schedule without dynamic reallocation.
4. **NurseFlow:** Combine acuity, temporal workload, protected breaks, and dynamic re-optimization.

## 10. Success Criteria and Expected Outcome

The MVP should demonstrate that NurseFlow can:

- Generate a feasible nurse allocation and shift schedule from ward inputs.
- Account for differences in patient acuity and time-dependent care requirements.
- Balance workloads without violating mandatory coverage constraints.
- Identify and schedule genuine protected breaks.
- Respond to unexpected operational events through re-optimization.
- Demonstrate measurable differences against conventional allocation baselines.

**Expected Deliverable:** An interactive prototype demonstrating workload estimation, schedule generation, workload visualization, and dynamic schedule adjustment in a simulated acute-care ward.

---

## 11. Initial Project Pitch

Hospitals don't just have a nurse allocation problem; they have a workload orchestration problem.

Traditional staffing approaches often distribute nurses based on patient counts, overlooking patient acuity, time-dependent care activities, workload peaks, and opportunities for genuine rest.

**NurseFlow** is an intelligent nursing workforce orchestration system that combines patient acuity assessment, temporal task scheduling, workforce optimization, and dynamic reallocation.

Our goal is to help hospitals maintain patient-care coverage while distributing nursing workloads more fairly and creating protected opportunities for nurses to rest.