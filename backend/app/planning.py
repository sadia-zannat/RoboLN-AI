"""Bounded deterministic engineering intake: NOT a generative AI model or safety approval.

Suggestions are component *categories*, never verified electrical pins, prices or
manufacturer compatibility. A project can be edited without a hardcoded screen.
"""
from dataclasses import dataclass
from typing import Any

@dataclass(frozen=True)
class Family:
    key: str
    name: str
    risk: str
    parts: tuple[str, ...]
    questions: tuple[str, ...]
    tasks: tuple[str, ...]

COMMON = (
    'Identify the exact board, revision, supply and component manufacturer part numbers.',
    'Obtain datasheets and verify voltage, current, power budget, pin functions and protection independently.',
    'Have a competent person review the wiring, power isolation and safe test procedure.',
    'Build unpowered; inspect connections and polarity before applying a current-limited supply.',
    'Record actual measurements and evidence; do not mark unobserved behaviour as PASS.',
)
FAMILIES = {
    'obstacle_alarm': Family('obstacle_alarm','Obstacle detector / parking alarm','LOW_VOLTAGE_REVIEW',('Distance sensor (exact part to confirm)','Compatible controller / SBC','Low-voltage indicator','Suitable regulated supply'),('Sensor type and part number','Detection range and environment','Board revision and logic level'),('Verify sensor pin functions against its datasheet','Prototype read-only sensor acquisition','Test at measured distances with uncertainty and false-positive checks')),
    'agri_inspection': Family('agri_inspection','Agricultural inspection rover','ACTUATOR_REVIEW',('Controller / SBC','Soil moisture sensor + interface','Camera (optional)','Motors, rated driver and power distribution','Independent pump cutoff (optional)'),('Target environment','Sensor electrical interface and calibration','Actuator ratings and physical emergency stop'),('Calibrate moisture measurements against physical soil samples','Test wheels and pump separately under supervision','Enable monitoring before considering any bounded actuation')),
    'robot_arm': Family('robot_arm','Educational robotic arm','ACTUATOR_REVIEW',('Rated servos / motor drivers','Controller','Mechanically constrained arm','Current-limited regulated supply'),('Payload and reach','Actuator stall current','Mechanical end stops and E-stop'),('Verify reachable geometry without power','Test each servo under low load with hardware safety','Validate current budget and motion limits')),
    'smart_irrigation': Family('smart_irrigation','Low-voltage irrigation demonstrator','ACTUATOR_REVIEW',('Moisture sensor and suitable ADC/interface','Microcontroller / SBC','Rated low-voltage pump driver','Independent manual shutoff'),('Pump supply rating','Moisture calibration method','Fail-safe dry-run behaviour'),('Log measurements with units and calibration','Test alert logic with recorded inputs','Review supervised pump enable limits')),
    'environment_monitor': Family('environment_monitor','Environmental sensor monitoring','LOW_VOLTAGE_REVIEW',('Environmental sensor module (exact variant)','Compatible controller','Regulated supply','Data logging destination'),('Target measurement and units','Sensor model and interface','Measurement range and calibration'),('Check sensor datasheet and wiring','Acquire timestamped observations','Compare readings with a reference instrument')),
    'solar_demo': Family('solar_demo','Miniature solar tracker','ACTUATOR_REVIEW',('Small solar demonstration panel','Light sensing circuit','Rated servo or geared motor','Low-voltage controller'),('Panel and motor ratings','Indoor or outdoor use','Mechanical rotation limit'),('Check motor current and panel isolation','Test light sensing without motion','Supervise small-angle motion within physical stops')),
    'generic': Family('generic','Other low-voltage embedded project','REVIEW_REQUIRED',('Board/processor (unverified)','Inputs and outputs to specify','Regulated power (to determine)'),('What should the project do?','Exact board and component versions','Available supply and physical environment'),('Define measurable acceptance criteria','Review electrical and mechanical constraints','Build a safe, reproducible test plan')),
}
RESTRICTED_HINTS = ('mains','220v','230v','240v','high voltage','railway crossing','train gate','jammer','jamming','interference transmitter','medical life support','weapon','explosive','autonomous drone flight','grid inverter','lithium battery charger','110v','120v','ac mains','bypass interlock','bypass emergency stop','nonconsensual tracking','high-power inverter')

def catalog() -> list[dict[str, str]]:
    return [{'key':v.key,'name':v.name,'risk_class':v.risk} for v in FAMILIES.values()]

def draft_engineering_plan(*, family_key: str, goal: str, board: str, revision: str, available_parts: str, context_version: int) -> dict[str,Any]:
    family=FAMILIES[family_key]
    normalized=goal.strip()
    if not normalized: raise ValueError('A project goal is required')
    restricted=any(hint in normalized.lower() for hint in RESTRICTED_HINTS)
    blockers=[]
    if not board.strip(): blockers.append('Exact board model is not identified')
    if not revision.strip(): blockers.append('Board revision is not identified')
    if not available_parts.strip(): blockers.append('No exact parts or model numbers supplied')
    blockers.append('Manufacturer datasheet and reviewed pin/power compatibility are not attached')
    if family.risk=='ACTUATOR_REVIEW': blockers.append('Actuator power, physical stop and independent safe-off have not been verified')
    if restricted: blockers.insert(0,'RESTRICTED_OPERATION: provide only conceptual analysis or safe low-voltage simulation; no operational control or wiring')
    return {
        'family':family.key,'title':family.name,'goal':normalized,'board':board.strip() or None,
        'board_revision':revision.strip() or None,'parts_available':available_parts.strip() or None,
        'context_version':context_version,'mode':'RESTRICTED_CONCEPT_ONLY' if restricted else 'ENGINEERING_DRAFT',
        'risk_class':'RESTRICTED' if restricted else family.risk,
        'candidate_parts':list(family.parts) if not restricted else [],
        'questions':list(family.questions),
        'steps':list(COMMON + family.tasks) if not restricted else ['Document the intended use and safety hazards.','Choose a harmless simulation or low-voltage demonstration for review.'],
        'blockers':blockers,
        'verification':'NOT_VERIFIED',
        'evidence':[],
        'model_provenance':{'provider':'DETERMINISTIC_RULES','meta_model_inference':False},
        'disclaimer':'No manufacturer compatibility, wiring pin, 3D geometry, measurement, hardware test or AI inference has been verified. This is a preliminary intake, not an approved physical build plan.'
    }
