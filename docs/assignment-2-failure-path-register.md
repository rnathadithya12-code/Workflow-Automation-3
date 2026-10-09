# Failure Path Register — Assignment 2

**Process:** Logistics and Shipment Exception Management  
**Model:** `bpmn/assignment-2-logistics-shipment.bpmn`  
**Start:** Shipper books a shipment  
**Happy end:** Shipment delivered  
**Other ends:** Booking cancelled, returned to sender, lost, claim closed, cancelled after dispatch

| ID | Failure point | Cause / trigger | Solution in the model | BPMN construct |
| --- | --- | --- | --- | --- |
| LOG-01 | Booking data | Incomplete address, illegal weight, unknown service level | Business-rule validation fails. Shipper corrects the data and the booking is retried. | Business-rule task + exclusive gateway + loop to booking |
| LOG-02 | Pickup | Shipper absent or parcel not ready | Escalation from the pickup task. Dispatcher reschedules, maximum **2** attempts, then cancels the booking and charges a fee. | Escalation boundary + exclusive retry gateway + cancel end |
| LOG-03 | Address at the door | Address is wrong when the agent arrives | Agent contacts the recipient. If a change is agreed, delivery is retried (surcharge can be applied in the same decision). If not, return to sender. | User task + exclusive gateway |
| LOG-04 | Damage | Damage seen at hub scan or at delivery | Inspection task, then exclusive: insured → claims sub-flow (refund / replace / reship); not insured → record and inform the shipper. | Error boundary on hub sort + exclusive gateway + claims user task |
| LOG-05 | Lost parcel | No scan for 48 hours | Timer starts a trace. If the parcel is not found within 5 days, declare lost, pay compensation, notify, and end *Lost*. If found, resume hub movement. | Interrupting timer boundary + exclusive gateway |
| LOG-06 | Delay in transit | Weather, strike, breakdown, hub overload | Non-interrupting delay message on hub movement. Event-based gateway then waits for a delay message or an ETA timer, notifies the customer, and reroutes. Happy-path delivery is not blocked unless a delay actually occurs. | Non-interrupting message boundary + event-based gateway |
| LOG-07 | Customs | Missing or wrong export/import papers | Inclusive gateway starts document collection and/or a customs-hold task. If documents never arrive (5-day timer), return to origin. | Inclusive gateway + timer boundary on document task |
| LOG-08 | Recipient not home | Nobody at the delivery address | Up to **3** delivery attempts. Then hold at depot for 7 days; if still unclaimed, return to sender. | Exclusive gateway with counter + timer catch |
| LOG-09 | Refusal / COD failure | Recipient refuses the parcel or cash-on-delivery fails | Exclusive gateway on delivery outcome starts return-to-sender and charge adjustment. | Exclusive gateway → RTS service task |
| LOG-10 | Scan / tracking failure | Scanner offline or scan data does not match | Non-interrupting error on hub sort. Supervisor enters the scan by hand; a reconciliation/retry write follows, then the parallel join continues. | Non-interrupting error boundary + user + service task |
| LOG-11 | Cancel after dispatch | Shipper cancels while the parcel is already moving | Interrupting message on hub movement. Compensation stops the line-haul, returns the parcel, and refunds minus a fee. | Message boundary + compensation throw |
| LOG-12 | Tracking vs movement | Physical hub work and customer notification must not wait on each other | After a successful pickup, movement and “picked up” notification run in **parallel** and join before last-mile. | Parallel split/join |

## Happy path (trace)

1. Start — shipper books  
2. User task — create shipment booking  
3. Business-rule task — validate address, weight, SLA, rate → **Valid**  
4. Service task — schedule pickup and assign agent  
5. Manual task — collect parcel and first scan → **Collected**  
6. Parallel split — notify shipper **and** hub sort / line-haul  
7. Parallel join  
8. Inclusive gateway — skip customs when the shipment is domestic  
9. Send task — out for delivery, notify recipient  
10. User task — handover + proof of delivery → **Delivered**  
11. Service task — close shipment and invoice  
12. End — shipment delivered  
