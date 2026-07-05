"""Imports every model so Base.metadata is complete for Alembic autogenerate."""
from app.models.account import Account, Contact
from app.models.activity import Activity
from app.models.audit import AuditLog
from app.models.auth import RevokedToken
from app.models.lead import Lead
from app.models.notification import Notification
from app.models.opportunity import Opportunity
from app.models.reference import (
    ActivityType,
    LeadSource,
    LossReason,
    PipelineStage,
    Role,
    Team,
)
from app.models.user import User
from app.models.workflow import (
    AssignmentRule,
    ScoringCriteria,
    ScoringRule,
    WorkflowExecutionLog,
    WorkflowRule,
)

__all__ = [
    "Account", "Contact", "Activity", "AuditLog", "RevokedToken", "Lead",
    "Opportunity", "ActivityType", "LeadSource", "LossReason", "PipelineStage",
    "Role", "Team", "User", "AssignmentRule", "ScoringCriteria", "ScoringRule",
    "Notification", "WorkflowRule", "WorkflowExecutionLog",
]
