from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from backend.app.api.deps import get_db
from backend.app.schemas.dataset import ImportRequest, ImportResult, DatasetOut
from backend.app.services import dataset_service, audit_service

router = APIRouter()

@router.post("/import", response_model=ImportResult)
def import_data(req: ImportRequest, db: Session = Depends(get_db)):
    result = dataset_service.import_dataset(
        req.file_path, req.format or "csv", db,
        reset=req.reset, dataset_name=req.dataset_name, description=req.description,
    )
    audit_service.log(db, "import", entity="dataset", entity_id=result.get("dataset_id"),
                      detail=f"imported={result['imported']} skipped={result['skipped']}")
    return result

@router.get("/", response_model=List[DatasetOut])
def list_datasets(db: Session = Depends(get_db)):
    return dataset_service.list_datasets(db)

@router.get("/{dataset_id}", response_model=DatasetOut)
def get_dataset(dataset_id: int, db: Session = Depends(get_db)):
    return dataset_service.get_dataset(db, dataset_id)