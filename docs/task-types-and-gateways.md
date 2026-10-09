# Task types and gateways — justification

The rubric asks for a deliberate choice of task types and of exclusive, parallel, inclusive, and event-based gateways. This note is the spoken justification if you are asked in a viva.

## Task types

| Type | When we used it | Why this type, not another |
| --- | --- | --- |
| **User task** | Submit proposal, coordinator screen, committee/HoD decision, late-submission approval, claims handling, delivery handover | A named person must look at a work item in Camunda Tasklist and complete it. |
| **Manual task** | Pickup collect-and-scan | Work happens in the physical world. The engine is only told that it was done; the driver is not sitting in Tasklist. |
| **Service task** | Form validation, similarity check, allocate slot, schedule pickup, close shipment, retry mail | Automated call to the department / courier system. No human form. |
| **Send task** | Notify team, send allocation request, pickup confirmation, uninsured-damage notice | One-way message. The process does not wait for a reply on that flow. |
| **Receive / message catch** | Guide accepts, guide declines, delay event, cancellation, withdrawal | The process **waits** for an external message. That is the opposite of a send task. |
| **Business-rule task** | Guide matching (domain + load); booking rate/address/SLA | Decision table / DMN-style policy, not a long-running human review and not a generic script. |
| **Script task** | Not used as a happy-path step | Calculation is already covered by business-rule and service tasks. Scripts would hide policy in code. |

## Gateways

| Gateway | Assignment 1 | Assignment 2 | Why |
| --- | --- | --- | --- |
| **Exclusive (XOR)** | Valid / invalid team / incomplete form; committee approve–revise–reject; guide available; late submission allowed | Booking valid; pickup ok; delivery outcome; insured?; parcel found? | Exactly **one** path. Decisions are mutually exclusive. |
| **Parallel (AND)** | Similarity check **and** clearance rules; notify team **and** write the register | Physical hub movement **and** shipper notification | Both branches **always** run, then join. No business choice. |
| **Inclusive (OR)** | Ethics form and/or lab booking and/or skip | Customs documents and/or customs hold and/or skip (domestic) | One, both, or neither may apply. XOR would force a single choice; AND would force unused work. |
| **Event-based** | Wait for guide accept **or** decline **or** 5-day silence | After a delay signal, wait for delay message **or** ETA timer | The process does not choose the path. The **first event that arrives** does. A user task after this gateway would be invalid BPMN. |

## Boundary events and other exception constructs

| Construct | Role |
| --- | --- |
| **Interrupting timer** | Deadline on proposal submit; overdue committee review; 48-hour missing scan; 5-day customs docs; 7-day depot hold |
| **Non-interrupting timer** | SLA reminder while the committee is still working |
| **Error boundary** | Mail/DB failure; damaged scan; scanner mismatch |
| **Message boundary** | Withdrawal after a guide slot is reserved; shipper cancels in transit |
| **Escalation** | Pickup exception to dispatcher; delayed review to HoD |
| **Compensation** | Release the reserved guide slot; stop line-haul and refund minus fee |
| **Loop with a hard limit** | 2 validation retries; 2 revision cycles; 3 guide allocation tries; 2 pickups; 3 delivery attempts |
| **Error / named end events** | Invalid team, rejected, lapsed, withdrawn, cancelled, RTS, lost, delivered |

These limits stop infinite loops, which is a common BPMN modelling mistake.
