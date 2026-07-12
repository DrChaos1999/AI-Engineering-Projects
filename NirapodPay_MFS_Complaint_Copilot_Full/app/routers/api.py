from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas import CaseListItem, ComplaintRequest, ComplaintResult, DemoReference
from app.services.complaint_orchestrator import ComplaintOrchestrator, list_cases
from app.services.transaction_service import TransactionNotFoundError, VerificationFailedError

router = APIRouter(prefix="/api")
orchestrator = ComplaintOrchestrator()


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "healthy", "service": "mfs-complaint-copilot"}


@router.get("/demo-references", response_model=list[DemoReference])
def demo_references() -> list[DemoReference]:
    return [
        DemoReference(reference_number="MFS202607120001", verification_code="4488", scenario="Completed same-MFS transfer"),
        DemoReference(reference_number="MFS202607120002", verification_code="7712", scenario="Failed transfer; sender debited"),
        DemoReference(reference_number="MFS202607120003", verification_code="0091", scenario="Reversed transaction"),
        DemoReference(reference_number="MFS202607120004", verification_code="3410", scenario="Long-pending cross-MFS transfer"),
        DemoReference(reference_number="MFS202607120005", verification_code="8824", scenario="Completed cross-MFS; receiver not credited"),
        DemoReference(reference_number="MFS202607120006", verification_code="6620", scenario="Suspected unauthorized transfer"),
    ]


@router.post("/complaints/analyze", response_model=ComplaintResult, status_code=status.HTTP_201_CREATED)
def analyze_complaint(request: ComplaintRequest, db: Session = Depends(get_db)) -> ComplaintResult:
    try:
        return orchestrator.analyze_and_create_case(
            db=db,
            reference_number=request.reference_number,
            verification_code=request.verification_code,
            customer_message=request.message,
        )
    except TransactionNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except VerificationFailedError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


@router.get("/cases", response_model=list[CaseListItem])
def get_cases(db: Session = Depends(get_db)) -> list[CaseListItem]:
    return [
        CaseListItem(
            case_id=case.public_case_id,
            reference_number=case.transaction.reference_number,
            category=case.category,
            priority=case.priority,
            routed_team=case.routed_team,
            summary=case.summary,
            status=case.status,
            created_at=case.created_at,
        )
        for case in list_cases(db)
    ]
