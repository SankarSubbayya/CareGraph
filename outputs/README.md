# CareGraph Clinical AI Pipeline Outputs

This directory contains the standardized JSON outputs for the four-stage clinical AI diagnostic pipeline.

## Pipeline Flow

1. **Check-in Analysis (`checkin_analysis.json`)**
   - Extracts symptoms, mood, wellness score, and a short clinical summary from the raw transcript.
   - **Model**: Gemini 3.1 Flash-Lite

2. **Condition Suggestion (`condition_suggestion.json`)**
   - Chaines the analysis with the transcript to suggest up to 3 potential conditions based on clinical indicators.
   - **Model**: Gemini 3.1 Flash-Lite

3. **Drug Interaction (`drug_interaction.json`)**
   - Correlates the patient's existing medications with their reported symptoms and suggested conditions to identify safety risks or side effects.
   - **Model**: Gemini 3.1 Flash-Lite

4. **Final Care Plan (`final_care_plan.json`)**
   - Synthesizes all previous steps into a final, actionable clinical recommendation for the family and care team.
   - **Model**: Gemini 3.1 Flash-Lite

## Data Schema (Standardized)

All files follow a scenario-based structure:
```json
{
  "Scenario Name": {
    "input": "...",
    "output": {
      "explanation": "...",
      "severity": "low|medium|high",
      "symptoms_to_watch": [],
      "action": "..."
    }
  }
}
```

## Scenarios Tested
- **Healthy/Positive**: Baseline check-in with no issues.
- **Concerning Symptoms**: Dizziness and pallor while on antihypertensives.
- **Non-Adherence / Loneliness**: Missed doses and psychological distress.
- **Critical / Respiratory Distress**: Emergency asthma/cardiac symptoms unresponsive to inhaler.
