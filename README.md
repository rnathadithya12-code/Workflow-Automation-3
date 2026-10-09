# BPMN Camunda Assignments

Camunda BPMN 2.0 models for **two** of the three given topics:

1. **Student Project Approval and Allocation System**
2. **Logistics and Shipment Exception Management**

Open the `.bpmn` files in [Camunda Modeler](https://camunda.com/download/modeler/). They target **Camunda Platform 7** (executable BPMN 2.0).

## Repository layout

| Path | What it is |
| --- | --- |
| `bpmn/assignment-1-student-project-approval.bpmn` | Process model with lanes, happy path, and exception handling |
| `bpmn/assignment-2-logistics-shipment.bpmn` | Shipment life cycle with exception handling |
| `docs/assignment-1-failure-path-register.md` | Failure Path Register for Assignment 1 |
| `docs/assignment-2-failure-path-register.md` | Failure Path Register for Assignment 2 |
| `docs/task-types-and-gateways.md` | Why each task type and gateway was chosen |

## How to open the diagrams

1. Install Camunda Modeler.
2. File → Open → select a file under `bpmn/`.
3. Use the canvas zoom and the map in the lower-right corner. The diagrams are wide because failure paths sit beside the happy path instead of hiding in collapsed boxes.
4. Click a task to see its type (user, service, send, receive/message catch, business-rule, manual).
5. Click a boundary event on the border of a task to see timers, errors, messages, and escalations.

## Happy path (short)

**Assignment 1.** Team submits a proposal → system validates it → coordinator screens it → duplicate-topic check runs in parallel with ethics/lab clearance → committee approves → a faculty guide is matched and accepts → team is notified and the allocation is stored.

**Assignment 2.** Shipper books a parcel → rates and address are validated → pickup is scheduled and completed → tracking notification and hub movement run together → last-mile delivery with proof of delivery → shipment is closed and invoiced.

Every other path is an exception. Those are listed in the Failure Path Registers and drawn in the same diagrams.


