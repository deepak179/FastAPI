from fastapi import FastAPI, Path, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, computed_field
from typing import Annotated, Literal, Optional
import json

app = FastAPI()

class Patient(BaseModel):
    id : Annotated[str, Field(..., description="Unique identifier for the patient", example="P001")]
    name : Annotated[str, Field(..., description="Full name of the patient", example="John Doe")]
    age : Annotated[int, Field(..., gt=0, lt=120, description="Age of the patient in years", example=30)] 
    city : Annotated[str, Field(..., description="City where the patient resides", example="New York")]
    gender : Annotated[Literal['male', 'female','others'], Field(..., description="Gender of the patient")]
    height : Annotated[float, Field(..., gt=0, description="Height of the patient in meters", example=175)]
    weight : Annotated[float, Field(..., gt=0, description="Weight of the patient in kilograms", example=70)]

    @computed_field
    @property
    def bmi(self) -> float:
        bmi = round(self.weight / (self.height ** 2), 2)
        return bmi
    
    @computed_field
    @property
    def verdict(self) -> str:
        if self.bmi < 18.5:
            return "Underweight"
        elif 18.5 <= self.bmi < 24.9:
            return "Normal"
        elif 25 <= self.bmi < 29.9:
            return "Overweight"
        else:
            return "Obese"
        
class PatientUpdate(BaseModel):
    name: Annotated[Optional[str], Field(default=None)]
    city: Annotated[Optional[str], Field(default=None)]
    age: Annotated[Optional[int], Field(default=None, gt=0)]
    gender: Annotated[Optional[Literal['male', 'female']], Field(default=None)]
    height: Annotated[Optional[float], Field(default=None, gt=0)]
    weight: Annotated[Optional[float], Field(default=None, gt=0)]

def load_data():
    with open("patients.json", "r") as f:
        data = json.load(f)
        
    return data

def save_data(data):
    with open('patients.json', 'w') as f:
        json.dump(data, f)

@app.get("/")
async def hello():
    return {"message":"Patient Management System API"}

@app.get("/about")
async def about():
    return {"message":"A fully functional API to manage your patients records"}

@app.get("/view")
async def view():
    data = load_data()
    
    return data

@app.get("/patient/{patient_id}")
async def view_patient(patient_id: str = Path(..., description = "ID of the patient in DB", example = "P001")):    #... means it is required
    #load all the patients
    data = load_data()
    
    if patient_id in data:
        return data[patient_id]
    
    raise HTTPException(status_code = 404, detail = "Patient not found")

@app.get("/sort")
async def sort_patients(sort_by: str = Query(..., detail = "Sort on the basis of height, weight, or bmi"), order: Literal["asc", "desc"] = Query("asc", description = "Order of sorting, either asc or desc")):
    fields = ["height", "weight", "bmi"]
    
    if sort_by not in fields:
        raise HTTPException(status_code = 400, detail = f"Invalid sort_by parameter: {sort_by}. Must be one of {fields}")
    
    if order not in ["asc", "desc"]:
        raise HTTPException(status_code = 400, detail = f"Invalid order parameter: {order}. Must be either 'asc' or 'desc'.")

    data = load_data()
    sorted_data = sorted(data.values(), key=lambda x: x.get(sort_by, 0), reverse=(order == "desc"))
    
    return sorted_data

@app.post("/add")
async def add_patient(patient: Patient):
    data = load_data()

    #check if patient already exists
    if patient.id in data:
        raise HTTPException(status_code=400, detail="Patient with this ID already exists")

    #new patient add to the database
    data[patient.id] = patient.model_dump(exclude=['id'])
    
    #save in json file
    with open("patients.json", "w") as f:
        json.dump(data, f)

    return JSONResponse(status_code=201, content={"message": "Patient added successfully", "patient_id": patient.id})
    #return {"message": "Patient added successfully"}
    
@app.put("/update/{patient_id}")
async def update_patient(patient_id: str, patient_update: PatientUpdate):
    data = load_data()

    if patient_id not in data:
        raise HTTPException(status_code=404, detail="Patient not found")

    existing_patient_info = data[patient_id]
    
    # Update patient information
    update_info = patient_update.model_dump(exclude_unset=True)    #update_info will be dict of keys which client wants to update(set keys) exclude rest of keys using exclude_unset
    
    for key, value in update_info.items():
        existing_patient_info[key] = value
        
    #existing_patient_info -> pydantic object -> updated bmi + verdict
    existing_patient_info['id'] = patient_id
    patient_pydandic_obj = Patient(**existing_patient_info)
    #-> pydantic object -> dict
    existing_patient_info = patient_pydandic_obj.model_dump(exclude='id')

    # add this dict to data
    data[patient_id] = existing_patient_info

    # Save changes to JSON file
    with open("patients.json", "w") as f:
        json.dump(data, f)

    return {"message": "Patient updated successfully"}

@app.delete("/delete/{patient_id}")
async def delete_patient(patient_id: str):
    data = load_data()
    
    if patient_id not in data:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    del data[patient_id]
    
    save_data(data)
    
    return JSONResponse(status_code=200, content={"message": "Patient deleted successfully"})

@app.get("/sum")
async def sum(a: float = Query(..., description="First number"), b: float = Query(..., description="Second number")):
    return {"sum {} + {}".format(a,b) : a + b}