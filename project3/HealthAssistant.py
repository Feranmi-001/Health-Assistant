from fastapi import FastAPI ,HTTPException,Depends
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from Db import get_db,Base, engine
from models import Patient_table,ApprovedStaffTable, Doctor_table, Appointment_table, Patient_gender, Appointment_status
from enum import Enum
from secured import hash_password
import os
from datetime import datetime
from dotenv import load_dotenv
from secured import hash_password, verify_password
from Authentication import (
     create_access_token,
     get_current_user,
     require_admin,
     require_doctor,    
     require_patient,
)       
load_dotenv()
app = FastAPI()


Base.metadata.create_all(bind=engine)
 
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL")
ADMIN_PASSWORD_HASH = hash_password(os.getenv("ADMIN_PASSWORD"))


class Patient_gender(str,Enum):
   Male = "Male"
   Female = "Female"
class Patient(BaseModel):
 patient_Name : str  
 Age:int
 Patient_gender: Patient_gender
 Email:str
 password : str

class PatientResponse(BaseModel):
    patient_id : str
    patient_Name: str
    Email:str
    model_config = ConfigDict(from_attributes=True)



class Token(BaseModel):
      access_token: str
      token_type: str= "bearer"


def generate_next_patient_id(db: Session):
    last_patient = db.query(Patient_table).order_by(Patient_table.patient_id.desc()).first()
    if last_patient:
        last_id = int(last_patient.patient_id[4:])
        next_id = f"2026{last_id + 1:04d}"
    else:
        next_id = "20260001"
    return next_id

def handle_integrity_error(e: IntegrityError):
    error_message = str(e.orig)
    if "Email" in error_message or "email" in error_message:
        raise HTTPException(status_code=409, detail="Email already exists",)
    else:
        raise HTTPException(status_code=400, detail="Could not create patient :{error_message}",)

@app.post("/patients/create_patient", response_model= PatientResponse, status_code= 201)
def create_patient(patient:Patient, db: Session = Depends(get_db)):
    patient_id = generate_next_patient_id(db)
   
    new_patient = Patient_table(
        patient_id= patient_id,
        patient_Name=patient.patient_Name,
        Age=patient.Age,
        Patient_gender=patient.Patient_gender,
        Email=patient.Email,
        password=hash_password(patient.password),
     )
    
 
    db.add(new_patient)
    try:
         db.commit()
         db.refresh(new_patient)
    except IntegrityError as e:
        db.rollback()
        handle_integrity_error(e)
    return new_patient


@app.get("/get_patient", response_model= list[PatientResponse])
def get_patients(db: Session = Depends(get_db)):
   return db.query(Patient_table).all()

@app.get("/patients/{patient_id}", response_model= PatientResponse)
def get_patient(patient_id: str, db: Session = Depends(get_db)):
   found = db.query(Patient_table).filter(Patient_table.patient_id == patient_id).first()
   if not found : raise HTTPException(status_code=404, detail= "Patient Not Found")    
   return db.query(Patient_table).filter(Patient_table.patient_id == patient_id).first()

@app.put("/patients/{patient_id}", response_model= PatientResponse)
def update_patient(patient_id: str, updated_patient: Patient, db: Session = Depends(get_db)):
    patient = db.query(Patient_table).filter(Patient_table.patient_id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient Not Found")
    
    patient.patient_Name = updated_patient.patient_Name
    patient.Age = updated_patient.Age
    patient.Patient_gender = updated_patient.Patient_gender
    patient.Email = updated_patient.Email
    patient.password = hash_password(updated_patient.password)
    
    try:
        db.commit() 
        db.refresh(patient)
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(status_code=409, detail="Email already exists")
        handle_integrity_error(e)
    return patient



@app.delete("/patients/{patient_id}", status_code=204)
def delete_patient(patient_id: str, db: Session = Depends(get_db)):
    patient = db.query(Patient_table).filter(Patient_table.patient_id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient Not Found")
    
    db.delete(patient)
    db.commit()
    return {"message": "Patient deleted successfully"}

class PatientLogin(BaseModel):
    Email: str
    password: str


@app.post("/patients/login", response_model=Token)
def patient_login(credentials: PatientLogin, db: Session = Depends(get_db)):
    patient = db.query(Patient_table).filter(Patient_table.Email == credentials.Email).first()
    if not patient or not verify_password(credentials.password, patient.password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    token = create_access_token(data={"sub": patient.Email, "role": "patient"})
    return {"access_token": token, "token_type": "bearer"}


class AdminLogin(BaseModel):
    Email: str
    password: str



   
@app.post("/admin/login", response_model=Token)
def admin_login(credentials: AdminLogin):
    if credentials.Email != ADMIN_EMAIL or not verify_password(
        credentials.password, ADMIN_PASSWORD_HASH
        ):
 
        raise HTTPException(status_code=401, detail="Invalid email or password")
 
    token = create_access_token(data={"sub": credentials.Email, "role": "admin"})
    return {"access_token": token, "token_type": "bearer"}
   


class ApprovedStaff(BaseModel):
    staff_id : str
    staff_Name: str
    Email:str
    

class ApprovedStaffResponse(BaseModel):
    staff_id : str
    staff_Name: str
    Email:str
    model_config = ConfigDict(from_attributes=True)

@app.post("/admin/approve_staff", response_model= ApprovedStaffResponse, status_code= 201)
def approve_staff_id(staff: ApprovedStaff, db: Session = Depends(get_db),
                    current_admin: dict = Depends(require_admin)):
        existing = db.query(ApprovedStaffTable).filter(
        ApprovedStaffTable.staff_id == staff.staff_id).first()
        if existing:
          raise HTTPException(status_code=409, detail="Staff ID already approved")
       
        new_entry = ApprovedStaffTable(
                staff_id=staff.staff_id,
                staff_Name=staff.staff_Name,
                Email=staff.Email,
        )
        db.add(new_entry)
        try:
            db.commit()
            db.refresh(new_entry)
            return new_entry
        except IntegrityError as e:
            db.rollback()
            handle_integrity_error(e)

        return new_entry

@app.get("/admin/approved_staff", response_model=list[ApprovedStaffResponse])
def get_approved_staff(
    db: Session = Depends(get_db),
    current_admin: dict = Depends(require_admin),
):
    return db.query(ApprovedStaffTable).all()  
    
 

class Doctor (BaseModel):
    staff_id : str
    Doctor_Name: str
    Field_of_Specialization: str
    Email:str
    password : str
    model_config = ConfigDict(from_attributes=True)

class DoctorResponse(BaseModel):
    staff_id : str
    Doctor_Name: str
    Field_of_Specialization: str
    Email:str
    model_config = ConfigDict(from_attributes=True)

@app.post("/doctors/register", response_model= DoctorResponse, status_code= 201)
def register_doctor(doctor: Doctor, db: Session = Depends(get_db)):
        approved= db.query(ApprovedStaffTable).filter(ApprovedStaffTable.staff_id == doctor.staff_id).first()
        if not approved:
            raise HTTPException(status_code=403, detail="Staff ID not approved")
        
        already_registered = db.query(Doctor_table).filter(Doctor_table.staff_id == doctor.staff_id).first()
        if already_registered:
            raise HTTPException(status_code=409, detail="Doctor already registered")
        
        new_doctor = Doctor_table(
            staff_id=doctor.staff_id,
            Doctor_Name=doctor.Doctor_Name,
            Field_of_Specialization=doctor.Field_of_Specialization,
            Email=doctor.Email,
            password=hash_password(doctor.password)
        )

        db.add(new_doctor)
        try:
            db.commit()
            db.refresh(new_doctor)
        except IntegrityError as e:
            db.rollback()
            handle_integrity_error(e)
        return new_doctor



    
class DoctorLogin(BaseModel):
    Email: str
    password: str


@app.post("/doctors/login", response_model=Token)
def doctor_login(credentials: DoctorLogin, db: Session = Depends(get_db)):
    doctor = db.query(Doctor_table).filter(Doctor_table.Email == credentials.Email).first()
    if not doctor or not verify_password(credentials.password, doctor.password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    token = create_access_token(data={"sub": doctor.Email, "role": "doctor"})
    return {"access_token": token, "token_type": "bearer"}


@app.get("/doctors", response_model=list[DoctorResponse])
def get_all_doctors(
    db: Session = Depends(get_db),  
    current_user: dict = Depends(get_current_user),
):
    return db.query(Doctor_table).all()   
  
@app.get("/doctors/search", response_model=list[DoctorResponse])
def search_doctors(
    name: str = None,
    specialization: str = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    query = db.query(Doctor_table)
    if name:
        query = query.filter(Doctor_table.Doctor_Name.contains(name))
    if specialization:
        query = query.filter(Doctor_table.Field_of_Specialization == specialization)
    return query.all()

@app.get("/doctors/me", response_model=DoctorResponse)
def get_current_doctor(
    db: Session = Depends(get_db),
    current_doctor: dict = Depends(require_doctor),
):
    doctor = db.query(Doctor_table).filter(Doctor_table.Email == current_doctor["email"]).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
    return doctor

@app.get("/doctors/{staff_id}", response_model=DoctorResponse)
def get_doctor(staff_id: str, db: Session = Depends(get_db)):
    doctor = db.query(Doctor_table).filter(Doctor_table.staff_id == staff_id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor Not Found")
    return doctor

@app.put("/doctors/{staff_id}", response_model=DoctorResponse)
def update_doctor(staff_id: str, updated_doctor: Doctor, db: Session = Depends(get_db)):
        doctor = db.query(Doctor_table).filter(Doctor_table.staff_id == staff_id).first()
        if not doctor:
            raise HTTPException(status_code=404, detail="Doctor Not Found")
        
        doctor.Doctor_Name = updated_doctor.Doctor_Name
        doctor.Field_of_Specialization = updated_doctor.Field_of_Specialization
        doctor.Email = updated_doctor.Email
        doctor.password = hash_password(updated_doctor.password)
        
        try:
            db.commit()
            db.refresh(doctor)
        except IntegrityError as e:
            db.rollback()
            handle_integrity_error(e)
        return doctor
    
@app.delete("/doctors/{staff_id}", status_code=204)
def delete_doctor(staff_id: str, db: Session = Depends(get_db)):    
        doctor = db.query(Doctor_table).filter(Doctor_table.staff_id == staff_id).first()
        if not doctor:
            raise HTTPException(status_code=404, detail="Doctor Not Found")
        
        db.delete(doctor)
        db.commit()
        return {"message": "Doctor deleted successfully"}



class AppointmentCreate(BaseModel):
    staff_id: str           
    appointment_date: datetime
    appointment_time: datetime
    
class AppointmentResponse(BaseModel):
    appointment_id: str
    patient_id: str
    staff_id: str
    appointment_time: datetime
    appointment_date: datetime
    proposed_time: datetime | None = None
    status: Appointment_status
    model_config = ConfigDict(from_attributes=True)


def generate_next_appointment_id(db: Session):
        last_appointment = db.query(Appointment_table).order_by(Appointment_table.appointment_id.desc()).first()
        if last_appointment:
            last_id = int(last_appointment.appointment_id[4:])
            next_id = f"APP-{last_id + 1:05d}"
        else :
            next_id="APP-00001"
        return next_id
 

@app.post("/appointments", response_model=AppointmentResponse, status_code=201)
def book_appointment(
    appointment: AppointmentCreate,
    db: Session = Depends(get_db),
    current_patient: dict = Depends(require_patient),
):
    patient = db.query(Patient_table).filter(
        Patient_table.Email == current_patient["email"]
    ).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
 
    doctor = db.query(Doctor_table).filter(
        Doctor_table.staff_id == appointment.staff_id
    ).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
    new_appointment_id=  generate_next_appointment_id(db)

    new_appointment = Appointment_table(
        appointment_id=new_appointment_id,
        patient_id=patient.patient_id,
        staff_id=appointment.staff_id,
        appointment_time=appointment.appointment_time,
        appointment_date=appointment.appointment_date,
        status=Appointment_status.pending, 
    )
    db.add(new_appointment)
    db.commit()
    db.refresh(new_appointment)
    return new_appointment
 
 
@app.get("/appointments", response_model=list[AppointmentResponse])
def get_all_appointments(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    if current_user["role"] not in ("admin", "doctor"):
        raise HTTPException(status_code=403, detail="Not permitted to view all appointments")
    return db.query(Appointment_table).all()
 
 
@app.get("/patients/me/appointments", response_model=list[AppointmentResponse])
def get_my_appointments(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_patient),
):
    patient = db.query(Patient_table).filter(
        Patient_table.Email == current_user["email"]
    ).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
 
    return db.query(Appointment_table).filter(
        Appointment_table.patient_id == patient.patient_id
    ).all()
 
 
@app.get("/doctors/me/appointments", response_model=list[AppointmentResponse])
def get_my_doctor_appointments(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_doctor),
):
    doctor = db.query(Doctor_table).filter(
        Doctor_table.Email == current_user["email"]
    ).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
 
    return db.query(Appointment_table).filter(
        Appointment_table.staff_id == doctor.staff_id
    ).all()
 
class DoctorAppointmentAction(BaseModel):
    action: str 
    proposed_time: datetime | None = None 
 
@app.put("/appointments/{appointment_id}/doctor-response", response_model=AppointmentResponse)
def doctor_respond_to_appointment(
    appointment_id: str,
    response: DoctorAppointmentAction,
    db: Session = Depends(get_db),
    current_doctor: dict = Depends(require_doctor),
):
    appointment = db.query(Appointment_table).filter(
        Appointment_table.appointment_id == appointment_id
    ).first()
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
 
    doctor = db.query(Doctor_table).filter(
        Doctor_table.Email == current_doctor["email"]
    ).first()
    if not doctor or appointment.staff_id != doctor.staff_id:
        raise HTTPException(status_code=403, detail="Not your appointment to respond to")
 
    if appointment.status != Appointment_status.pending:
        raise HTTPException(
            status_code=400,
            detail="Only pending appointments can be responded to",
        )
 
    if response.action == "confirm":
        appointment.status = Appointment_status.confirmed
 
    elif response.action == "decline":
        appointment.status = Appointment_status.declined
 
    elif response.action == "propose_alternative":
        if not response.proposed_time:
            raise HTTPException(
                status_code=400,
                detail="proposed_time is required when proposing an alternative",
            )
        appointment.proposed_time = response.proposed_time
        appointment.status = Appointment_status.alternative_proposed
 
    else:
        raise HTTPException(status_code=400, detail="Invalid action")
 
    db.commit()
    db.refresh(appointment)
    return appointment
 
 
class PatientAppointmentAction(BaseModel):
    action: str  
 
 
@app.put("/appointments/{appointment_id}/patient-response", response_model=AppointmentResponse)
def patient_respond_to_alternative(
    appointment_id: str,
    response: PatientAppointmentAction,
    db: Session = Depends(get_db),
    current_patient: dict = Depends(require_patient),
):
    appointment = db.query(Appointment_table).filter(
        Appointment_table.appointment_id == appointment_id
    ).first()
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
 
    patient = db.query(Patient_table).filter(
        Patient_table.Email == current_patient["email"]
    ).first()
    if not patient or appointment.patient_id != patient.patient_id:
        raise HTTPException(status_code=403, detail="Not your appointment to respond to")
 
    if appointment.status != Appointment_status.alternative_proposed:
        raise HTTPException(
            status_code=400,
            detail="There is no proposed alternative time to respond to",
        )
 
    if response.action == "accept":
        appointment.appointment_time = appointment.proposed_time
        appointment.proposed_time = None
        appointment.status = Appointment_status.confirmed
 
    elif response.action == "decline":
        appointment.status = Appointment_status.declined
 
    else:
        raise HTTPException(status_code=400, detail="Invalid action")
 
    db.commit()
    db.refresh(appointment)
    return appointment
 
 
@app.put("/appointments/{appointment_id}/complete", response_model=AppointmentResponse)
def mark_appointment_completed(
    appointment_id: str,
    db: Session = Depends(get_db),
    current_doctor: dict = Depends(require_doctor),
):
    appointment = db.query(Appointment_table).filter(
        Appointment_table.appointment_id == appointment_id
    ).first()
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
 
    doctor = db.query(Doctor_table).filter(
        Doctor_table.Email == current_doctor["email"]
    ).first()
    if not doctor or appointment.staff_id != doctor.staff_id:
        raise HTTPException(status_code=403, detail="Not your appointment to update")
 
    if appointment.status != Appointment_status.confirmed:
        raise HTTPException(
            status_code=400,
            detail="Only confirmed appointments can be marked completed",
        )
 
    appointment.status = Appointment_status.completed
    db.commit()
    db.refresh(appointment)
    return appointment