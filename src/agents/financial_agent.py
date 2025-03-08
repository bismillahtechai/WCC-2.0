from langchain.agents import Tool
from typing import List, Dict, Any, Optional
import logging
import json
import datetime
import uuid
from decimal import Decimal

from .base_agent import BaseAgent
from ..memory.vector_store import VectorStoreFactory
from ..utils.schema import FinancialTransaction, Budget, ProjectFinancials

logger = logging.getLogger(__name__)

class FinancialAgent(BaseAgent):
    """
    Financial Management Agent responsible for tracking budgets, expenses,
    invoices, and financial reporting for construction projects.
    """
    
    def __init__(self):
        """
        Initialize the Financial Management Agent.
        """
        # Initialize base agent
        super().__init__(
            name="Financial Management",
            description="financial planning, budgeting, expense tracking, invoice management, and financial reporting for construction projects"
        )
        
        # Initialize vector store for financial document search
        self.vector_store = VectorStoreFactory.create_vector_store()
        
        logger.info("Financial Management Agent initialized")
    
    def _get_tools(self) -> List[Tool]:
        """
        Get the tools for the Financial Management Agent.
        
        Returns:
            List[Tool]: List of tools for the agent
        """
        tools = [
            Tool(
                name="Create Budget",
                func=self._create_budget,
                description="Create a new budget for a project"
            ),
            Tool(
                name="Update Budget",
                func=self._update_budget,
                description="Update an existing project budget"
            ),
            Tool(
                name="Get Budget",
                func=self._get_budget,
                description="Get budget information for a project"
            ),
            Tool(
                name="Record Transaction",
                func=self._record_transaction,
                description="Record a financial transaction (expense or income)"
            ),
            Tool(
                name="Generate Financial Report",
                func=self._generate_financial_report,
                description="Generate a financial report for a project"
            ),
            Tool(
                name="Process Invoice",
                func=self._process_invoice,
                description="Process an invoice for payment"
            ),
            Tool(
                name="Get Project Finances",
                func=self._get_project_finances,
                description="Get complete financial information for a project"
            )
        ]
        return tools
        
    def _create_budget(self, budget_json: str) -> str:
        """
        Create a new budget for a project.
        
        Args:
            budget_json: JSON string with budget information
            
        Returns:
            JSON string with budget creation results
        """
        try:
            # Parse the budget information
            budget_dict = json.loads(budget_json)
            
            # Generate a budget ID if not provided
            if "budget_id" not in budget_dict:
                budget_dict["budget_id"] = str(uuid.uuid4())
                
            # Set created timestamp if not provided
            if "created_at" not in budget_dict:
                budget_dict["created_at"] = datetime.datetime.now().isoformat()
                
            # Validate budget with Pydantic model
            budget = Budget(**budget_dict)
            
            # Store in memory
            self.mem0.add_memory(
                text=f"Budget for project '{budget.project_id}' created with total amount {budget.total_amount}",
                category="finances",
                metadata={
                    "type": "budget",
                    "budget_id": budget.budget_id,
                    "project_id": budget.project_id,
                    "total_amount": float(budget.total_amount),
                    "categories": budget.categories
                }
            )
            
            # Return success response
            return json.dumps({
                "success": True,
                "budget_id": budget.budget_id,
                "project_id": budget.project_id,
                "message": f"Budget created for project {budget.project_id}"
            })
            
        except Exception as e:
            logger.error(f"Error creating budget: {str(e)}")
            return json.dumps({
                "success": False,
                "error": str(e)
            })
            
    def _update_budget(self, budget_update_json: str) -> str:
        """
        Update an existing project budget.
        
        Args:
            budget_update_json: JSON string with budget update information
            
        Returns:
            JSON string with budget update results
        """
        try:
            # Parse the budget update information
            update_dict = json.loads(budget_update_json)
            
            # Ensure budget_id is provided
            if "budget_id" not in update_dict:
                return json.dumps({
                    "success": False,
                    "error": "Budget ID is required for updates"
                })
                
            budget_id = update_dict["budget_id"]
            
            # Get existing budget from memory
            existing_budgets = self.mem0.search(
                query=f"budget_id:{budget_id}",
                category="finances",
                limit=1
            )
            
            if not existing_budgets:
                return json.dumps({
                    "success": False,
                    "error": f"Budget not found with ID: {budget_id}"
                })
                
            # Get existing budget data
            existing_budget = existing_budgets[0].get("metadata", {})
            
            # Update the budget with new values
            for key, value in update_dict.items():
                if key != "budget_id":
                    existing_budget[key] = value
                    
            # Add updated timestamp
            existing_budget["updated_at"] = datetime.datetime.now().isoformat()
            
            # Store updated budget in memory
            self.mem0.add_memory(
                text=f"Budget for project '{existing_budget.get('project_id')}' updated with total amount {existing_budget.get('total_amount')}",
                category="finances",
                metadata={
                    "type": "budget",
                    "budget_id": budget_id,
                    **existing_budget
                }
            )
            
            # Return success response
            return json.dumps({
                "success": True,
                "budget_id": budget_id,
                "message": "Budget updated successfully"
            })
            
        except Exception as e:
            logger.error(f"Error updating budget: {str(e)}")
            return json.dumps({
                "success": False,
                "error": str(e)
            })
            
    def _get_budget(self, project_id: str) -> str:
        """
        Get budget information for a project.
        
        Args:
            project_id: ID of the project
            
        Returns:
            JSON string with budget information
        """
        try:
            # Search for budget in memory
            budgets = self.mem0.search(
                query=f"project_id:{project_id} type:budget",
                category="finances",
                limit=10,
                sort_by_time=True
            )
            
            if not budgets:
                return json.dumps({
                    "success": False,
                    "error": f"No budget found for project: {project_id}"
                })
                
            # Get the most recent budget (should be first in the list)
            budget = budgets[0].get("metadata", {})
            
            # Return success response
            return json.dumps({
                "success": True,
                "budget": budget
            })
            
        except Exception as e:
            logger.error(f"Error getting budget: {str(e)}")
            return json.dumps({
                "success": False,
                "error": str(e)
            })
            
    def _record_transaction(self, transaction_json: str) -> str:
        """
        Record a financial transaction (expense or income).
        
        Args:
            transaction_json: JSON string with transaction information
            
        Returns:
            JSON string with transaction recording results
        """
        try:
            # Parse the transaction information
            transaction_dict = json.loads(transaction_json)
            
            # Generate a transaction ID if not provided
            if "transaction_id" not in transaction_dict:
                transaction_dict["transaction_id"] = str(uuid.uuid4())
                
            # Set transaction timestamp if not provided
            if "timestamp" not in transaction_dict:
                transaction_dict["timestamp"] = datetime.datetime.now().isoformat()
                
            # Validate transaction with Pydantic model
            transaction = FinancialTransaction(**transaction_dict)
            
            # Store in memory
            self.mem0.add_memory(
                text=f"Financial transaction recorded: {transaction.amount} for {transaction.description}",
                category="finances",
                metadata={
                    "type": "transaction",
                    "transaction_id": transaction.transaction_id,
                    "project_id": transaction.project_id,
                    "amount": float(transaction.amount),
                    "transaction_type": transaction.transaction_type,
                    "category": transaction.category,
                    "description": transaction.description,
                    "timestamp": transaction.timestamp
                }
            )
            
            # Return success response
            return json.dumps({
                "success": True,
                "transaction_id": transaction.transaction_id,
                "message": "Transaction recorded successfully"
            })
            
        except Exception as e:
            logger.error(f"Error recording transaction: {str(e)}")
            return json.dumps({
                "success": False,
                "error": str(e)
            })
            
    def _generate_financial_report(self, report_request_json: str) -> str:
        """
        Generate a financial report for a project.
        
        Args:
            report_request_json: JSON string with report request information
            
        Returns:
            JSON string with financial report
        """
        try:
            # Parse the report request
            request = json.loads(report_request_json)
            
            # Ensure project_id is provided
            if "project_id" not in request:
                return json.dumps({
                    "success": False,
                    "error": "Project ID is required for financial reports"
                })
                
            project_id = request["project_id"]
            
            # Get project finances
            finances = self._get_project_finances_data(project_id)
            
            if not finances.get("budget"):
                return json.dumps({
                    "success": False,
                    "error": f"No budget found for project: {project_id}"
                })
                
            # Generate report based on finances
            budget = finances["budget"]
            transactions = finances["transactions"]
            
            # Calculate totals
            total_expenses = sum(float(t["amount"]) for t in transactions 
                              if t.get("transaction_type") == "expense")
            total_income = sum(float(t["amount"]) for t in transactions 
                            if t.get("transaction_type") == "income")
            balance = total_income - total_expenses
            budget_remaining = float(budget.get("total_amount", 0)) - total_expenses
            
            # Calculate category breakdown
            categories = {}
            for transaction in transactions:
                category = transaction.get("category", "Uncategorized")
                if category not in categories:
                    categories[category] = 0
                    
                amount = float(transaction.get("amount", 0))
                if transaction.get("transaction_type") == "expense":
                    categories[category] += amount
                    
            # Create report
            report = {
                "project_id": project_id,
                "report_date": datetime.datetime.now().isoformat(),
                "total_budget": float(budget.get("total_amount", 0)),
                "total_expenses": total_expenses,
                "total_income": total_income,
                "balance": balance,
                "budget_remaining": budget_remaining,
                "budget_utilization_percentage": (total_expenses / float(budget.get("total_amount", 1))) * 100,
                "expense_by_category": categories,
                "transaction_count": len(transactions)
            }
            
            # Store report in memory
            self.mem0.add_memory(
                text=f"Financial report generated for project {project_id}",
                category="finances",
                metadata={
                    "type": "financial_report",
                    "project_id": project_id,
                    "report": report
                }
            )
            
            # Return success response
            return json.dumps({
                "success": True,
                "report": report
            })
            
        except Exception as e:
            logger.error(f"Error generating financial report: {str(e)}")
            return json.dumps({
                "success": False,
                "error": str(e)
            })
            
    def _process_invoice(self, invoice_json: str) -> str:
        """
        Process an invoice for payment.
        
        Args:
            invoice_json: JSON string with invoice information
            
        Returns:
            JSON string with invoice processing results
        """
        try:
            # Parse the invoice information
            invoice = json.loads(invoice_json)
            
            # Ensure required fields are present
            required_fields = ["project_id", "amount", "vendor", "invoice_number"]
            for field in required_fields:
                if field not in invoice:
                    return json.dumps({
                        "success": False,
                        "error": f"Missing required field: {field}"
                    })
                    
            # Generate invoice ID if not provided
            if "invoice_id" not in invoice:
                invoice["invoice_id"] = str(uuid.uuid4())
                
            # Set invoice date if not provided
            if "invoice_date" not in invoice:
                invoice["invoice_date"] = datetime.datetime.now().isoformat()
                
            # Set status to pending if not provided
            if "status" not in invoice:
                invoice["status"] = "pending"
                
            # Store in memory
            self.mem0.add_memory(
                text=f"Invoice {invoice['invoice_number']} from {invoice['vendor']} processed for ${invoice['amount']}",
                category="finances",
                metadata={
                    "type": "invoice",
                    **invoice
                }
            )
            
            # Also record as a transaction if invoice is approved
            if invoice.get("status") == "approved":
                transaction = {
                    "transaction_id": str(uuid.uuid4()),
                    "project_id": invoice["project_id"],
                    "amount": invoice["amount"],
                    "transaction_type": "expense",
                    "category": invoice.get("category", "Vendor Payment"),
                    "description": f"Payment for invoice {invoice['invoice_number']} to {invoice['vendor']}",
                    "timestamp": datetime.datetime.now().isoformat(),
                    "reference": invoice["invoice_id"]
                }
                
                self._record_transaction(json.dumps(transaction))
                
            # Return success response
            return json.dumps({
                "success": True,
                "invoice_id": invoice["invoice_id"],
                "message": f"Invoice {invoice['invoice_number']} processed successfully"
            })
            
        except Exception as e:
            logger.error(f"Error processing invoice: {str(e)}")
            return json.dumps({
                "success": False,
                "error": str(e)
            })
            
    def _get_project_finances(self, project_id: str) -> str:
        """
        Get complete financial information for a project.
        
        Args:
            project_id: ID of the project
            
        Returns:
            JSON string with project financial information
        """
        try:
            # Get project finances data
            finances = self._get_project_finances_data(project_id)
            
            # Return success response
            return json.dumps({
                "success": True,
                "finances": finances
            })
            
        except Exception as e:
            logger.error(f"Error getting project finances: {str(e)}")
            return json.dumps({
                "success": False,
                "error": str(e)
            })
            
    def _get_project_finances_data(self, project_id: str) -> Dict[str, Any]:
        """
        Helper method to get project finances data.
        
        Args:
            project_id: ID of the project
            
        Returns:
            Dictionary with project finances data
        """
        # Get budget
        budgets = self.mem0.search(
            query=f"project_id:{project_id} type:budget",
            category="finances",
            limit=1,
            sort_by_time=True
        )
        
        budget = budgets[0].get("metadata", {}) if budgets else None
        
        # Get transactions
        transaction_memories = self.mem0.search(
            query=f"project_id:{project_id} type:transaction",
            category="finances",
            limit=100,
            sort_by_time=True
        )
        
        transactions = [memory.get("metadata", {}) for memory in transaction_memories]
        
        # Get invoices
        invoice_memories = self.mem0.search(
            query=f"project_id:{project_id} type:invoice",
            category="finances",
            limit=100,
            sort_by_time=True
        )
        
        invoices = [memory.get("metadata", {}) for memory in invoice_memories]
        
        # Combine into finances object
        finances = {
            "project_id": project_id,
            "budget": budget,
            "transactions": transactions,
            "invoices": invoices
        }
        
        return finances 