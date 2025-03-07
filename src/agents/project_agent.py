from langchain.agents import Tool
from typing import List
import logging
import json
from .base_agent import BaseAgent
from ..integrations.clickup_integration import ClickUpIntegration

logger = logging.getLogger(__name__)

class ProjectAgent(BaseAgent):
    """
    Project Management Agent responsible for managing construction projects,
    tasks, timelines, resources, and critical paths.
    """
    
    def __init__(self):
        """
        Initialize the Project Management Agent with ClickUp integration.
        """
        # Initialize ClickUp integration
        self.clickup = ClickUpIntegration()
        
        # Initialize base agent
        super().__init__(
            name="Project Management",
            description="construction project management, task tracking, timelines, and resource allocation"
        )
    
    def _get_tools(self) -> List[Tool]:
        """
        Get the tools for the Project Management Agent.
        
        Returns:
            List[Tool]: List of tools for the agent
        """
        tools = [
            Tool(
                name="Create Project",
                func=self._create_project,
                description="Create a new construction project with specified parameters"
            ),
            Tool(
                name="Create Task",
                func=self._create_task,
                description="Create a new task within a project"
            ),
            Tool(
                name="Get Project Status",
                func=self._get_project_status,
                description="Get the current status of a project"
            ),
            Tool(
                name="Update Task",
                func=self._update_task,
                description="Update the status, priority, or details of a task"
            ),
            Tool(
                name="Get Critical Path",
                func=self._get_critical_path,
                description="Identify the critical path of tasks for a project"
            ),
            Tool(
                name="List Projects",
                func=self._list_projects,
                description="List all active construction projects"
            ),
        ]
        
        return tools
    
    def _create_project(self, params_str: str) -> str:
        """
        Create a new construction project in ClickUp.
        
        Args:
            params_str (str): JSON string with project parameters
                - name: Project name
                - description: Project description
                - due_date: Project due date (timestamp)
                - budget: Project budget
                - client: Client name
                - location: Project location
                
        Returns:
            str: Response indicating success or failure
        """
        try:
            # Parse parameters
            params = json.loads(params_str)
            
            required_params = ["name"]
            for param in required_params:
                if param not in params:
                    return f"Missing required parameter: {param}"
            
            # Create project (folder) in ClickUp
            result = self.clickup.create_folder(
                name=params["name"],
                description=params.get("description", ""),
                space_id=self.clickup.get_space_id()  # Get the space ID from configuration
            )
            
            # Create custom fields for project metadata
            if "budget" in params:
                self.clickup.create_custom_field(
                    list_id=result["id"],
                    name="Budget",
                    type="currency",
                    value=params["budget"]
                )
            
            if "client" in params:
                self.clickup.create_custom_field(
                    list_id=result["id"],
                    name="Client",
                    type="text",
                    value=params["client"]
                )
                
            if "location" in params:
                self.clickup.create_custom_field(
                    list_id=result["id"],
                    name="Location",
                    type="text",
                    value=params["location"]
                )
            
            return f"Successfully created project: {params['name']} with ID: {result['id']}"
        
        except Exception as e:
            logger.error(f"Error creating project: {str(e)}")
            return f"Error creating project: {str(e)}"
    
    def _create_task(self, params_str: str) -> str:
        """
        Create a new task within a project in ClickUp.
        
        Args:
            params_str (str): JSON string with task parameters
                - name: Task name
                - description: Task description
                - project_id: Project ID (folder ID in ClickUp)
                - due_date: Task due date (timestamp)
                - assignees: List of assignee user IDs
                - priority: Priority (1-4, where 1 is urgent)
                - dependencies: List of task IDs this task depends on
                
        Returns:
            str: Response indicating success or failure
        """
        try:
            # Parse parameters
            params = json.loads(params_str)
            
            required_params = ["name", "project_id"]
            for param in required_params:
                if param not in params:
                    return f"Missing required parameter: {param}"
            
            # Create task in ClickUp
            result = self.clickup.create_task(
                name=params["name"],
                description=params.get("description", ""),
                list_id=params["project_id"],
                due_date=params.get("due_date"),
                assignees=params.get("assignees", []),
                priority=params.get("priority"),
                dependencies=params.get("dependencies", [])
            )
            
            return f"Successfully created task: {params['name']} with ID: {result['id']}"
        
        except Exception as e:
            logger.error(f"Error creating task: {str(e)}")
            return f"Error creating task: {str(e)}"
    
    def _get_project_status(self, project_id: str) -> str:
        """
        Get the current status of a project from ClickUp.
        
        Args:
            project_id (str): The project ID (folder ID in ClickUp)
            
        Returns:
            str: Project status summary
        """
        try:
            # Get folder data
            folder_data = self.clickup.get_folder(folder_id=project_id)
            
            # Get lists in folder
            lists = self.clickup.get_lists(folder_id=project_id)
            
            # Get tasks in folder
            tasks = []
            for list_item in lists:
                list_tasks = self.clickup.get_tasks(list_id=list_item["id"])
                tasks.extend(list_tasks)
            
            # Calculate statistics
            total_tasks = len(tasks)
            completed_tasks = sum(1 for task in tasks if task["status"]["status"] == "complete")
            progress = (completed_tasks / total_tasks) * 100 if total_tasks > 0 else 0
            
            # Get status by task categories
            status_counts = {}
            for task in tasks:
                status = task["status"]["status"]
                if status in status_counts:
                    status_counts[status] += 1
                else:
                    status_counts[status] = 1
            
            # Format response
            response = f"Project: {folder_data['name']}\n"
            response += f"Progress: {progress:.1f}% ({completed_tasks}/{total_tasks} tasks completed)\n"
            response += "Status Breakdown:\n"
            for status, count in status_counts.items():
                response += f"- {status}: {count} tasks\n"
            
            return response
        
        except Exception as e:
            logger.error(f"Error getting project status: {str(e)}")
            return f"Error getting project status: {str(e)}"
    
    def _update_task(self, params_str: str) -> str:
        """
        Update a task in ClickUp.
        
        Args:
            params_str (str): JSON string with task update parameters
                - task_id: Task ID
                - name: New task name (optional)
                - description: New task description (optional)
                - status: New task status (optional)
                - due_date: New due date (timestamp, optional)
                - priority: New priority (1-4, optional)
                
        Returns:
            str: Response indicating success or failure
        """
        try:
            # Parse parameters
            params = json.loads(params_str)
            
            if "task_id" not in params:
                return "Missing required parameter: task_id"
            
            # Update task in ClickUp
            result = self.clickup.update_task(
                task_id=params["task_id"],
                name=params.get("name"),
                description=params.get("description"),
                status=params.get("status"),
                due_date=params.get("due_date"),
                priority=params.get("priority")
            )
            
            return f"Successfully updated task: {result['name']}"
        
        except Exception as e:
            logger.error(f"Error updating task: {str(e)}")
            return f"Error updating task: {str(e)}"
    
    def _get_critical_path(self, project_id: str) -> str:
        """
        Identify the critical path of tasks for a project.
        
        Args:
            project_id (str): The project ID (folder ID in ClickUp)
            
        Returns:
            str: Critical path of tasks
        """
        try:
            # Get lists in folder
            lists = self.clickup.get_lists(folder_id=project_id)
            
            # Get tasks in folder
            tasks = []
            for list_item in lists:
                list_tasks = self.clickup.get_tasks(list_id=list_item["id"])
                tasks.extend(list_tasks)
            
            # Build dependency graph
            dependency_graph = {}
            task_durations = {}
            task_names = {}
            
            # Initialize graph
            for task in tasks:
                task_id = task["id"]
                dependency_graph[task_id] = []
                
                # Calculate task duration
                start_date = task.get("start_date")
                due_date = task.get("due_date")
                
                if start_date and due_date:
                    duration_ms = due_date - start_date
                    duration_days = duration_ms / (1000 * 60 * 60 * 24)
                    task_durations[task_id] = max(1, round(duration_days))
                else:
                    task_durations[task_id] = 1  # Default to 1 day if no dates
                
                task_names[task_id] = task["name"]
            
            # Fill dependencies
            for task in tasks:
                task_id = task["id"]
                if "dependencies" in task and task["dependencies"]:
                    for dep in task["dependencies"]:
                        if dep in dependency_graph:
                            dependency_graph[dep].append(task_id)
            
            # Find tasks with no dependencies (starting tasks)
            start_tasks = []
            for task_id in dependency_graph:
                has_dependencies = any(task_id in deps for deps in dependency_graph.values())
                if not has_dependencies:
                    start_tasks.append(task_id)
            
            # Calculate earliest completion times
            earliest_completion = {}
            for task_id in dependency_graph:
                earliest_completion[task_id] = 0
            
            # Topological sort and calculate earliest completion times
            visited = set()
            
            def dfs(task_id):
                if task_id in visited:
                    return
                
                visited.add(task_id)
                
                # Process dependencies
                for dep_task_id in dependency_graph[task_id]:
                    dfs(dep_task_id)
                    earliest_completion[dep_task_id] = max(
                        earliest_completion[dep_task_id],
                        earliest_completion[task_id] + task_durations[task_id]
                    )
            
            # Start DFS from all starting tasks
            for start_task in start_tasks:
                dfs(start_task)
            
            # Find the latest tasks (no outgoing edges)
            end_tasks = []
            for task_id in dependency_graph:
                if not dependency_graph[task_id]:
                    end_tasks.append(task_id)
            
            # Find the project completion time
            project_completion_time = max(earliest_completion[task_id] + task_durations[task_id] for task_id in end_tasks)
            
            # Calculate latest start times
            latest_start = {}
            for task_id in dependency_graph:
                latest_start[task_id] = project_completion_time
            
            # Backward pass to calculate latest start times
            def backward_dfs(task_id):
                for dep_task_id in [tid for tid, deps in dependency_graph.items() if task_id in deps]:
                    latest_start[dep_task_id] = min(
                        latest_start[dep_task_id],
                        latest_start[task_id] - task_durations[dep_task_id]
                    )
                    backward_dfs(dep_task_id)
            
            # Start backward DFS from all ending tasks
            for end_task in end_tasks:
                backward_dfs(end_task)
            
            # Find critical path (tasks with zero slack)
            critical_path = []
            for task_id in dependency_graph:
                slack = latest_start[task_id] - earliest_completion[task_id]
                if slack == 0:
                    critical_path.append(task_id)
            
            # Format response
            response = "Critical Path Analysis:\n"
            response += f"Project Duration: {project_completion_time} days\n"
            response += "Critical Path Tasks:\n"
            
            for task_id in critical_path:
                response += f"- {task_names[task_id]} (Duration: {task_durations[task_id]} days)\n"
            
            response += "\nThese tasks must be completed on time to avoid project delays."
            
            return response
        
        except Exception as e:
            logger.error(f"Error calculating critical path: {str(e)}")
            return f"Error calculating critical path: {str(e)}"
    
    def _list_projects(self) -> str:
        """
        List all active construction projects from ClickUp.
        
        Returns:
            str: List of projects with basic details
        """
        try:
            # Get all spaces
            spaces = self.clickup.get_spaces()
            
            # Get construction space
            construction_space = None
            for space in spaces:
                if "construction" in space["name"].lower():
                    construction_space = space
                    break
            
            if not construction_space:
                return "No construction space found in ClickUp."
            
            # Get folders (projects) in the space
            folders = self.clickup.get_folders(space_id=construction_space["id"])
            
            if not folders:
                return "No projects found in the construction space."
            
            # Format response
            response = "Active Construction Projects:\n"
            
            for i, folder in enumerate(folders, 1):
                folder_id = folder["id"]
                
                # Get tasks statistics
                lists = self.clickup.get_lists(folder_id=folder_id)
                
                total_tasks = 0
                completed_tasks = 0
                
                for list_item in lists:
                    list_tasks = self.clickup.get_tasks(list_id=list_item["id"])
                    total_tasks += len(list_tasks)
                    completed_tasks += sum(1 for task in list_tasks if task["status"]["status"] == "complete")
                
                progress = (completed_tasks / total_tasks) * 100 if total_tasks > 0 else 0
                
                response += f"{i}. {folder['name']}\n"
                response += f"   ID: {folder_id}\n"
                response += f"   Progress: {progress:.1f}% ({completed_tasks}/{total_tasks} tasks)\n"
                
                # Check for custom fields
                custom_fields = folder.get("custom_fields", [])
                for field in custom_fields:
                    if field["name"] == "Budget":
                        response += f"   Budget: ${field['value']}\n"
                    elif field["name"] == "Client":
                        response += f"   Client: {field['value']}\n"
                    elif field["name"] == "Location":
                        response += f"   Location: {field['value']}\n"
                
                response += "\n"
            
            return response
        
        except Exception as e:
            logger.error(f"Error listing projects: {str(e)}")
            return f"Error listing projects: {str(e)}" 