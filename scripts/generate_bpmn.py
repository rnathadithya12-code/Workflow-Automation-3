"""Generate Camunda-compatible BPMN 2.0 files for the two assignment models."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parents[1]
BPMN_DIR = ROOT / "bpmn"


@dataclass
class Node:
    id: str
    name: str
    kind: str
    lane: str
    x: int
    y: int
    w: int = 100
    h: int = 80
    extra: dict = field(default_factory=dict)


@dataclass
class Flow:
    id: str
    source: str
    target: str
    name: str = ""
    extra: str = ""


def task_xml(n: Node) -> str:
    name = escape(n.name)
    incoming = n.extra.get("incoming", [])
    outgoing = n.extra.get("outgoing", [])
    io = "".join(f'<bpmn:incoming>{i}</bpmn:incoming>' for i in incoming)
    io += "".join(f'<bpmn:outgoing>{o}</bpmn:outgoing>' for o in outgoing)

    if n.kind == "start":
        return f'<bpmn:startEvent id="{n.id}" name="{name}">{io}</bpmn:startEvent>'
    if n.kind == "end":
        return f'<bpmn:endEvent id="{n.id}" name="{name}">{io}</bpmn:endEvent>'
    if n.kind == "error-end":
        return (
            f'<bpmn:endEvent id="{n.id}" name="{name}">{io}'
            f'<bpmn:errorEventDefinition id="{n.id}_err"/></bpmn:endEvent>'
        )
    if n.kind == "terminate-end":
        return (
            f'<bpmn:endEvent id="{n.id}" name="{name}">{io}'
            f'<bpmn:terminateEventDefinition id="{n.id}_term"/></bpmn:endEvent>'
        )
    if n.kind == "user":
        return f'<bpmn:userTask id="{n.id}" name="{name}">{io}</bpmn:userTask>'
    if n.kind == "service":
        return f'<bpmn:serviceTask id="{n.id}" name="{name}">{io}</bpmn:serviceTask>'
    if n.kind == "send":
        return f'<bpmn:sendTask id="{n.id}" name="{name}">{io}</bpmn:sendTask>'
    if n.kind == "receive":
        return f'<bpmn:receiveTask id="{n.id}" name="{name}">{io}</bpmn:receiveTask>'
    if n.kind == "manual":
        return f'<bpmn:manualTask id="{n.id}" name="{name}">{io}</bpmn:manualTask>'
    if n.kind == "business-rule":
        return f'<bpmn:businessRuleTask id="{n.id}" name="{name}">{io}</bpmn:businessRuleTask>'
    if n.kind == "script":
        return f'<bpmn:scriptTask id="{n.id}" name="{name}">{io}</bpmn:scriptTask>'
    if n.kind == "xor":
        return f'<bpmn:exclusiveGateway id="{n.id}" name="{name}" default="{n.extra.get("default","")}">{io}</bpmn:exclusiveGateway>'.replace(
            ' default=""', ""
        )
    if n.kind == "and":
        return f'<bpmn:parallelGateway id="{n.id}" name="{name}">{io}</bpmn:parallelGateway>'
    if n.kind == "or":
        return f'<bpmn:inclusiveGateway id="{n.id}" name="{name}">{io}</bpmn:inclusiveGateway>'
    if n.kind == "event-gw":
        return f'<bpmn:eventBasedGateway id="{n.id}" name="{name}">{io}</bpmn:eventBasedGateway>'
    if n.kind == "timer-catch":
        return (
            f'<bpmn:intermediateCatchEvent id="{n.id}" name="{name}">{io}'
            f'<bpmn:timerEventDefinition id="{n.id}_timer">'
            f'<bpmn:timeDuration xsi:type="tFormalExpression">{n.extra.get("duration","PT24H")}</bpmn:timeDuration>'
            f"</bpmn:timerEventDefinition></bpmn:intermediateCatchEvent>"
        )
    if n.kind == "message-catch":
        return (
            f'<bpmn:intermediateCatchEvent id="{n.id}" name="{name}">{io}'
            f'<bpmn:messageEventDefinition id="{n.id}_msg" messageRef="{n.extra.get("message","Message_1")}"/>'
            f"</bpmn:intermediateCatchEvent>"
        )
    if n.kind == "escalation-throw":
        return (
            f'<bpmn:intermediateThrowEvent id="{n.id}" name="{name}">{io}'
            f'<bpmn:escalationEventDefinition id="{n.id}_esc"/>'
            f"</bpmn:intermediateThrowEvent>"
        )
    if n.kind == "compensate-throw":
        return (
            f'<bpmn:intermediateThrowEvent id="{n.id}" name="{name}">{io}'
            f'<bpmn:compensateEventDefinition id="{n.id}_comp" waitForCompletion="true"/>'
            f"</bpmn:intermediateThrowEvent>"
        )
    raise ValueError(n.kind)


def boundary_xml(b: dict, incoming: list[str], outgoing: list[str]) -> str:
    io = "".join(f"<bpmn:incoming>{i}</bpmn:incoming>" for i in incoming)
    io += "".join(f"<bpmn:outgoing>{o}</bpmn:outgoing>" for o in outgoing)
    cancel = str(b.get("cancel", True)).lower()
    inner = ""
    if b["kind"] == "timer":
        inner = (
            f'<bpmn:timerEventDefinition id="{b["id"]}_timer">'
            f'<bpmn:timeDuration xsi:type="tFormalExpression">{b.get("duration","P7D")}</bpmn:timeDuration>'
            f"</bpmn:timerEventDefinition>"
        )
    elif b["kind"] == "error":
        inner = f'<bpmn:errorEventDefinition id="{b["id"]}_err"/>'
    elif b["kind"] == "message":
        inner = f'<bpmn:messageEventDefinition id="{b["id"]}_msg" messageRef="{b.get("message","Message_Withdraw")}"/>'
    elif b["kind"] == "escalation":
        inner = f'<bpmn:escalationEventDefinition id="{b["id"]}_esc"/>'
    return (
        f'<bpmn:boundaryEvent id="{b["id"]}" name="{escape(b["name"])}" '
        f'attachedToRef="{b["attached"]}" cancelActivity="{cancel}">{io}{inner}</bpmn:boundaryEvent>'
    )


def shape(n: Node) -> str:
    if n.kind in {"xor", "and", "or", "event-gw"}:
        w, h = 50, 50
        x, y = n.x + 25, n.y + 15
    elif n.kind in {"start", "end", "error-end", "terminate-end", "timer-catch", "message-catch", "escalation-throw", "compensate-throw"}:
        w, h = 36, 36
        x, y = n.x + 32, n.y + 22
    else:
        w, h, x, y = n.w, n.h, n.x, n.y
    return (
        f'<bpmndi:BPMNShape id="{n.id}_di" bpmnElement="{n.id}">'
        f'<dc:Bounds x="{x}" y="{y}" width="{w}" height="{h}" />'
        f'<bpmndi:BPMNLabel />'
        f"</bpmndi:BPMNShape>"
    )


def edge(flow: Flow, nodes: dict[str, Node], extra_y: int = 0) -> str:
    s, t = nodes[flow.source], nodes[flow.target]
    sx, sy = s.x + s.w // 2, s.y + s.h // 2 + extra_y
    tx, ty = t.x + t.w // 2, t.y + t.h // 2 + extra_y
    return (
        f'<bpmndi:BPMNEdge id="{flow.id}_di" bpmnElement="{flow.id}">'
        f'<di:waypoint x="{sx}" y="{sy}" />'
        f'<di:waypoint x="{tx}" y="{ty}" />'
        f"</bpmndi:BPMNEdge>"
    )


def wrap(process_id: str, name: str, participant_id: str, lanes: list[tuple[str, str, int, int]],
         nodes: list[Node], flows: list[Flow], boundaries: list[dict], messages: list[tuple[str, str]],
         pool_w: int, pool_h: int) -> str:
    by_id = {n.id: n for n in nodes}
    in_map: dict[str, list[str]] = {n.id: [] for n in nodes}
    out_map: dict[str, list[str]] = {n.id: [] for n in nodes}
    b_in: dict[str, list[str]] = {b["id"]: [] for b in boundaries}
    b_out: dict[str, list[str]] = {b["id"]: [] for b in boundaries}

    for f in flows:
        if f.source in out_map:
            out_map[f.source].append(f.id)
        elif f.source in b_out:
            b_out[f.source].append(f.id)
        if f.target in in_map:
            in_map[f.target].append(f.id)
        elif f.target in b_in:
            b_in[f.target].append(f.id)

    for n in nodes:
        n.extra["incoming"] = in_map[n.id]
        n.extra["outgoing"] = out_map[n.id]

    lane_xml = []
    for lid, lname, _, _ in lanes:
        refs = "".join(
            f"<bpmn:flowNodeRef>{n.id}</bpmn:flowNodeRef>"
            for n in nodes
            if n.lane == lid
        )
        # also attach boundaries to same lane as host conceptually via flowNodeRef
        for b in boundaries:
            host = by_id[b["attached"]]
            if host.lane == lid:
                refs += f'<bpmn:flowNodeRef>{b["id"]}</bpmn:flowNodeRef>'
        lane_xml.append(
            f'<bpmn:lane id="{lid}" name="{escape(lname)}">{refs}</bpmn:lane>'
        )

    node_xml = "\n      ".join(task_xml(n) for n in nodes)
    flow_xml = "\n      ".join(
        f'<bpmn:sequenceFlow id="{f.id}" sourceRef="{f.source}" targetRef="{f.target}"'
        + (f' name="{escape(f.name)}"' if f.name else "")
        + (f' {f.extra}' if f.extra else "")
        + " />"
        for f in flows
    )
    bound_xml = "\n      ".join(boundary_xml(b, b_in[b["id"]], b_out[b["id"]]) for b in boundaries)
    msg_xml = "\n    ".join(
        f'<bpmn:message id="{mid}" name="{escape(mname)}" />' for mid, mname in messages
    )

    lane_shapes = []
    for lid, _, ly, lh in lanes:
        lane_shapes.append(
            f'<bpmndi:BPMNShape id="{lid}_di" bpmnElement="{lid}" isHorizontal="true">'
            f'<dc:Bounds x="170" y="{ly}" width="{pool_w - 20}" height="{lh}" />'
            f"</bpmndi:BPMNShape>"
        )

    node_shapes = [shape(n) for n in nodes]
    bound_shapes = []
    for b in boundaries:
        host = by_id[b["attached"]]
        bx, by = host.x + host.w - 18, host.y + host.h - 18
        bound_shapes.append(
            f'<bpmndi:BPMNShape id="{b["id"]}_di" bpmnElement="{b["id"]}">'
            f'<dc:Bounds x="{bx}" y="{by}" width="36" height="36" />'
            f"</bpmndi:BPMNShape>"
        )
    # include boundary nodes in edge lookup
    for b in boundaries:
        by_id[b["id"]] = Node(b["id"], b["name"], "start", "", b["attached"] and by_id[b["attached"]].x + 80, by_id[b["attached"]].y + 70, 36, 36)
        host = {n.id: n for n in nodes}[b["attached"]]
        by_id[b["id"]].x = host.x + host.w - 18
        by_id[b["id"]].y = host.y + host.h - 18
        by_id[b["id"]].w = 36
        by_id[b["id"]].h = 36

    edges = [edge(f, by_id) for f in flows]

    return f'''<?xml version="1.0" encoding="UTF-8"?>
<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"
                  xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI"
                  xmlns:dc="http://www.omg.org/spec/DD/20100524/DC"
                  xmlns:di="http://www.omg.org/spec/DD/20100524/DI"
                  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                  xmlns:camunda="http://camunda.org/schema/1.0/bpmn"
                  xmlns:modeler="http://camunda.org/schema/modeler/1.0"
                  id="Definitions_{process_id}"
                  targetNamespace="http://bpmn.io/schema/bpmn"
                  exporter="Camunda Modeler"
                  exporterVersion="5.23.0"
                  modeler:executionPlatform="Camunda Platform"
                  modeler:executionPlatformVersion="7.21.0">
    {msg_xml}
    <bpmn:collaboration id="Collaboration_{process_id}">
      <bpmn:participant id="{participant_id}" name="{escape(name)}" processRef="{process_id}" />
    </bpmn:collaboration>
    <bpmn:process id="{process_id}" name="{escape(name)}" isExecutable="true">
      <bpmn:laneSet id="LaneSet_{process_id}">
        {''.join(lane_xml)}
      </bpmn:laneSet>
      {node_xml}
      {bound_xml}
      {flow_xml}
    </bpmn:process>
    <bpmndi:BPMNDiagram id="BPMNDiagram_{process_id}">
      <bpmndi:BPMNPlane id="BPMNPlane_{process_id}" bpmnElement="Collaboration_{process_id}">
        <bpmndi:BPMNShape id="{participant_id}_di" bpmnElement="{participant_id}" isHorizontal="true">
          <dc:Bounds x="150" y="{lanes[0][2] - 20}" width="{pool_w}" height="{pool_h}" />
        </bpmndi:BPMNShape>
        {''.join(lane_shapes)}
        {''.join(node_shapes)}
        {''.join(bound_shapes)}
        {''.join(edges)}
      </bpmndi:BPMNPlane>
    </bpmndi:BPMNDiagram>
</bpmn:definitions>
'''


def mid_y(lane_top: int, lane_h: int = 140) -> int:
    return lane_top + (lane_h - 80) // 2


def assignment_1() -> str:
    # lane tops
    st, coord, comm, guide, sys_ = 100, 240, 380, 520, 660
    lanes = [
        ("Lane_Student", "Student / Team", st, 140),
        ("Lane_Coordinator", "Project Coordinator", coord, 140),
        ("Lane_Committee", "Review Committee (incl. HoD)", comm, 140),
        ("Lane_Guide", "Faculty Guide", guide, 140),
        ("Lane_System", "Project Management System", sys_, 140),
    ]
    ys = {
        "Lane_Student": mid_y(st),
        "Lane_Coordinator": mid_y(coord),
        "Lane_Committee": mid_y(comm),
        "Lane_Guide": mid_y(guide),
        "Lane_System": mid_y(sys_),
    }

    def N(i, name, kind, lane, x):
        return Node(i, name, kind, lane, x, ys[lane])

    nodes = [
        N("Start_1", "Team decides to submit", "start", "Lane_Student", 200),
        N("UT_Submit", "Submit project proposal", "user", "Lane_Student", 310),
        N("ST_Validate", "Validate form and team rules", "service", "Lane_System", 470),
        N("XOR_Valid", "Validation result", "xor", "Lane_System", 620),
        N("ST_NotifyInvalid", "Notify invalid team", "send", "Lane_System", 620),
        N("End_InvalidTeam", "Invalid team", "error-end", "Lane_Student", 780),
        N("XOR_Retry", "Resubmit attempts left?", "xor", "Lane_System", 780),
        N("UT_EscalateVal", "Escalate incomplete proposal", "user", "Lane_Coordinator", 940),
        N("UT_Screen", "Screen proposal", "user", "Lane_Coordinator", 940),
        N("AND_SplitChecks", "Run checks in parallel", "and", "Lane_System", 1100),
        N("ST_Similarity", "Run duplicate-topic check", "service", "Lane_System", 1240),
        N("BR_EthicsLab", "Need ethics and/or lab clearance?", "business-rule", "Lane_System", 1240),
        N("OR_SplitClearance", "Additional clearances", "or", "Lane_System", 1400),
        N("UT_Ethics", "Complete ethics form", "user", "Lane_Student", 1540),
        N("UT_Lab", "Request lab / resource booking", "user", "Lane_Coordinator", 1540),
        N("OR_JoinClearance", "Clearances complete", "or", "Lane_System", 1700),
        N("AND_JoinChecks", "Checks complete", "and", "Lane_System", 1840),
        N("XOR_Dup", "Similarity above threshold?", "xor", "Lane_System", 1980),
        N("UT_ReviewMatch", "Review suspected duplicate", "user", "Lane_Coordinator", 2120),
        N("XOR_MatchDec", "Duplicate decision", "xor", "Lane_Coordinator", 2280),
        N("UT_Committee", "Evaluate proposal", "user", "Lane_Committee", 2120),
        N("ST_RemindCommittee", "Send SLA reminder", "send", "Lane_System", 2280),
        N("TH_EscalateHod", "Escalate delayed review to HoD", "escalation-throw", "Lane_Committee", 2440),
        N("UT_HodDecide", "HoD takes over decision", "user", "Lane_Committee", 2580),
        N("XOR_Committee", "Committee outcome", "xor", "Lane_Committee", 2440),
        N("XOR_RevLimit", "Revision cycles left?", "xor", "Lane_Committee", 2580),
        N("UT_Revise", "Revise proposal (7 days)", "user", "Lane_Student", 2740),
        N("ST_RejectReasons", "Send rejection reasons", "send", "Lane_System", 2580),
        N("XOR_NewTopic", "Allow one new topic?", "xor", "Lane_Student", 2740),
        N("End_Rejected", "Proposal rejected", "end", "Lane_Student", 2900),
        N("BR_GuideAvail", "Match guide by domain and load", "business-rule", "Lane_System", 2580),
        N("XOR_GuideAvail", "Guide available?", "xor", "Lane_System", 2740),
        N("UT_ManualGuide", "Allocate manually / wait-list", "user", "Lane_Coordinator", 2900),
        N("ST_Allocate", "Reserve guide slot", "service", "Lane_System", 2900),
        N("ST_SendAlloc", "Send allocation request", "send", "Lane_System", 3060),
        N("EG_GuideWait", "Wait for guide response", "event-gw", "Lane_Guide", 3220),
        N("MSG_Accept", "Guide accepts", "message-catch", "Lane_Guide", 3380),
        N("TMR_Silent", "No response (5 days)", "timer-catch", "Lane_Guide", 3380),
        N("MSG_Decline", "Guide declines", "message-catch", "Lane_Guide", 3380),
        N("XOR_GuideOk", "Accepted?", "xor", "Lane_Guide", 3540),
        N("XOR_AllocTries", "Allocation attempts left?", "xor", "Lane_Coordinator", 3700),
        N("AND_NotifySplit", "Confirm allocation", "and", "Lane_System", 3860),
        N("ST_NotifyTeam", "Notify student team", "send", "Lane_System", 4020),
        N("ST_RecordAlloc", "Record allocation in register", "service", "Lane_System", 4020),
        N("AND_NotifyJoin", "Notifications done", "and", "Lane_System", 4180),
        N("End_Allocated", "Guide allocated and confirmed", "end", "Lane_Student", 4340),
        N("ST_LateFlag", "Flag late submission", "service", "Lane_System", 470),
        N("UT_LateApprove", "Approve or refuse late submission", "user", "Lane_Coordinator", 620),
        N("XOR_Late", "Late submission allowed?", "xor", "Lane_Coordinator", 780),
        N("End_Lapsed", "Proposal lapsed", "end", "Lane_Student", 940),
        N("ST_RetryMail", "Retry notification (max 3)", "service", "Lane_System", 4180),
        N("UT_ManualNotify", "Notify team manually", "user", "Lane_Coordinator", 4340),
        N("TH_Compensate", "Release reserved guide slot", "compensate-throw", "Lane_System", 3700),
        N("ST_ReleaseSlot", "Compensation: free guide slot", "service", "Lane_System", 3860),
        N("XOR_AfterWithdraw", "Re-allocate or close?", "xor", "Lane_Coordinator", 4020),
        N("End_Withdrawn", "Case withdrawn", "end", "Lane_Student", 4180),
        N("UT_FixValidation", "Correct form errors", "user", "Lane_Student", 780),
    ]

    # fix overlapping y for same-lane same-x by nudging selected nodes
    nudge = {
        "ST_NotifyInvalid": ("Lane_System", 470, ys["Lane_System"] + 0),  # will reposition below
        "BR_EthicsLab": 40,
    }
    # Place exception / alternate nodes with distinct coordinates
    pos = {
        "ST_NotifyInvalid": (470, ys["Lane_System"]),  # overwrite later
    }
    # Re-layout critical overlapping nodes
    coords = {
        "Start_1": (200, ys["Lane_Student"]),
        "UT_Submit": (320, ys["Lane_Student"]),
        "ST_Validate": (480, ys["Lane_System"]),
        "XOR_Valid": (640, ys["Lane_System"]),
        "UT_FixValidation": (640, ys["Lane_Student"]),
        "XOR_Retry": (800, ys["Lane_System"]),
        "UT_EscalateVal": (960, ys["Lane_Coordinator"]),
        "ST_NotifyInvalid": (800, ys["Lane_Student"] - 0),
        "End_InvalidTeam": (960, ys["Lane_Student"]),
        "UT_Screen": (960, ys["Lane_Coordinator"]),
        "AND_SplitChecks": (1120, ys["Lane_System"]),
        "ST_Similarity": (1280, ys["Lane_System"]),
        "OR_SplitClearance": (1280, ys["Lane_Coordinator"]),
        "UT_Ethics": (1440, ys["Lane_Student"]),
        "UT_Lab": (1440, ys["Lane_Coordinator"]),
        "OR_JoinClearance": (1600, ys["Lane_Coordinator"]),
        "AND_JoinChecks": (1760, ys["Lane_System"]),
        "XOR_Dup": (1920, ys["Lane_System"]),
        "UT_ReviewMatch": (2080, ys["Lane_Coordinator"]),
        "XOR_MatchDec": (2240, ys["Lane_Coordinator"]),
        "UT_Committee": (2080, ys["Lane_Committee"]),
        "ST_RemindCommittee": (2240, ys["Lane_System"]),
        "TH_EscalateHod": (2400, ys["Lane_Committee"] - 0),
        "UT_HodDecide": (2560, ys["Lane_Committee"]),
        "XOR_Committee": (2240, ys["Lane_Committee"]),
        "XOR_RevLimit": (2400, ys["Lane_Committee"]),
        "UT_Revise": (2560, ys["Lane_Student"]),
        "ST_RejectReasons": (2400, ys["Lane_System"]),
        "XOR_NewTopic": (2560, ys["Lane_Student"]),
        "End_Rejected": (2720, ys["Lane_Student"]),
        "BR_GuideAvail": (2400, ys["Lane_System"]),
        "XOR_GuideAvail": (2560, ys["Lane_System"]),
        "UT_ManualGuide": (2720, ys["Lane_Coordinator"]),
        "ST_Allocate": (2720, ys["Lane_System"]),
        "ST_SendAlloc": (2880, ys["Lane_System"]),
        "EG_GuideWait": (3040, ys["Lane_Guide"]),
        "MSG_Accept": (3200, ys["Lane_Guide"]),
        "TMR_Silent": (3200, ys["Lane_Guide"] + 0),
        "UT_Decline": (3200, ys["Lane_Coordinator"]),
        "XOR_GuideOk": (3360, ys["Lane_Guide"]),
        "XOR_AllocTries": (3520, ys["Lane_Coordinator"]),
        "AND_NotifySplit": (3680, ys["Lane_System"]),
        "ST_NotifyTeam": (3840, ys["Lane_System"]),
        "ST_RecordAlloc": (3840, ys["Lane_Coordinator"]),
        "AND_NotifyJoin": (4000, ys["Lane_System"]),
        "End_Allocated": (4160, ys["Lane_Student"]),
        "ST_LateFlag": (320, ys["Lane_System"]),
        "UT_LateApprove": (480, ys["Lane_Coordinator"]),
        "XOR_Late": (640, ys["Lane_Coordinator"]),
        "End_Lapsed": (800, ys["Lane_Coordinator"]),
        "ST_RetryMail": (4000, ys["Lane_Student"]),
        "UT_ManualNotify": (4160, ys["Lane_Coordinator"]),
        "TH_Compensate": (3520, ys["Lane_System"]),
        "ST_ReleaseSlot": (3680, ys["Lane_Coordinator"]),
        "XOR_AfterWithdraw": (3840, ys["Lane_Guide"]),
        "End_Withdrawn": (4000, ys["Lane_Guide"]),
        "BR_EthicsLab": (1120, ys["Lane_Coordinator"]),
    }
    # resolve remaining overlaps for event-based branches
    coords["TMR_Silent"] = (3200, ys["Lane_Guide"] + 50)
    coords["MSG_Accept"] = (3200, ys["Lane_Guide"] - 10)
    coords["ST_NotifyInvalid"] = (800, ys["Lane_Student"])
    coords["XOR_NewTopic"] = (2560, ys["Lane_Coordinator"])
    coords["End_Rejected"] = (2720, ys["Lane_Coordinator"])
    coords["UT_Revise"] = (2560, ys["Lane_Student"])
    coords["ST_RecordAlloc"] = (3840, ys["Lane_Student"])
    coords["AND_NotifyJoin"] = (4000, ys["Lane_System"])
    coords["ST_RetryMail"] = (4160, ys["Lane_System"])
    coords["UT_ManualNotify"] = (4320, ys["Lane_Coordinator"])
    coords["End_Allocated"] = (4480, ys["Lane_Student"])
    coords["XOR_AfterWithdraw"] = (3840, ys["Lane_Coordinator"])
    coords["End_Withdrawn"] = (4000, ys["Lane_Student"])
    coords["ST_ReleaseSlot"] = (3680, ys["Lane_System"])
    coords["TH_Compensate"] = (3520, ys["Lane_System"])
    coords["TMR_Silent"] = (3200, ys["Lane_Committee"])
    coords["MSG_Decline"] = (3360, ys["Lane_Coordinator"])
    coords["XOR_GuideOk"] = (3520, ys["Lane_Guide"])
    coords["XOR_AllocTries"] = (3680, ys["Lane_Coordinator"])
    coords["AND_NotifySplit"] = (3840, ys["Lane_System"])
    coords["ST_NotifyTeam"] = (4000, ys["Lane_System"])
    coords["ST_RecordAlloc"] = (4000, ys["Lane_Student"])
    coords["AND_NotifyJoin"] = (4160, ys["Lane_System"])
    coords["End_Allocated"] = (4320, ys["Lane_Student"])
    coords["TH_EscalateHod"] = (2240, ys["Lane_Committee"])  # overlap with XOR_Committee
    coords["XOR_Committee"] = (2400, ys["Lane_Committee"])
    coords["TH_EscalateHod"] = (2080, ys["Lane_System"])
    coords["UT_HodDecide"] = (2240, ys["Lane_Committee"])
    coords["XOR_RevLimit"] = (2560, ys["Lane_Committee"])
    coords["ST_RejectReasons"] = (2560, ys["Lane_System"])
    coords["XOR_NewTopic"] = (2720, ys["Lane_Student"])
    coords["End_Rejected"] = (2880, ys["Lane_Student"])
    coords["BR_GuideAvail"] = (2560, ys["Lane_System"])
    coords["XOR_GuideAvail"] = (2720, ys["Lane_System"])
    coords["ST_Allocate"] = (2880, ys["Lane_System"])
    coords["UT_ManualGuide"] = (2880, ys["Lane_Coordinator"])
    coords["ST_SendAlloc"] = (3040, ys["Lane_System"])
    coords["EG_GuideWait"] = (3200, ys["Lane_Guide"])
    coords["MSG_Accept"] = (3360, ys["Lane_Guide"])
    coords["TMR_Silent"] = (3360, ys["Lane_Committee"])
    coords["MSG_Decline"] = (3360, ys["Lane_Coordinator"])
    coords["XOR_GuideOk"] = (3520, ys["Lane_Guide"])
    coords["ST_LateFlag"] = (200, ys["Lane_System"])
    coords["UT_LateApprove"] = (320, ys["Lane_Coordinator"])
    coords["XOR_Late"] = (480, ys["Lane_Coordinator"])
    coords["End_Lapsed"] = (640, ys["Lane_Coordinator"])
    coords["UT_Screen"] = (960, ys["Lane_Coordinator"])
    coords["UT_EscalateVal"] = (960, ys["Lane_Committee"])
    coords["End_InvalidTeam"] = (960, ys["Lane_Student"])
    coords["ST_NotifyInvalid"] = (800, ys["Lane_Student"])

    for n in nodes:
        if n.id in coords:
            n.x, n.y = coords[n.id]
            n.lane = n.lane  # keep
    # map node lanes from y
    lane_by_y = [
        (st, "Lane_Student"),
        (coord, "Lane_Coordinator"),
        (comm, "Lane_Committee"),
        (guide, "Lane_Guide"),
        (sys_, "Lane_System"),
    ]
    def lane_for_y(y):
        best = min(lane_by_y, key=lambda t: abs(y - (t[0] + 30)))
        # use closest lane top
        return min(lane_by_y, key=lambda t: abs(y - mid_y(t[0])) )[1]
    for n in nodes:
        n.lane = lane_for_y(n.y)

    flows = [
        Flow("f1", "Start_1", "UT_Submit"),
        Flow("f2", "UT_Submit", "ST_Validate"),
        Flow("f3", "ST_Validate", "XOR_Valid"),
        Flow("f4", "XOR_Valid", "ST_NotifyInvalid", "Invalid team rules"),
        Flow("f5", "ST_NotifyInvalid", "End_InvalidTeam"),
        Flow("f6", "XOR_Valid", "XOR_Retry", "Incomplete / invalid data"),
        Flow("f7", "XOR_Retry", "UT_FixValidation", "Attempts remaining"),
        Flow("f8", "UT_FixValidation", "UT_Submit"),
        Flow("f9", "XOR_Retry", "UT_EscalateVal", "2 attempts used"),
        Flow("f10", "UT_EscalateVal", "UT_Screen", "Coordinator admits case"),
        Flow("f11", "XOR_Valid", "UT_Screen", "Valid"),
        Flow("f12", "UT_Screen", "AND_SplitChecks"),
        Flow("f13", "AND_SplitChecks", "ST_Similarity"),
        Flow("f14", "AND_SplitChecks", "BR_EthicsLab"),
        Flow("f15", "BR_EthicsLab", "OR_SplitClearance"),
        Flow("f16", "OR_SplitClearance", "UT_Ethics", "Ethics required"),
        Flow("f17", "OR_SplitClearance", "UT_Lab", "Lab / resource required"),
        Flow("f17b", "OR_SplitClearance", "OR_JoinClearance", "No extra clearance"),
        Flow("f18", "UT_Ethics", "OR_JoinClearance"),
        Flow("f19", "UT_Lab", "OR_JoinClearance"),
        Flow("f20", "OR_JoinClearance", "AND_JoinChecks"),
        Flow("f21", "ST_Similarity", "AND_JoinChecks"),
        Flow("f22", "AND_JoinChecks", "XOR_Dup"),
        Flow("f23", "XOR_Dup", "UT_ReviewMatch", "High similarity"),
        Flow("f24", "XOR_Dup", "UT_Committee", "Unique topic"),
        Flow("f25", "UT_ReviewMatch", "XOR_MatchDec"),
        Flow("f26", "XOR_MatchDec", "UT_Submit", "Modify topic"),
        Flow("f27", "XOR_MatchDec", "ST_RejectReasons", "Confirm duplicate / reject"),
        Flow("f28", "UT_Committee", "XOR_Committee"),
        Flow("f28b", "UT_HodDecide", "XOR_Committee"),
        Flow("f29", "XOR_Committee", "XOR_RevLimit", "Revise"),
        Flow("f30", "XOR_RevLimit", "UT_Revise", "Cycle < 2"),
        Flow("f31", "UT_Revise", "UT_Committee"),
        Flow("f32", "XOR_RevLimit", "XOR_Committee", "Force approve or reject"),
        Flow("f33", "XOR_Committee", "ST_RejectReasons", "Rejected"),
        Flow("f34", "ST_RejectReasons", "XOR_NewTopic"),
        Flow("f35", "XOR_NewTopic", "UT_Submit", "One new topic allowed"),
        Flow("f36", "XOR_NewTopic", "End_Rejected", "No further attempt"),
        Flow("f37", "XOR_Committee", "BR_GuideAvail", "Approved"),
        Flow("f38", "BR_GuideAvail", "XOR_GuideAvail"),
        Flow("f39", "XOR_GuideAvail", "UT_ManualGuide", "No matching guide"),
        Flow("f40", "XOR_GuideAvail", "ST_Allocate", "Guide matched"),
        Flow("f41", "UT_ManualGuide", "ST_Allocate"),
        Flow("f42", "ST_Allocate", "ST_SendAlloc"),
        Flow("f43", "ST_SendAlloc", "EG_GuideWait"),
        Flow("f44", "EG_GuideWait", "MSG_Accept"),
        Flow("f45", "EG_GuideWait", "TMR_Silent"),
        Flow("f46", "EG_GuideWait", "MSG_Decline"),
        Flow("f47", "MSG_Accept", "XOR_GuideOk"),
        Flow("f48", "TMR_Silent", "XOR_GuideOk"),
        Flow("f49", "MSG_Decline", "XOR_GuideOk"),
        Flow("f50", "XOR_GuideOk", "AND_NotifySplit", "Accepted"),
        Flow("f51", "XOR_GuideOk", "XOR_AllocTries", "Declined or silent"),
        Flow("f52", "XOR_AllocTries", "BR_GuideAvail", "Try next guide (< 3)"),
        Flow("f53", "XOR_AllocTries", "UT_ManualGuide", "3 attempts used"),
        Flow("f54", "AND_NotifySplit", "ST_NotifyTeam"),
        Flow("f55", "AND_NotifySplit", "ST_RecordAlloc"),
        Flow("f56", "ST_NotifyTeam", "AND_NotifyJoin"),
        Flow("f57", "ST_RecordAlloc", "AND_NotifyJoin"),
        Flow("f58", "AND_NotifyJoin", "End_Allocated"),
        Flow("f59", "Boundary_Deadline", "ST_LateFlag"),
        Flow("f60", "ST_LateFlag", "UT_LateApprove"),
        Flow("f61", "UT_LateApprove", "XOR_Late"),
        Flow("f62", "XOR_Late", "ST_Validate", "Late allowed"),
        Flow("f63", "XOR_Late", "End_Lapsed", "Deadline enforced"),
        Flow("f64", "Boundary_Remind", "ST_RemindCommittee"),
        Flow("f65", "ST_RemindCommittee", "UT_Committee"),
        Flow("f66", "Boundary_ReviewSLA", "TH_EscalateHod"),
        Flow("f67", "TH_EscalateHod", "UT_HodDecide"),
        Flow("f68", "Boundary_NotifyErr", "ST_RetryMail"),
        Flow("f69", "ST_RetryMail", "AND_NotifyJoin", "Retry succeeded"),
        Flow("f70", "Boundary_NotifyErr2", "UT_ManualNotify"),
        Flow("f71", "UT_ManualNotify", "AND_NotifyJoin"),
        Flow("f72", "Boundary_Withdraw", "TH_Compensate"),
        Flow("f73", "TH_Compensate", "ST_ReleaseSlot"),
        Flow("f74", "ST_ReleaseSlot", "XOR_AfterWithdraw"),
        Flow("f75", "XOR_AfterWithdraw", "BR_GuideAvail", "Re-allocate"),
        Flow("f76", "XOR_AfterWithdraw", "End_Withdrawn", "Close case"),
    ]

    boundaries = [
        {"id": "Boundary_Deadline", "name": "Submission deadline", "kind": "timer", "attached": "UT_Submit", "cancel": True, "duration": "P14D"},
        {"id": "Boundary_Remind", "name": "Review SLA reminder", "kind": "timer", "attached": "UT_Committee", "cancel": False, "duration": "P5D"},
        {"id": "Boundary_ReviewSLA", "name": "Review overdue", "kind": "timer", "attached": "UT_Committee", "cancel": True, "duration": "P10D"},
        {"id": "Boundary_NotifyErr", "name": "Email / DB error", "kind": "error", "attached": "ST_NotifyTeam", "cancel": True},
        {"id": "Boundary_NotifyErr2", "name": "Retries exhausted", "kind": "error", "attached": "ST_RetryMail", "cancel": True},
        {"id": "Boundary_Withdraw", "name": "Team or guide withdraws", "kind": "message", "attached": "ST_Allocate", "cancel": True, "message": "Message_Withdraw"},
    ]

    messages = [
        ("Message_Withdraw", "Withdrawal after approval"),
        ("Message_1", "Guide acceptance"),
        ("Message_Decline", "Guide decline"),
    ]
    # message catch needs Message_1
    for n in nodes:
        if n.id == "MSG_Accept":
            n.extra["message"] = "Message_1"
        if n.id == "MSG_Decline":
            n.extra["message"] = "Message_Decline"
        if n.id == "TMR_Silent":
            n.extra["duration"] = "P5D"

    return wrap(
        "StudentProjectApproval",
        "Student Project Approval and Allocation",
        "Pool_SPA",
        lanes,
        nodes,
        flows,
        boundaries,
        messages,
        pool_w=4500,
        pool_h=740,
    )


def assignment_2() -> str:
    ship, tower, pickup, hub, delivery, recip, claims = 100, 240, 380, 520, 660, 800, 940
    lanes = [
        ("Lane_Shipper", "Shipper / Customer", ship, 140),
        ("Lane_Tower", "Control Tower / Dispatcher", tower, 140),
        ("Lane_Pickup", "Pickup Agent", pickup, 140),
        ("Lane_Hub", "Hub / Warehouse", hub, 140),
        ("Lane_Delivery", "Delivery Agent", delivery, 140),
        ("Lane_Recipient", "Recipient", recip, 140),
        ("Lane_Claims", "Claims Department", claims, 140),
    ]
    ys = {
        "Lane_Shipper": mid_y(ship),
        "Lane_Tower": mid_y(tower),
        "Lane_Pickup": mid_y(pickup),
        "Lane_Hub": mid_y(hub),
        "Lane_Delivery": mid_y(delivery),
        "Lane_Recipient": mid_y(recip),
        "Lane_Claims": mid_y(claims),
    }

    def N(i, name, kind, lane, x, y=None):
        return Node(i, name, kind, lane, x, ys[lane] if y is None else y)

    nodes = [
        N("Start_2", "Shipper books shipment", "start", "Lane_Shipper", 200),
        N("UT_Book", "Create shipment booking", "user", "Lane_Shipper", 320),
        N("BR_Rate", "Validate address, weight, SLA and rate", "business-rule", "Lane_Tower", 480),
        N("XOR_BookOk", "Booking valid?", "xor", "Lane_Tower", 640),
        N("UT_FixAddr", "Correct address / package data", "user", "Lane_Shipper", 800),
        N("ST_Schedule", "Schedule pickup and assign agent", "service", "Lane_Tower", 800),
        N("MT_Pickup", "Collect parcel and first scan", "manual", "Lane_Pickup", 960),
        N("XOR_Pickup", "Pickup successful?", "xor", "Lane_Pickup", 1120),
        N("XOR_PickupTries", "Reschedule attempts left?", "xor", "Lane_Tower", 1280),
        N("ST_CancelFee", "Cancel booking and raise fee", "service", "Lane_Tower", 1440),
        N("End_Cancelled", "Booking cancelled", "end", "Lane_Shipper", 1600),
        N("AND_SplitMove", "Move and track in parallel", "and", "Lane_Hub", 1280),
        N("ST_NotifyPickup", "Notify shipper: picked up", "send", "Lane_Tower", 1440),
        N("ST_HubSort", "Hub sort, scan and line-haul", "service", "Lane_Hub", 1440),
        N("AND_JoinMove", "In transit complete", "and", "Lane_Hub", 1600),
        N("OR_Intl", "International extra checks", "or", "Lane_Tower", 1760),
        N("UT_CustomsDocs", "Provide customs documents", "user", "Lane_Shipper", 1920),
        N("UT_CustomsClear", "Clear customs hold", "user", "Lane_Hub", 1920),
        N("OR_JoinIntl", "Export checks done", "or", "Lane_Tower", 2080),
        N("ST_OutForDel", "Dispatch last-mile and notify recipient", "send", "Lane_Delivery", 2240),
        N("UT_Deliver", "Hand over parcel and capture POD", "user", "Lane_Delivery", 2400),
        N("XOR_DelOut", "Delivery outcome", "xor", "Lane_Delivery", 2560),
        N("XOR_Attempts", "Delivery attempts < 3?", "xor", "Lane_Tower", 2720),
        N("TMR_Depot", "Hold at depot 7 days", "timer-catch", "Lane_Hub", 2880),
        N("ST_RTS", "Return to sender", "service", "Lane_Hub", 3040),
        N("End_RTS", "Returned to sender", "end", "Lane_Shipper", 3200),
        N("ST_Close", "Close shipment and generate invoice", "service", "Lane_Tower", 2720),
        N("End_Delivered", "Shipment delivered", "end", "Lane_Shipper", 2880),
        N("UT_Contact", "Contact recipient for address / COD", "user", "Lane_Delivery", 2720),
        N("XOR_AddrFix", "Address change / COD retry ok?", "xor", "Lane_Tower", 2880),
        N("UT_Inspect", "Inspect damage", "user", "Lane_Hub", 1760),
        N("XOR_Insured", "Insured?", "xor", "Lane_Claims", 1920),
        N("UT_Claim", "Claims: refund, replace or reship", "user", "Lane_Claims", 2080),
        N("ST_Uninsured", "Record damage and inform shipper", "send", "Lane_Tower", 2080),
        N("End_Claimed", "Exception closed (claim / damage)", "end", "Lane_Shipper", 2240),
        N("UT_Trace", "Trace missing scans", "user", "Lane_Tower", 1760),
        N("XOR_Found", "Parcel found in 5 days?", "xor", "Lane_Tower", 1920),
        N("ST_LostPay", "Declare lost and pay compensation", "service", "Lane_Claims", 2080),
        N("End_Lost", "Closed as lost", "end", "Lane_Shipper", 2240),
        N("EG_Delay", "Delay signal or timeout", "event-gw", "Lane_Tower", 1600),
        N("MSG_Delay", "Delay event (weather / breakdown)", "message-catch", "Lane_Tower", 1760),
        N("TMR_ETA", "ETA breach timer", "timer-catch", "Lane_Tower", 1760),
        N("ST_Reroute", "Notify customer and reroute / new ETA", "send", "Lane_Tower", 1920),
        N("UT_ManualScan", "Supervisor manual scan / reconcile", "user", "Lane_Hub", 1600),
        N("ST_RetryScan", "Retry scan write", "service", "Lane_Hub", 1760),
        N("TH_CompCancel", "Compensate: stop movement and refund", "compensate-throw", "Lane_Tower", 2080),
        N("ST_ReturnCancel", "Return parcel and refund minus fee", "service", "Lane_Claims", 2240),
        N("End_CancelTransit", "Cancelled after dispatch", "end", "Lane_Shipper", 2400),
        N("End_Refused", "Refused / COD failed — RTS", "end", "Lane_Shipper", 3040),
    ]

    coords = {
        "Start_2": (200, ys["Lane_Shipper"]),
        "UT_Book": (320, ys["Lane_Shipper"]),
        "BR_Rate": (500, ys["Lane_Tower"]),
        "XOR_BookOk": (680, ys["Lane_Tower"]),
        "UT_FixAddr": (680, ys["Lane_Shipper"]),
        "ST_Schedule": (860, ys["Lane_Tower"]),
        "MT_Pickup": (1040, ys["Lane_Pickup"]),
        "XOR_Pickup": (1220, ys["Lane_Pickup"]),
        "XOR_PickupTries": (1400, ys["Lane_Tower"]),
        "ST_CancelFee": (1580, ys["Lane_Tower"]),
        "End_Cancelled": (1760, ys["Lane_Shipper"]),
        "AND_SplitMove": (1400, ys["Lane_Hub"]),
        "ST_NotifyPickup": (1580, ys["Lane_Shipper"]),
        "ST_HubSort": (1580, ys["Lane_Hub"]),
        "AND_JoinMove": (1760, ys["Lane_Hub"]),
        "EG_Delay": (1940, ys["Lane_Tower"]),
        "MSG_Delay": (2120, ys["Lane_Tower"]),
        "TMR_ETA": (2120, ys["Lane_Pickup"]),
        "ST_Reroute": (2300, ys["Lane_Tower"]),
        "OR_Intl": (1940, ys["Lane_Hub"]),
        "UT_CustomsDocs": (2120, ys["Lane_Shipper"]),
        "UT_CustomsClear": (2120, ys["Lane_Hub"]),
        "OR_JoinIntl": (2300, ys["Lane_Hub"]),
        "ST_OutForDel": (2480, ys["Lane_Delivery"]),
        "UT_Deliver": (2660, ys["Lane_Delivery"]),
        "XOR_DelOut": (2840, ys["Lane_Delivery"]),
        "XOR_Attempts": (3020, ys["Lane_Tower"]),
        "TMR_Depot": (3200, ys["Lane_Hub"]),
        "ST_RTS": (3380, ys["Lane_Hub"]),
        "End_RTS": (3560, ys["Lane_Shipper"]),
        "ST_Close": (3020, ys["Lane_Tower"]),
        "End_Delivered": (3200, ys["Lane_Shipper"]),
        "UT_Contact": (3020, ys["Lane_Recipient"]),
        "XOR_AddrFix": (3200, ys["Lane_Delivery"]),
        "UT_Inspect": (1760, ys["Lane_Claims"]),
        "XOR_Insured": (1940, ys["Lane_Claims"]),
        "UT_Claim": (2120, ys["Lane_Claims"]),
        "ST_Uninsured": (2120, ys["Lane_Pickup"]),
        "End_Claimed": (2300, ys["Lane_Claims"]),
        "UT_Trace": (1940, ys["Lane_Pickup"]),
        "XOR_Found": (2120, ys["Lane_Pickup"]),
        "ST_LostPay": (2300, ys["Lane_Claims"]),
        "End_Lost": (2480, ys["Lane_Claims"]),
        "UT_ManualScan": (1760, ys["Lane_Pickup"]),
        "ST_RetryScan": (1940, ys["Lane_Delivery"]),
        "TH_CompCancel": (2300, ys["Lane_Shipper"]),
        "ST_ReturnCancel": (2480, ys["Lane_Claims"]),
        "End_CancelTransit": (2660, ys["Lane_Shipper"]),
        "End_Refused": (3200, ys["Lane_Pickup"]),
    }
    # fix ST_Close overlapping XOR_Attempts
    coords["ST_Close"] = (3020, ys["Lane_Shipper"])
    coords["End_Delivered"] = (3200, ys["Lane_Shipper"])
    coords["End_RTS"] = (3560, ys["Lane_Shipper"])
    coords["ST_Close"] = (3020, ys["Lane_Recipient"])
    coords["End_Delivered"] = (3200, ys["Lane_Recipient"])
    coords["XOR_Attempts"] = (3020, ys["Lane_Tower"])
    coords["UT_Contact"] = (3020, ys["Lane_Recipient"] - 0)
    # ST_Close vs UT_Contact
    coords["ST_Close"] = (3020, ys["Lane_Shipper"])
    coords["End_Delivered"] = (3180, ys["Lane_Shipper"])
    coords["UT_Contact"] = (3020, ys["Lane_Recipient"])
    coords["ST_LostPay"] = (2300, ys["Lane_Claims"])
    coords["UT_Claim"] = (2120, ys["Lane_Claims"])
    coords["ST_ReturnCancel"] = (2480, ys["Lane_Tower"])
    coords["End_CancelTransit"] = (2660, ys["Lane_Tower"])
    coords["End_Lost"] = (2480, ys["Lane_Pickup"])
    coords["End_Claimed"] = (2300, ys["Lane_Pickup"])
    coords["ST_Uninsured"] = (2120, ys["Lane_Tower"])
    coords["UT_Trace"] = (1760, ys["Lane_Tower"])
    coords["XOR_Found"] = (1940, ys["Lane_Pickup"])
    coords["UT_ManualScan"] = (1580, ys["Lane_Delivery"])
    coords["ST_RetryScan"] = (1760, ys["Lane_Delivery"])
    coords["End_Refused"] = (3380, ys["Lane_Delivery"])
    coords["ST_RTS"] = (3380, ys["Lane_Hub"])

    for n in nodes:
        n.x, n.y = coords[n.id]

    lane_by = [
        (ship, "Lane_Shipper"),
        (tower, "Lane_Tower"),
        (pickup, "Lane_Pickup"),
        (hub, "Lane_Hub"),
        (delivery, "Lane_Delivery"),
        (recip, "Lane_Recipient"),
        (claims, "Lane_Claims"),
    ]
    def lane_for_y(y):
        return min(lane_by, key=lambda t: abs(y - mid_y(t[0])))[1]
    for n in nodes:
        n.lane = lane_for_y(n.y)

    for n in nodes:
        if n.id == "MSG_Delay":
            n.extra["message"] = "Message_Delay"
        if n.id == "TMR_ETA":
            n.extra["duration"] = "PT12H"
        if n.id == "TMR_Depot":
            n.extra["duration"] = "P7D"

    flows = [
        Flow("g1", "Start_2", "UT_Book"),
        Flow("g2", "UT_Book", "BR_Rate"),
        Flow("g3", "BR_Rate", "XOR_BookOk"),
        Flow("g4", "XOR_BookOk", "UT_FixAddr", "Invalid address / weight"),
        Flow("g5", "UT_FixAddr", "UT_Book"),
        Flow("g6", "XOR_BookOk", "ST_Schedule", "Valid"),
        Flow("g7", "ST_Schedule", "MT_Pickup"),
        Flow("g8", "MT_Pickup", "XOR_Pickup"),
        Flow("g9", "XOR_Pickup", "XOR_PickupTries", "Shipper absent / not ready"),
        Flow("g10", "XOR_PickupTries", "MT_Pickup", "Reschedule (< 2)"),
        Flow("g11", "XOR_PickupTries", "ST_CancelFee", "2 failed pickups"),
        Flow("g12", "ST_CancelFee", "End_Cancelled"),
        Flow("g13", "XOR_Pickup", "AND_SplitMove", "Collected"),
        Flow("g14", "AND_SplitMove", "ST_NotifyPickup"),
        Flow("g15", "AND_SplitMove", "ST_HubSort"),
        Flow("g16", "ST_NotifyPickup", "AND_JoinMove"),
        Flow("g17", "ST_HubSort", "AND_JoinMove"),
        Flow("g18", "AND_JoinMove", "OR_Intl"),
        Flow("g19", "EG_Delay", "MSG_Delay"),
        Flow("g20", "EG_Delay", "TMR_ETA"),
        Flow("g21", "MSG_Delay", "ST_Reroute"),
        Flow("g22", "TMR_ETA", "ST_Reroute"),
        Flow("g23", "ST_Reroute", "ST_HubSort"),
        Flow("g24", "Boundary_DelayEvt", "EG_Delay"),
        Flow("g25", "OR_Intl", "UT_CustomsDocs", "Docs missing / international"),
        Flow("g26", "OR_Intl", "UT_CustomsClear", "Customs hold"),
        Flow("g26b", "OR_Intl", "OR_JoinIntl", "Domestic / no extra checks"),
        Flow("g27", "UT_CustomsDocs", "OR_JoinIntl"),
        Flow("g28", "UT_CustomsClear", "OR_JoinIntl"),
        Flow("g29", "OR_JoinIntl", "ST_OutForDel"),
        Flow("g30", "ST_OutForDel", "UT_Deliver"),
        Flow("g31", "UT_Deliver", "XOR_DelOut"),
        Flow("g32", "XOR_DelOut", "ST_Close", "Delivered + POD"),
        Flow("g33", "ST_Close", "End_Delivered"),
        Flow("g34", "XOR_DelOut", "XOR_Attempts", "Recipient unavailable"),
        Flow("g35", "XOR_Attempts", "UT_Deliver", "Retry delivery"),
        Flow("g36", "XOR_Attempts", "TMR_Depot", "3 attempts done"),
        Flow("g37", "TMR_Depot", "ST_RTS"),
        Flow("g38", "ST_RTS", "End_RTS"),
        Flow("g39", "XOR_DelOut", "UT_Contact", "Wrong address / COD issue"),
        Flow("g40", "UT_Contact", "XOR_AddrFix"),
        Flow("g41", "XOR_AddrFix", "UT_Deliver", "Updated / COD retried"),
        Flow("g42", "XOR_AddrFix", "ST_RTS", "Cannot deliver"),
        Flow("g43", "XOR_DelOut", "ST_RTS", "Refused / COD failed"),
        Flow("g44", "Boundary_Damage", "UT_Inspect"),
        Flow("g45", "UT_Inspect", "XOR_Insured"),
        Flow("g46", "XOR_Insured", "UT_Claim", "Insured"),
        Flow("g47", "XOR_Insured", "ST_Uninsured", "Not insured"),
        Flow("g48", "UT_Claim", "End_Claimed"),
        Flow("g49", "ST_Uninsured", "End_Claimed"),
        Flow("g50", "Boundary_Lost", "UT_Trace"),
        Flow("g51", "UT_Trace", "XOR_Found"),
        Flow("g52", "XOR_Found", "ST_HubSort", "Found — resume"),
        Flow("g53", "XOR_Found", "ST_LostPay", "Not found"),
        Flow("g54", "ST_LostPay", "End_Lost"),
        Flow("g55", "Boundary_ScanErr", "UT_ManualScan"),
        Flow("g56", "UT_ManualScan", "ST_RetryScan"),
        Flow("g57", "ST_RetryScan", "AND_JoinMove"),
        Flow("g58", "Boundary_Cancel", "TH_CompCancel"),
        Flow("g59", "TH_CompCancel", "ST_ReturnCancel"),
        Flow("g60", "ST_ReturnCancel", "End_CancelTransit"),
        Flow("g61", "Boundary_PickupEsc", "XOR_PickupTries"),
        Flow("g62", "Boundary_CustomsTimer", "ST_RTS"),
    ]

    boundaries = [
        {"id": "Boundary_PickupEsc", "name": "Pickup exception", "kind": "escalation", "attached": "MT_Pickup", "cancel": True},
        {"id": "Boundary_Damage", "name": "Damage found at scan", "kind": "error", "attached": "ST_HubSort", "cancel": True},
        {"id": "Boundary_Lost", "name": "No scan for 48 hours", "kind": "timer", "attached": "ST_HubSort", "cancel": True, "duration": "P2D"},
        {"id": "Boundary_ScanErr", "name": "Scanner / data mismatch", "kind": "error", "attached": "ST_HubSort", "cancel": False},
        {"id": "Boundary_Cancel", "name": "Shipper cancels in transit", "kind": "message", "attached": "ST_HubSort", "cancel": True, "message": "Message_Cancel"},
        {"id": "Boundary_CustomsTimer", "name": "Docs not received in 5 days", "kind": "timer", "attached": "UT_CustomsDocs", "cancel": True, "duration": "P5D"},
        {"id": "Boundary_DelayEvt", "name": "Delay while in transit", "kind": "message", "attached": "ST_HubSort", "cancel": False, "message": "Message_Delay"},
    ]

    messages = [
        ("Message_Delay", "Transit delay"),
        ("Message_Cancel", "Cancellation after dispatch"),
    ]

    return wrap(
        "LogisticsShipmentExceptions",
        "Logistics and Shipment Exception Management",
        "Pool_LOG",
        lanes,
        nodes,
        flows,
        boundaries,
        messages,
        pool_w=3800,
        pool_h=1020,
    )


def main() -> None:
    BPMN_DIR.mkdir(parents=True, exist_ok=True)
    p1 = BPMN_DIR / "assignment-1-student-project-approval.bpmn"
    p2 = BPMN_DIR / "assignment-2-logistics-shipment.bpmn"
    p1.write_text(assignment_1(), encoding="utf-8")
    p2.write_text(assignment_2(), encoding="utf-8")
    print(f"Wrote {p1}")
    print(f"Wrote {p2}")


if __name__ == "__main__":
    main()
