from fastapi import FastAPI ,HTTPException
from pydantic import BaseModel
app = FastAPI()

patient_db= {
}

class Patient(BaseModel):
 patient_Name : str  
 Age:int
 Email:str
 password : str

class PatientResponse(BaseModel):
    patient_id : str
    patient_Name: str
    Email:str

patient_counter=1

 

@app.post("/patients/create_patient", response_model= PatientResponse, status_code= 201)
def create_patient(patient:Patient):
    global patient_counter
    patient_id = f"2026{patient_counter:04d}"
    patient_counter += 1
    
    patient_db[patient_id] ={
       "patient_id": patient_id, 
       "patient_Name" : patient.patient_Name,
        "Email": patient.Email,
        "password": patient.password,
    }
    return patient_db[patient_id]

@app.get("/get_patient", response_model= list[PatientResponse])
def get_patients():
   return list(patient_db.values())

@app.get("/patients/{patient_id}", response_model= PatientResponse)
def get_patient(patient_id: str):
   found = patient_db.get(patient_id)
   if not found : raise HTTPException(status_code=404, detail= "Patient Not Found")    
   return patient_db[patient_id]






