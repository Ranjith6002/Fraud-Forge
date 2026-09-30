from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.rule import RuleModel
from app.schemas.rule import RuleCreate, RuleOut, RuleUpdate

router = APIRouter(prefix="/api/rules", tags=["rules"])


@router.get("", response_model=List[RuleOut], summary="List all configured fraud rules")
def list_rules(db: Session = Depends(get_db)):
    models = db.scalars(select(RuleModel).order_by(RuleModel.id)).all()
    return models


@router.post("", response_model=RuleOut, status_code=status.HTTP_201_CREATED, summary="Add a new fraud rule")
def create_rule(payload: RuleCreate, db: Session = Depends(get_db)):
    existing = db.scalar(select(RuleModel).where(RuleModel.name == payload.name))
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A rule named '{payload.name}' already exists.",
        )

    model = RuleModel(
        name=payload.name,
        rule_type=payload.rule_type,
        description=payload.description,
        enabled=payload.enabled,
        risk_score=payload.risk_score,
        parameters=payload.parameters,
    )
    db.add(model)
    db.commit()
    db.refresh(model)
    return model


@router.get("/{rule_id}", response_model=RuleOut, summary="Get rule details")
def get_rule(rule_id: int, db: Session = Depends(get_db)):
    model = db.get(RuleModel, rule_id)
    if not model:
        raise HTTPException(status_code=404, detail=f"Rule with ID {rule_id} not found.")
    return model


@router.patch("/{rule_id}", response_model=RuleOut, summary="Update rule configuration or enabled status")
def update_rule(rule_id: int, payload: RuleUpdate, db: Session = Depends(get_db)):
    model = db.get(RuleModel, rule_id)
    if not model:
        raise HTTPException(status_code=404, detail=f"Rule with ID {rule_id} not found.")

    if payload.name is not None and payload.name != model.name:
        existing = db.scalar(select(RuleModel).where(RuleModel.name == payload.name))
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"A rule named '{payload.name}' already exists.",
            )
        model.name = payload.name

    if payload.description is not None:
        model.description = payload.description
    if payload.enabled is not None:
        model.enabled = payload.enabled
    if payload.risk_score is not None:
        model.risk_score = payload.risk_score
    if payload.parameters is not None:
        model.parameters = payload.parameters

    db.commit()
    db.refresh(model)
    return model


@router.delete("/{rule_id}", status_code=status.HTTP_200_OK, summary="Delete or deactivate rule")
def delete_rule(rule_id: int, db: Session = Depends(get_db)):
    model = db.get(RuleModel, rule_id)
    if not model:
        raise HTTPException(status_code=404, detail=f"Rule with ID {rule_id} not found.")

    db.delete(model)
    db.commit()
    return {"message": f"Rule '{model.name}' deleted successfully."}
