from fastapi import FastAPI ,HTTPException,Depends
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from Db import get_db,Base, engine
from models import Patient_table,ApprovedStaffTable, Doctor_table
from enum import Enum
from secured import hash_password
import os
app = FastAPI()

Base.metadata.create_all(bind=engine)
 
ADMIN_EMAIL = os.getenv("Admin_Email")
ADMIN_PASSWORD = os.getenv("Admin_Password")


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


class AdminLogin(BaseModel):
    Email: str
    password: str


class AdminLoginResponse(BaseModel):
    message: str
    Email: str
   
@app.post("/admin/login", response_model=AdminLoginResponse)
def admin_login(admin: AdminLogin):
    if admin.Email == ADMIN_EMAIL and admin.password == ADMIN_PASSWORD:
        return {"message": "Admin login successful", "Email": admin.Email}
    else:
        raise HTTPException(status_code=401, detail="Invalid email or password")

class ApprovedStaff(BaseModel):
    staff_id : str
    staff_Name: str
    Email:str
    model_config = ConfigDict(from_attributes=True)

class ApprovedStaffResponse(BaseModel):
    staff_id : str
    staff_Name: str
    Email:str
    model_config = ConfigDict(from_attributes=True)

@app.post("/admin/login/approve_staff", response_model= ApprovedStaffResponse, status_code= 201)
def approve_staff_id(staff: ApprovedStaff, db: Session = Depends(get_db)):
        existing = db.query(ApprovedStaffTable).filter(
        ApprovedStaffTable.staff_id == staff.staff_id).first()
        if existing:
          raise HTTPException(status_code=409, detail="Staff ID already approved")
       
        new_entry = ApprovedStaffTable(
                staff_id=staff.staff_id,
                staff_Name=staff.staff_Name,
                Email=staff.Email
        )
        db.add(new_entry)
        db.commit()
        db.refresh(new_entry)
        return new_entry
    
@app.get("/admin/approved_staff", response_model= list[ApprovedStaffResponse])
def get_approved_staff(db: Session = Depends(get_db)):
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
    
@app.get("/doctors", response_model=list[DoctorResponse])
def get_all_doctors(db: Session = Depends(get_db)):
        return db.query(Doctor_table).all()
    
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