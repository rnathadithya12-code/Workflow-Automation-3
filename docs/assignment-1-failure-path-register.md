# Failure Path Register — Assignment 1

**Process:** Student Project Approval and Allocation  
**Model:** `bpmn/assignment-1-student-project-approval.bpmn`  
**Start:** Student team decides to submit a proposal  
**Happy end:** Guide allocated and confirmed  
**Other ends:** Invalid team, proposal rejected, proposal lapsed, case withdrawn

| ID | Failure point | Cause / trigger | Solution in the model | BPMN construct |
| --- | --- | --- | --- | --- |
| SPA-01 | Proposal form | Missing abstract, empty fields, invalid roll numbers | After the validation service task an exclusive gateway returns the form. The student corrects it. After **2** failed attempts the case is escalated to the coordinator instead of looping forever. | Exclusive gateway + loop counter + user task (escalate) |
| SPA-02 | Team composition | Team too large, or a student already listed on another team | Treat as a business-rule failure, notify the team, and close the case. The team must reform and start again. | Exclusive gateway → send task → error end event *Invalid team* |
| SPA-03 | Duplicate / similar topic | Similarity score above the department threshold | Coordinator reviews the match. Either send the team back to change the topic, or reject and record the decision. | Service task (similarity) → exclusive gateway → user task |
| SPA-04 | Submission deadline | Team does not submit before the published date | Interrupting timer on *Submit project proposal*. The team is flagged. Coordinator decides whether a late case is admitted. If not, the proposal lapses. | Interrupting timer boundary event |
| SPA-05 | Committee asks for revision | Scope too wide, weak novelty, unclear objectives | Revision loop. Student revises within 7 days. Maximum **2** cycles; after that the committee must approve or reject (no third rewrite). | Exclusive gateway + user task loop with limit |
| SPA-06 | Committee rejects | Not feasible, out of syllabus, or resources missing | Reasons are sent to the team. **One** new topic is allowed; otherwise the process ends as rejected. | Send task + exclusive gateway + end event *Rejected* |
| SPA-07 | Review delayed | Committee does not decide inside the SLA | Non-interrupting timer sends a reminder. A second, interrupting timer escalates to the HoD, who takes over the decision. | Non-interrupting timer + interrupting timer + escalation throw + HoD user task |
| SPA-08 | No faculty guide | Domain mismatch or all matching guides at max load | Business-rule task returns “none”. Coordinator allocates manually, adds a co-guide / external guide, or wait-lists the team. | Business-rule task + exclusive gateway + user task |
| SPA-09 | Guide declines or stays silent | Workload, conflict of interest, or no reply in 5 days | Event-based gateway waits for accept, decline, or timeout. That guide is excluded and allocation is retried. After **3** tries the coordinator allocates by hand. | Event-based gateway + message/timer catch + retry limit |
| SPA-10 | Notification or record write fails | Mail gateway down or database error | Error boundary on notify; retry service (max 3). If retries fail, coordinator notifies the team manually so the case can still complete. | Error boundary events + retry + fallback user task |
| SPA-11 | Withdrawal after a slot is reserved | Team dissolves, or guide goes on long leave | Message boundary on allocate. Compensation releases the reserved slot. Coordinator either re-runs allocation or closes the case. | Message boundary + compensation throw + exclusive gateway |
| SPA-12 | Extra clearance needed | Ethics approval and/or lab booking required (one, both, or neither) | Inclusive gateway starts only the clearances that apply, then joins before committee review. | Inclusive split/join |
| SPA-13 | Screening bottleneck | Coordinator screen and system checks would delay the case if done strictly in series | After screening, similarity check and clearance rules run in **parallel**, then join. | Parallel split/join |

## Happy path (trace)

1. Start — team decides to submit  
2. User task — submit project proposal  
3. Service task — validate form and team rules → **Valid**  
4. User task — coordinator screens the proposal  
5. Parallel split — duplicate-topic check **and** clearance rules  
6. Inclusive gateway — skip extra forms when none are required  
7. Parallel join — checks complete → similarity below threshold  
8. User task — committee evaluates → **Approved**  
9. Business-rule task — match guide by domain and load → guide found  
10. Service + send — reserve slot and request acceptance  
11. Event-based wait — guide **accepts**  
12. Parallel split — notify team **and** write the register  
13. End — guide allocated and confirmed  
