# EHR Dataset Sample Data Summary

**Source:** [dataframer/ehr-multi-file-patient-samples](https://huggingface.co/datasets/dataframer/ehr-multi-file-patient-samples)
**Type:** Synthetic EHR / cardiac stress test reports
**Total rows:** 3,942 lines across ~33 reports for 13 unique patients

---

## Patients Extracted

| # | Name | Patient ID | Gender | Age Group | Condition |
|---|------|-----------|--------|-----------|-----------|
| 1 | James Rodriguez | PC-114-2024 | Male | Middle-Aged (45-69) | Normal Cardiac Function |
| 2 | Jennifer Johnson | PC-104-2024 | Female | Elderly (70+) | Normal Cardiac Function |
| 3 | Linda Chen | — | Female | Middle-Aged (45-69) | Normal Cardiac Function |
| 4 | Dorothy Williams | DW-892-2024 | Female | Elderly (70+) | Normal Cardiac Function |
| 5 | Patricia Anderson | — | Female | Middle-Aged (45-69) | Normal Cardiac Function |
| 6 | William Rodriguez | WR-928-2024 | Male | Middle-Aged (45-69) | Severe Multi-vessel CAD |
| 7 | Dorothy Thompson | — | Female | Elderly (70+) | Severe Multi-vessel CAD |
| 8 | James Davis | JD-452-991 | Female | Middle-Aged (45-69) | Normal Cardiac Function |
| 9 | Elizabeth Brown | — | Female | Young Adult (25-44) | Severe Multi-vessel CAD |
| 10 | Patricia Chen | PC-092-2024 | Male | Young Adult (25-44) | Normal Cardiac Function |
| 11 | Dorothy Wilson | — | Female | Elderly (70+) | Normal Cardiac Function |
| 12 | Patricia Thompson | — | Female | Elderly (70+) | Normal Cardiac Function |
| 13 | Robert Johnson | — | Male | — | Severe Multi-vessel CAD |
| 14 | Linda Martinez | — | Female | Elderly (70+) | Normal Cardiac Function |

---

## Medications Found in Dataset

| Medication | Dosage | Frequency | Use Case |
|-----------|--------|-----------|----------|
| Lisinopril | 10mg | Daily | Hypertension (ACE inhibitor) |
| Metoprolol | 25mg | Daily | Heart rate control (Beta-blocker) |
| Atorvastatin | 20mg | Daily | Cholesterol (Statin) |
| Alendronate | 70mg | Weekly | Osteoporosis |
| Omeprazole | 20mg | PRN | Acid reflux (PPI) |
| Sertraline | 50mg | Daily | Depression/Anxiety (SSRI) |

---

## Symptoms Recorded

| Symptom | Occurrences | Context |
|---------|-------------|---------|
| Chest Pain | Multiple | Present in severe CAD cases, absent in normal |
| Shortness of Breath | Most reports | Mild (normal) to Severe (CAD) |
| Dizziness | Some | Side effect of Lisinopril, Metoprolol |
| Fatigue | Most reports | Common across elderly patients |
| Palpitations | Rare | Occasional during stress tests |
| Nausea | Rare | Usually not present |
| Diaphoresis | Rare | Present in severe CAD cases |

---

## Clinical Conditions

| Condition | Description |
|-----------|-------------|
| Normal Cardiac Function | Symptoms ruled out, healthy baseline, discharge |
| Severe Multi-vessel CAD | Critical findings requiring surgical intervention |
| Hypertension | Mentioned in clinical indications |
| Coronary Artery Disease | Detected via stress testing |

---

## Vitals Ranges

| Vital | Range in Dataset |
|-------|-----------------|
| Resting Heart Rate | 68-76 bpm |
| Blood Pressure | 124/76 - 162/94 mmHg |
| O2 Saturation | 96-98% |
| Rest EF | 42-65% |
| Stress EF | 32-72%+ |
| METs | 3.8-12.4 |

---

## Relevance to CareGraph

This dataset provides realistic senior patient profiles for seeding CareGraph:

- **Elderly patients (70+):** Dorothy Williams, Jennifer Johnson, Dorothy Thompson, Dorothy Wilson, Patricia Thompson, Linda Martinez — ideal for senior care scenarios
- **Medications with known interactions:** Lisinopril + Metoprolol (both lower BP), Atorvastatin + Omeprazole (absorption interaction)
- **Symptoms to model:** Dizziness (Lisinopril side effect), Fatigue (Metoprolol side effect), Chest Pain, Shortness of Breath
- **Conditions:** Hypertension, Coronary Artery Disease, Osteoporosis, Depression/Anxiety

### Suggested CareGraph Seed Mapping

```
(:Senior {name: "Dorothy Williams", age: 72, phone: "555-0101"})
  -[:TAKES]-> (:Medication {name: "Lisinopril", dosage: "10mg", frequency: "daily"})
  -[:TAKES]-> (:Medication {name: "Atorvastatin", dosage: "20mg", frequency: "daily"})
  -[:TAKES]-> (:Medication {name: "Metoprolol", dosage: "25mg", frequency: "daily"})
  -[:REPORTED]-> (:Symptom {name: "fatigue"})
  -[:REPORTED]-> (:Symptom {name: "chest discomfort"})

(:Medication {name: "Lisinopril"}) -[:SIDE_EFFECT]-> (:Symptom {name: "dizziness"})
(:Medication {name: "Lisinopril"}) -[:SIDE_EFFECT]-> (:Symptom {name: "fatigue"})
(:Medication {name: "Metoprolol"}) -[:SIDE_EFFECT]-> (:Symptom {name: "dizziness"})
(:Medication {name: "Metoprolol"}) -[:SIDE_EFFECT]-> (:Symptom {name: "fatigue"})
(:Medication {name: "Lisinopril"}) -[:INTERACTS_WITH]-> (:Medication {name: "Metoprolol"})

(:Symptom {name: "chest discomfort"}) -[:SUGGESTS]-> (:Condition {name: "Coronary Artery Disease"})
(:Symptom {name: "dizziness"}) -[:SUGGESTS]-> (:Condition {name: "Hypotension"})
```
