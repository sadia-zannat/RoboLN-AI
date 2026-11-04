"""Deterministic planar constant-twist kinematics; no validated physical dynamics."""
import math
def simulate(params):
    dt=.2;x=z=yaw=distance=0.;trace=[];events=[];previous=''
    for step in range(round(params['duration']/dt)+1):
        t=round(step*dt,3);scenario=params['scenario'];speed=params['speed'];turn=math.radians(params['turn_rate'])
        obstacle=max(0.,4-distance) if scenario=='obstacle_stop' else None
        stopped=obstacle is not None and obstacle<=.8
        if stopped:speed=turn=0.
        dropout=scenario=='sensor_dropout' and t>=params['duration']*.45
        moisture=None if dropout else round(max(0.,min(100.,params['moisture']-(t*.65 if scenario=='dry_soil' else 0))),3)
        state='STOPPED_BY_SCENARIO' if stopped else 'SENSOR_DROPOUT' if dropout else 'MOVING' if speed else 'IDLE'
        if state!=previous:events.append({'t':t,'state':state,'origin':'SIMULATION'});previous=state
        trace.append({'t':t,'x':round(x,6),'z':round(z,6),'yaw_deg':round(math.degrees(yaw),6),'wheel_angle_deg':round(math.degrees(distance/params['wheel_radius']),6),'speed':speed,'soil_moisture':moisture,'virtual_distance':obstacle,'state':state,'origin':'SIMULATION'})
        if abs(turn)<1e-10:x+=speed*math.sin(yaw)*dt;z+=speed*math.cos(yaw)*dt
        else:x+=speed/turn*(math.cos(yaw)-math.cos(yaw+turn*dt));z+=speed/turn*(math.sin(yaw+turn*dt)-math.sin(yaw))
        yaw+=turn*dt;distance+=speed*dt
    return trace,events
