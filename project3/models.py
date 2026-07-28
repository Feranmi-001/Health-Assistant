from sqlalchemy import Column, Enum, Integer, String, ForeignKey,DateTime
from Db import Base
from enum import Enum as PyEnum
from sqlalchemy import Enum as SAEnum


class Patient_gender(str,PyEnum):
    Male = "Male"
    Female = "Female"

class Patient_table(Base):
    __tablename__= "patients"
    patient_id = Column(String, primary_key=True, index=True)
    patient_Name = Column(String, nullable=False)
    Age = Column(Integer, nullable=False)
    Patient_gender = Column(Enum(Patient_gender), nullable=False)
    Email = Column(String, unique=True, nullable=False)
    password = Column(String,nullable=False)

class ApprovedStaffTable(Base):
        __tablename__ = "approved_staff"
        staff_id = Column(String, primary_key=True, index=True)
        staff_Name = Column(String, nullable=False)
        Email = Column(String, unique=True, nullable=False)
       
class Doctor_table(Base):
      __tablename__ = "doctors"
      staff_id = Column(String, primary_key=True, index=True)
      Doctor_Name = Column(String, nullable=False)
      Field_of_Specialization = Column(String, nullable=False)
      Email = Column(String, unique=True, nullable=False)
      password = Column(String, nullable=False)


class Appointment_status(str, PyEnum):
    pending = "pending"
    confirmed = "confirmed"
    alternative_proposed = "alternative proposed"
    declined = "declined"
    Completed = "Completed"
    Cancelled = "Cancelled"

class Appointment_table(Base):
    __tablename__ = "appointments"
    appointment_id = Column(String, primary_key=True, index=True)
    patient_id = Column(String, ForeignKey("patients.patient_id"), nullable=False)
    staff_id = Column(String, ForeignKey("doctors.staff_id"), nullable=False)
    appointment_date = Column(DateTime, nullable=False)
    appointment_time = Column(DateTime, nullable=False)
    proposed_time = Column(DateTime, nullable=True)
    status = Column(SAEnum(Appointment_status), nullable= False, default=Appointment_status.pending)