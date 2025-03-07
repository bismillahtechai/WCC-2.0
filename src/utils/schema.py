from pydantic import BaseModel, Field, validator, root_validator
from typing import List, Dict, Any, Optional
from datetime import datetime
import re

class TaskCreate(BaseModel):
    """
    Model for creating a task.
    """
    name: str = Field(..., description="Task name")
    description: Optional[str] = Field(None, description="Task description")
    project_id: str = Field(..., description="Project ID (folder ID in ClickUp)")
    due_date: Optional[int] = Field(None, description="Due date timestamp (milliseconds)")
    assignees: Optional[List[str]] = Field(None, description="List of assignee user IDs")
    priority: Optional[int] = Field(None, description="Priority (1-4, where 1 is urgent)")
    dependencies: Optional[List[str]] = Field(None, description="List of task IDs this task depends on")
    
    @validator('name')
    def name_must_not_be_empty(cls, v):
        if not v.strip():
            raise ValueError('Task name cannot be empty')
        return v
    
    @validator('priority')
    def priority_must_be_valid(cls, v):
        if v is not None and v not in [1, 2, 3, 4]:
            raise ValueError('Priority must be between 1 and 4')
        return v

class ProjectCreate(BaseModel):
    """
    Model for creating a project.
    """
    name: str = Field(..., description="Project name")
    description: Optional[str] = Field(None, description="Project description")
    due_date: Optional[int] = Field(None, description="Project due date timestamp (milliseconds)")
    budget: Optional[float] = Field(None, description="Project budget")
    client: Optional[str] = Field(None, description="Client name")
    location: Optional[str] = Field(None, description="Project location")
    
    @validator('name')
    def name_must_not_be_empty(cls, v):
        if not v.strip():
            raise ValueError('Project name cannot be empty')
        return v
    
    @validator('budget')
    def budget_must_be_positive(cls, v):
        if v is not None and v <= 0:
            raise ValueError('Budget must be positive')
        return v

class TaskUpdate(BaseModel):
    """
    Model for updating a task.
    """
    task_id: str = Field(..., description="Task ID")
    name: Optional[str] = Field(None, description="New task name")
    description: Optional[str] = Field(None, description="New task description")
    status: Optional[str] = Field(None, description="New task status")
    due_date: Optional[int] = Field(None, description="New due date timestamp (milliseconds)")
    priority: Optional[int] = Field(None, description="New priority (1-4, where 1 is urgent)")
    
    @validator('name')
    def name_must_not_be_empty(cls, v):
        if v is not None and not v.strip():
            raise ValueError('Task name cannot be empty')
        return v
    
    @validator('priority')
    def priority_must_be_valid(cls, v):
        if v is not None and v not in [1, 2, 3, 4]:
            raise ValueError('Priority must be between 1 and 4')
        return v
    
    @root_validator
    def at_least_one_field(cls, values):
        non_id_fields = {k: v for k, v in values.items() if k != 'task_id' and v is not None}
        if not non_id_fields:
            raise ValueError('At least one field to update must be provided')
        return values

class TimeEntryCreate(BaseModel):
    """
    Model for creating a time tracking entry.
    """
    task_id: str = Field(..., description="Task ID")
    duration: int = Field(..., description="Duration in milliseconds")
    description: Optional[str] = Field(None, description="Time entry description")
    
    @validator('duration')
    def duration_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError('Duration must be positive')
        return v

class InvoiceCreate(BaseModel):
    """
    Model for creating an invoice.
    """
    project_id: str = Field(..., description="Project ID")
    client_id: str = Field(..., description="Client ID")
    amount: float = Field(..., description="Invoice amount")
    issue_date: int = Field(..., description="Issue date timestamp (milliseconds)")
    due_date: int = Field(..., description="Due date timestamp (milliseconds)")
    items: List[Dict[str, Any]] = Field(..., description="Invoice line items")
    
    @validator('amount')
    def amount_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError('Invoice amount must be positive')
        return v
    
    @validator('due_date')
    def due_date_must_be_after_issue_date(cls, v, values):
        issue_date = values.get('issue_date')
        if issue_date is not None and v < issue_date:
            raise ValueError('Due date must be after issue date')
        return v
    
    @validator('items')
    def items_must_not_be_empty(cls, v):
        if not v:
            raise ValueError('Invoice must have at least one item')
        return v

class ClientCreate(BaseModel):
    """
    Model for creating a client.
    """
    name: str = Field(..., description="Client name")
    email: Optional[str] = Field(None, description="Client email")
    phone: Optional[str] = Field(None, description="Client phone number")
    address: Optional[str] = Field(None, description="Client address")
    
    @validator('name')
    def name_must_not_be_empty(cls, v):
        if not v.strip():
            raise ValueError('Client name cannot be empty')
        return v
    
    @validator('email')
    def email_must_be_valid(cls, v):
        if v is not None:
            email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
            if not re.match(email_regex, v):
                raise ValueError('Invalid email format')
        return v
    
    @validator('phone')
    def phone_must_be_valid(cls, v):
        if v is not None:
            # Remove non-numeric characters for validation
            digits = re.sub(r'\D', '', v)
            if len(digits) < 10:
                raise ValueError('Phone number must have at least 10 digits')
        return v 