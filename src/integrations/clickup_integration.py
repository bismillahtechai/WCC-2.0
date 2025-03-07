import requests
import os
import logging
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class ClickUpIntegration:
    """
    Integration with ClickUp API for construction management.
    Provides methods to interact with ClickUp for project and task management.
    """
    
    def __init__(self):
        """
        Initialize the ClickUp integration with API credentials.
        """
        self.api_token = os.getenv("CLICKUP_API_KEY")
        self.workspace_id = os.getenv("CLICKUP_WORKSPACE_ID")
        self.base_url = "https://api.clickup.com/api/v2"
        
        if not self.api_token or not self.workspace_id:
            logger.error("ClickUp API credentials not found in environment variables")
            raise ValueError("ClickUp API credentials not found. Please set CLICKUP_API_KEY and CLICKUP_WORKSPACE_ID environment variables.")
        
        logger.info("ClickUp integration initialized")
    
    def get_headers(self) -> Dict[str, str]:
        """
        Get the HTTP headers for ClickUp API requests.
        
        Returns:
            Dict[str, str]: HTTP headers with authentication
        """
        return {
            "Authorization": self.api_token,
            "Content-Type": "application/json"
        }
    
    def get_spaces(self) -> List[Dict[str, Any]]:
        """
        Get all spaces in the ClickUp workspace.
        
        Returns:
            List[Dict[str, Any]]: List of spaces
        """
        url = f"{self.base_url}/team/{self.workspace_id}/space"
        
        response = requests.get(url, headers=self.get_headers())
        response.raise_for_status()
        
        return response.json()["spaces"]
    
    def get_space_id(self) -> str:
        """
        Get the construction space ID.
        
        Returns:
            str: Construction space ID
        """
        spaces = self.get_spaces()
        
        # Look for a space with "construction" in the name
        construction_space = None
        for space in spaces:
            if "construction" in space["name"].lower():
                construction_space = space
                break
        
        # If no construction space found, use the first space
        if not construction_space and spaces:
            construction_space = spaces[0]
            logger.warning(f"No construction space found. Using the first space: {construction_space['name']}")
        
        if not construction_space:
            logger.error("No spaces found in the workspace")
            raise ValueError("No spaces found in the ClickUp workspace.")
        
        return construction_space["id"]
    
    def create_space(self, name: str, description: str = "") -> Dict[str, Any]:
        """
        Create a new space in the ClickUp workspace.
        
        Args:
            name (str): Space name
            description (str, optional): Space description
            
        Returns:
            Dict[str, Any]: Created space data
        """
        url = f"{self.base_url}/team/{self.workspace_id}/space"
        
        payload = {
            "name": name,
            "description": description
        }
        
        response = requests.post(url, headers=self.get_headers(), json=payload)
        response.raise_for_status()
        
        return response.json()
    
    def get_folders(self, space_id: str) -> List[Dict[str, Any]]:
        """
        Get all folders in a space.
        
        Args:
            space_id (str): Space ID
            
        Returns:
            List[Dict[str, Any]]: List of folders
        """
        url = f"{self.base_url}/space/{space_id}/folder"
        
        response = requests.get(url, headers=self.get_headers())
        response.raise_for_status()
        
        return response.json()["folders"]
    
    def get_folder(self, folder_id: str) -> Dict[str, Any]:
        """
        Get a specific folder by ID.
        
        Args:
            folder_id (str): Folder ID
            
        Returns:
            Dict[str, Any]: Folder data
        """
        url = f"{self.base_url}/folder/{folder_id}"
        
        response = requests.get(url, headers=self.get_headers())
        response.raise_for_status()
        
        return response.json()
    
    def create_folder(self, name: str, space_id: str, description: str = "") -> Dict[str, Any]:
        """
        Create a new folder in a space.
        
        Args:
            name (str): Folder name
            space_id (str): Space ID
            description (str, optional): Folder description
            
        Returns:
            Dict[str, Any]: Created folder data
        """
        url = f"{self.base_url}/space/{space_id}/folder"
        
        payload = {
            "name": name,
            "description": description
        }
        
        response = requests.post(url, headers=self.get_headers(), json=payload)
        response.raise_for_status()
        
        return response.json()
    
    def get_lists(self, folder_id: str) -> List[Dict[str, Any]]:
        """
        Get all lists in a folder.
        
        Args:
            folder_id (str): Folder ID
            
        Returns:
            List[Dict[str, Any]]: List of lists
        """
        url = f"{self.base_url}/folder/{folder_id}/list"
        
        response = requests.get(url, headers=self.get_headers())
        response.raise_for_status()
        
        return response.json()["lists"]
    
    def create_list(self, name: str, folder_id: str, description: str = "") -> Dict[str, Any]:
        """
        Create a new list in a folder.
        
        Args:
            name (str): List name
            folder_id (str): Folder ID
            description (str, optional): List description
            
        Returns:
            Dict[str, Any]: Created list data
        """
        url = f"{self.base_url}/folder/{folder_id}/list"
        
        payload = {
            "name": name,
            "description": description
        }
        
        response = requests.post(url, headers=self.get_headers(), json=payload)
        response.raise_for_status()
        
        return response.json()
    
    def get_tasks(self, list_id: str) -> List[Dict[str, Any]]:
        """
        Get all tasks in a list.
        
        Args:
            list_id (str): List ID
            
        Returns:
            List[Dict[str, Any]]: List of tasks
        """
        url = f"{self.base_url}/list/{list_id}/task"
        
        response = requests.get(url, headers=self.get_headers())
        response.raise_for_status()
        
        return response.json()["tasks"]
    
    def create_task(
        self,
        name: str,
        list_id: str,
        description: str = "",
        due_date: Optional[int] = None,
        assignees: Optional[List[str]] = None,
        priority: Optional[int] = None,
        dependencies: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Create a new task in a list.
        
        Args:
            name (str): Task name
            list_id (str): List ID
            description (str, optional): Task description
            due_date (int, optional): Due date timestamp (milliseconds)
            assignees (List[str], optional): List of assignee user IDs
            priority (int, optional): Priority (1-4, where 1 is urgent)
            dependencies (List[str], optional): List of task IDs this task depends on
            
        Returns:
            Dict[str, Any]: Created task data
        """
        url = f"{self.base_url}/list/{list_id}/task"
        
        payload = {
            "name": name,
            "description": description
        }
        
        if due_date:
            payload["due_date"] = due_date
        
        if assignees:
            payload["assignees"] = assignees
        
        if priority:
            payload["priority"] = priority
        
        response = requests.post(url, headers=self.get_headers(), json=payload)
        response.raise_for_status()
        task_id = response.json()["id"]
        
        # Add dependencies if provided
        if dependencies and task_id:
            for dep_id in dependencies:
                self.create_dependency(task_id, dep_id)
        
        return response.json()
    
    def update_task(
        self,
        task_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        status: Optional[str] = None,
        due_date: Optional[int] = None,
        priority: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Update a task.
        
        Args:
            task_id (str): Task ID
            name (str, optional): New task name
            description (str, optional): New task description
            status (str, optional): New task status
            due_date (int, optional): New due date timestamp (milliseconds)
            priority (int, optional): New priority (1-4, where 1 is urgent)
            
        Returns:
            Dict[str, Any]: Updated task data
        """
        url = f"{self.base_url}/task/{task_id}"
        
        payload = {}
        
        if name:
            payload["name"] = name
        
        if description:
            payload["description"] = description
        
        if status:
            payload["status"] = status
        
        if due_date:
            payload["due_date"] = due_date
        
        if priority:
            payload["priority"] = priority
        
        response = requests.put(url, headers=self.get_headers(), json=payload)
        response.raise_for_status()
        
        return response.json()
    
    def create_dependency(self, task_id: str, depends_on_id: str) -> Dict[str, Any]:
        """
        Create a dependency between tasks.
        
        Args:
            task_id (str): Dependent task ID
            depends_on_id (str): Task ID that task_id depends on
            
        Returns:
            Dict[str, Any]: Response data
        """
        url = f"{self.base_url}/task/{task_id}/dependency"
        
        payload = {
            "depends_on": depends_on_id
        }
        
        response = requests.post(url, headers=self.get_headers(), json=payload)
        response.raise_for_status()
        
        return response.json()
    
    def create_custom_field(
        self,
        list_id: str,
        name: str,
        type: str,
        value: Any = None
    ) -> Dict[str, Any]:
        """
        Create a custom field for a list.
        
        Args:
            list_id (str): List ID
            name (str): Field name
            type (str): Field type (text, number, date, currency, etc.)
            value (Any, optional): Default value
            
        Returns:
            Dict[str, Any]: Created custom field data
        """
        url = f"{self.base_url}/list/{list_id}/field"
        
        payload = {
            "name": name,
            "type": type
        }
        
        if value is not None:
            payload["value"] = value
        
        response = requests.post(url, headers=self.get_headers(), json=payload)
        response.raise_for_status()
        
        return response.json()
    
    def get_task_comments(self, task_id: str) -> List[Dict[str, Any]]:
        """
        Get all comments for a task.
        
        Args:
            task_id (str): Task ID
            
        Returns:
            List[Dict[str, Any]]: List of comments
        """
        url = f"{self.base_url}/task/{task_id}/comment"
        
        response = requests.get(url, headers=self.get_headers())
        response.raise_for_status()
        
        return response.json()["comments"]
    
    def create_task_comment(self, task_id: str, comment_text: str) -> Dict[str, Any]:
        """
        Create a comment on a task.
        
        Args:
            task_id (str): Task ID
            comment_text (str): Comment text
            
        Returns:
            Dict[str, Any]: Created comment data
        """
        url = f"{self.base_url}/task/{task_id}/comment"
        
        payload = {
            "comment_text": comment_text
        }
        
        response = requests.post(url, headers=self.get_headers(), json=payload)
        response.raise_for_status()
        
        return response.json()
    
    def get_task_time_tracking(self, task_id: str) -> List[Dict[str, Any]]:
        """
        Get time tracking entries for a task.
        
        Args:
            task_id (str): Task ID
            
        Returns:
            List[Dict[str, Any]]: List of time tracking entries
        """
        url = f"{self.base_url}/task/{task_id}/time"
        
        response = requests.get(url, headers=self.get_headers())
        response.raise_for_status()
        
        return response.json()["data"]
    
    def create_task_time_entry(
        self,
        task_id: str,
        duration: int,
        description: str = ""
    ) -> Dict[str, Any]:
        """
        Create a time tracking entry for a task.
        
        Args:
            task_id (str): Task ID
            duration (int): Duration in milliseconds
            description (str, optional): Time entry description
            
        Returns:
            Dict[str, Any]: Created time entry data
        """
        url = f"{self.base_url}/task/{task_id}/time"
        
        payload = {
            "duration": duration,
            "description": description
        }
        
        response = requests.post(url, headers=self.get_headers(), json=payload)
        response.raise_for_status()
        
        return response.json()
    
    def get_tags(self) -> List[Dict[str, Any]]:
        """
        Get all tags in the workspace.
        
        Returns:
            List[Dict[str, Any]]: List of tags
        """
        url = f"{self.base_url}/space/{self.get_space_id()}/tag"
        
        response = requests.get(url, headers=self.get_headers())
        response.raise_for_status()
        
        return response.json()["tags"]
    
    def create_tag(self, name: str, color: str = "#000000") -> Dict[str, Any]:
        """
        Create a new tag in the workspace.
        
        Args:
            name (str): Tag name
            color (str, optional): Tag color in hex format
            
        Returns:
            Dict[str, Any]: Created tag data
        """
        url = f"{self.base_url}/space/{self.get_space_id()}/tag"
        
        payload = {
            "name": name,
            "tag_bg": color
        }
        
        response = requests.post(url, headers=self.get_headers(), json=payload)
        response.raise_for_status()
        
        return response.json() 