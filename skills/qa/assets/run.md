# QA: {feature}

- Run: {date/time}; scope and intent source: {request/spec/conversation}
- Build: {revision plus relevant local-change identity}; target: {URL/device/binary/host}
- Environment: {versions, configuration, fixture identifiers; no credentials}
- Procedure: {link}; actual setup/deviations: {commands, inputs, injected faults}

## Scenario matrix

| ID | Priority | Entry/precondition | Actions and inputs | Expected intermediate/final state | Result | Observed evidence |
|---|---|---|---|---|---|---|
| Q1 | Core | {state} | {steps} | {observable outcome} | Not run | {pending} |

Results: Pass / Fail / Blocked / Not run / N/A. Give a reason for the last three.
Label evidence as runtime observation, automated check, or inspection only.

## Findings

### {ID}: {severity — concrete symptom}

- Scenario and impact: {who is affected and how}
- Reproduce: {starting state, exact actions/commands, inputs, fault setup}
- Expected: {contract}; actual: {observation}
- Evidence: {relative links}; frequency: {occurrences/attempts}
- Status: {confirmed/intermittent}; suspected cause: {optional, explicitly a hypothesis}
- Repair/retest: {if authorized, change and evidence; preserve original failure}

## Coverage and conclusion

- {Counts by result, unresolved findings, and what the evidence supports}
- {Blocked/untested cases, prerequisites, excluded surfaces, mock limitations}
- {Cleanup completed; any remaining session-owned state}
