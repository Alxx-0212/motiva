import os
from dotenv import load_dotenv, find_dotenv
import uuid
import enum
from datetime import datetime, timezone
import pytz
from pydantic import BaseModel, Field
from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey, func, select
from sqlalchemy.orm import relationship, mapped_column, Mapped
from sqlalchemy.dialects import postgresql
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_deepseek import ChatDeepSeek
from langchain_openai import ChatOpenAI, AzureChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import tool
from langchain.agents import create_openai_functions_agent, create_react_agent, Tool, AgentExecutor
from langchain.memory import ConversationBufferMemory
from langchain.tools.render import format_tool_to_openai_function
from langchain.agents.output_parsers import OpenAIFunctionsAgentOutputParser
from langchain.agents.format_scratchpad import format_to_openai_functions
from langchain.schema.agent import AgentFinish
from langchain.schema.runnable import RunnablePassthrough
from typing import Dict, Optional
import chainlit as cl
from chainlit.data.sql_alchemy import SQLAlchemyDataLayer
from chainlit.types import ThreadDict
from app.auth import verify_password
from app.models import User, Task, TaskPriority, TaskStatus
from app.db import AsyncSessionLocal, Session
from operator import itemgetter

from langchain_community.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema.output_parser import StrOutputParser
from langchain.schema.runnable import Runnable, RunnablePassthrough, RunnableLambda
from langchain.schema.runnable.config import RunnableConfig
from langchain.memory import ConversationBufferMemory

from chainlit.types import ThreadDict

load_dotenv(find_dotenv(), override=True)

# async def local_to_utc(local_dt, timezone_str):
#     """Convert local datetime to UTC."""
#     # Run the synchronous operations in a thread pool to avoid blocking
#     def _convert():
#         if not isinstance(local_dt, datetime):
#             raise ValueError("local_dt must be a datetime object")
        
#         # Get timezone object
#         local_tz = pytz.timezone(timezone_str)
        
#         if local_dt.tzinfo is None:
#             localized_dt = local_tz.localize(local_dt)
#         else:
#             localized_dt = local_dt
        
#         # Convert to UTC
#         return localized_dt.astimezone(pytz.UTC)
    
#     # Execute in thread pool for non-blocking operation
#     return await asyncio.to_thread(_convert)

# async def utc_to_local(utc_dt, timezone_str):
#     """Convert UTC datetime to local timezone."""
#     # Run the synchronous operations in a thread pool to avoid blocking
#     def _convert():
#         if not isinstance(utc_dt, datetime):
#             raise ValueError("utc_dt must be a datetime object")

#         if utc_dt.tzinfo is None:
#             localized_utc = pytz.UTC.localize(utc_dt)
#         else:
#             localized_utc = utc_dt
        
#         # Get target timezone
#         local_tz = pytz.timezone(timezone_str)
        
#         # Convert to local timezone
#         return localized_utc.astimezone(local_tz)
    
#     # Execute in thread pool for non-blocking operation
#     return await asyncio.to_thread(_convert)

def local_to_utc(local_dt, timezone_str):
    """Convert local datetime to UTC."""
    if not isinstance(local_dt, datetime):
        raise ValueError("local_dt must be a datetime object")
    
    # Get timezone object
    local_tz = pytz.timezone(timezone_str)
    
    if local_dt.tzinfo is None:
        local_dt = local_tz.localize(local_dt)
    
    # Convert to UTC
    return local_dt.astimezone(pytz.UTC)

def utc_to_local(utc_dt, timezone_str):
    """Convert UTC datetime to local timezone."""
    if not isinstance(utc_dt, datetime):
        raise ValueError("utc_dt must be a datetime object")

    if utc_dt.tzinfo is None:
        utc_dt = pytz.UTC.localize(utc_dt)
    
    # Get target timezone
    local_tz = pytz.timezone(timezone_str)
    
    # Convert to local timezone
    return utc_dt.astimezone(local_tz)

class AddTaskInput(BaseModel):
    id: str = Field(..., description="ID of the user")
    task_name: str = Field(..., description="Name of the task")
    start_time_local: datetime = Field(..., description="Task start time")
    end_time_local: datetime = Field(..., description="Task end time")
    task_description: str = Field(None, description="Task description")

@tool("add_task", args_schema=AddTaskInput)
async def add_task(
    id: str,
    task_name: str,
    start_time_local: datetime,
    end_time_local: datetime,
    task_description: str = None) -> str:
    """
    Add a new task to the database.
    Returns: Success or error message indicating the result of the operation.
    """
    async with AsyncSessionLocal() as session:
        try:
            # fetch the user
            res = await session.execute(select(User).filter_by(id=id))
            user = res.scalars().first()
            
            if not user:
                return "User not found"

            if user.timezone != "UTC":
                start_utc = local_to_utc(start_time_local, user.timezone)
                end_utc = local_to_utc(end_time_local, user.timezone)
            else:
                start_utc, end_utc = start_time_local, end_time_local

            new_task = Task(
                task_name=task_name,
                task_description=task_description,
                user_id=id,
                start_time_utc=start_utc,
                end_time_utc=end_utc,
                original_timezone=user.timezone,
            )
            session.add(new_task)
            await session.commit()
            return f"Task '{task_name}' added successfully"
        except Exception as e:
            await session.rollback()
            return f"Error adding task: {e}"

class GetUserTasksInput(BaseModel):
    id: str = Field(..., description="ID of the user whose tasks to retrieve")
    start_date: datetime = Field(None, description="Filter tasks starting after this date")
    end_date: datetime = Field(None, description="Filter tasks ending before this date")

@tool("get_user_tasks", args_schema=GetUserTasksInput)
async def get_user_tasks(
    id : str, 
    start_date : datetime = None, 
    end_date : datetime = None) -> str:
    """
    Get user's tasks.
    Returns: String of user's tasks.
    """
    async with AsyncSessionLocal() as session:
        try:
            res = await session.execute(select(User).filter_by(id=id))
            user = res.scalars().first()
            if not user:
                return "User not found"

            stmt = select(Task).filter(Task.user_id == id)

            if start_date:
                start_utc = (local_to_utc(start_date, user.timezone) if user.timezone != "UTC" else start_date)
                stmt = stmt.filter(Task.start_time_utc >= start_utc)

            if end_date:
                end_utc = (local_to_utc(end_date, user.timezone) if user.timezone != "UTC" else end_date)
                stmt = stmt.filter(Task.end_time_utc <= end_utc)

            res = await session.execute(stmt)
            tasks = res.scalars().all()

            if not tasks:
                return "No tasks found"

            user_tasks = ["User tasks:\n"]
            for t in tasks:
                user_tasks.append(
                    f"- task_id: {t.task_id}\n"
                    f"  name: {t.task_name}\n"
                    f"  description: {t.task_description or '—'}\n"
                    f"  start: {utc_to_local(t.start_time_utc, user.timezone)}\n"
                    f"  end:   {utc_to_local(t.end_time_utc,   user.timezone)}\n"
                    f"  timezone: {user.timezone}\n"
                )
            return "\n".join(user_tasks)
        except Exception as e:
            return f"Error retrieving tasks: {e}"

class UpdateTaskInput(BaseModel):
    task_id: str = Field(..., description="ID of the task to update")
    task_name: str = Field(None, description="New name for the task")
    task_description: str = Field(None, description="New description for the task")
    start_time_local: datetime = Field(None, description="New start time")
    end_time_local: datetime = Field(None, description="New end time")

@tool("update_task", args_schema=UpdateTaskInput)
async def update_task(
    task_id: str,
    task_name: str = None,
    task_description: str = None,
    start_time_local: datetime = None,
    end_time_local: datetime = None) -> str:
    """
    Update an existing task.
    Returns: Success or error message indicating the result of the operation.
    """
    async with AsyncSessionLocal() as session:
        try:
            res = await session.execute(select(Task).filter_by(task_id=task_id))
            task = res.scalars().first()
            if not task:
                return "Task not found"

            res = await session.execute(select(User).filter_by(id=task.user_id))
            user = res.scalars().first()
            if not user:
                return "User not found"

            if task_name is not None:
                task.task_name = task_name

            if task_description is not None:
                task.task_description = task_description

            if start_time_local is not None:
                task.start_time_utc = (local_to_utc(start_time_local, user.timezone) if user.timezone != "UTC" else start_time_local)

            if end_time_local is not None:
                task.end_time_utc = (local_to_utc(end_time_local, user.timezone) if user.timezone != "UTC" else end_time_local)

            await session.commit()
            return f"Task '{task.task_name}' updated successfully"
        except Exception as e:
            await session.rollback()
            return f"Error updating task: {e}"

# class UpdateTaskInput(BaseModel):
#     message: str = Field(..., description="Message to ask user for confirmation")

# async def ask_user_for_confirmation(message : str):
    
#     res = await cl.AskActionMessage(
#         content = message,
#         actions = [
#             cl.Action(
#                 name="continue", payload={"value": "continue"}, label="✅ Continue"
#             ),
#             cl.Action(name="cancel", payload={"value": "cancel"}, label="❌ Cancel"),
#         ],
#     ).send()

#     if res and res.get("payload").get("value") == "continue":
#         await cl.Message(
#             content="Continue!",
#         ).send()
                
# Function to setup the runnable environment for the chat application
async def setup_runnable(user_id: str, user_timezone: str, date: str):

    memory = cl.user_session.get("memory")
    tools = [get_user_tasks, add_task, update_task]
    functions = [format_tool_to_openai_function(f) for f in tools]

    model = AzureChatOpenAI(
        azure_deployment="gpt-4",
        api_version="2024-12-01-preview",
        temperature=0
    ).bind(functions=functions)

    system_message = f"""
You are a highly organized, meticulous, and helpful AI assistant dedicated to managing personal tasks.
Your primary goal is to help the user effectively organize their tasks.

You have access to the following tools to interact with the task management system:
1. **`get_user_tasks(id: str, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None)`**:
    * **Description**: Retrieves the user's tasks, optionally filtered by start and end dates.
    * **Parameters**:
        * `id` (str): The unique identifier of the user whose tasks are being retrieved.
        * `start_date` (Optional[datetime]): If provided, only tasks starting after this date will be returned. You must parse this from the user's natural language input, considering the current date and time context.
        * `end_date` (Optional[datetime]): If provided, only tasks ending before this date will be returned. You must parse this from the user's natural language input, considering the current date and time context.
    * **Returns**: A string of user's tasks.

2.  **`add_task(user_id: str, task_name: str, start_time_local: datetime, end_time_local: datetime, task_description: Optional[str] = None)`**:
    * **Description**: Adds a new task to the user's personal task list.
    * **Parameters**:
        * `user_id` (str): The unique identifier of the user who owns this task.
        * `task_name` (str): A clear, concise name or title for the task.
        * `start_time_local` (datetime): The *local* start date and time of the task. You must parse this from the user's natural language input, considering the current date and time context.
        * `end_time_local` (datetime): The *local* end date and time of the task. You must parse this from the user's natural language input, considering the current date and time context.
        * `task_description` (Optional[str]): An optional, more detailed description of the task.
    * **Returns**: A confirmation message indicating the task was successfully added, or an error message if the operation failed.

3.  **`update_task(task_id: str, task_name: str, start_time_local: datetime, end_time_local: datetime, task_description: Optional[str] = None)`**:
    * **Description**: Updates an existing task in the user's personal task list.
    * **Parameters**:
        * `task_id` (str): The unique identifier of the task to be updated.
        * `task_name` (Optional[str]): A clear, concise name or title for the task.
        * `start_time_local` (Optional[datetime]): The start date and time of the task. You must parse this from the user's natural language input, considering the current date and time context.
        * `end_time_local` (Optional[datetime]): The end date and time of the task. You must parse this from the user's natural language input, considering the current date and time context.
        * `task_description` (Optional[str]): An optional, more detailed description of the task.
    * **Returns**: A confirmation message indicating the task was successfully updated, or an error message if the operation failed.
     
---

**CRITICAL PROTOCOL FOR TASK MODIFICATIONS (Creation or Update):**

To ensure user control and prevent unintended changes, you **MUST ALWAYS** follow this explicit approval process for **ANY** request that involves adding or modifying tasks:
1.  **Understand Current State**: Call `get_user_tasks()` to retrieve the user's current task list and then ask the user for their request. This gives you the context of what tasks currently exist and what the user is asking for.
2.  **Formulate Proposal**: Based on the user's request and the user current task list, clearly formulate how the created or updated task **would look** after the requested changes. This includes:
    * For new tasks: Show the new task details to the user.
    * For updated tasks: Show the task with its modified fields.
3.  **Present for Approval**: Present this *proposed future task list* (or the specific proposed changes in context) to the user in a clear, easy-to-read format (e.g., a bulleted list, a formatted table).
4.  **Seek Confirmation**: Explicitly ask the user for confirmation of these proposed changes. For example: "Here is how your task list would look after these changes. Does this look correct, or would you like to make any adjustments?" or "Please review the proposed tasks below and confirm if I should proceed."
5.  **Execute ONLY on Approval**: **ONLY after the user explicitly confirms and approves the proposed changes ONCE** (e.g., by saying "Yes," "Go ahead," "Confirm," "Looks good"), you are then authorized to call the `create_task` or `update_task` tool(s) accordingly.
6.  **Handle Ambiguity**: If the user's request is ambiguous or lacks necessary information for a task modification, ask clarifying questions before proposing any changes.

**CRITICAL TASK UPDATE PROTOCOL:**

Before Modifying Any Task, ALWAYS:
1. Verify Ownership and Authenticity
   - MANDATORY: Cross-check the provided task ID with the user's existing task list
   - CONFIRM the task ID belongs to the specific user requesting the modification
   - PREVENT unauthorized or incorrect task updates

Verification Steps:
- Retrieve current user task list
- Match provided task ID exactly
- If task ID cannot be verified, IMMEDIATELY halt the update process

Update Workflow:
- Task ID Verification ✓ → Proceed with Update
- Task ID Verification ✗ → Reject Update, Report Error

Error Handling:
- If task ID is invalid or not found, return a clear error message
- Do not make ANY modifications without explicit, verified authorization

Security Principle: 
"Verify First, Update Second" - ZERO exceptions to this rule.

Always prioritize user clarity and confirmation. Be concise and empathetic in your responses.

--- 

Here is some information about the user's current context:
- **Current Date:** {date}
- **User ID:** {user_id}
- **User Timezone:** {user_timezone}

Please use this information to provide contextually relevant and timely responses. 
For example, if asked about scheduling, consider their current day and time.
"""

    # Create the chat prompt template, the ordering of the placeholders is important, taken from: https://smith.langchain.com/hub/hwchase17/openai-tools-agent
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_message),
            MessagesPlaceholder(variable_name="chat_history"),
            ("user", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ]
    )

    agent_chain = RunnablePassthrough.assign(
        agent_scratchpad= lambda x: format_to_openai_functions(x["intermediate_steps"])
    ) | prompt | model | OpenAIFunctionsAgentOutputParser()

    agent_executor = AgentExecutor(agent=agent_chain, tools=tools, verbose=True, memory=memory)
 
    cl.user_session.set("agent_executor", agent_executor)

@cl.password_auth_callback
def authorize(email: str, password: str):
    session = Session()
    try:
        user = session.query(User).filter_by(email=email.lower()).first()
    
        if not user or not verify_password(password, user.hashed_password):
            raise cl.UnauthorizedError("Invalid credentials")
        
        return cl.User(
            identifier=str(user.id)
        )
    except Exception as e:
        cl.error(f"Error during authorization: {e}")
        raise cl.UnauthorizedError("Internal error")
    finally:
        session.close()

# @cl.oauth_callback
# def oauth_callback(
#   provider_id: str,
#   token: str,
#   raw_user_data: Dict[str, str],
#   default_user: cl.User,
# ) -> Optional[cl.User]:
#   return default_user

@cl.data_layer
def get_data_layer():
    return SQLAlchemyDataLayer(conninfo=os.getenv("ASYNC_CHAINLIT_DB_URL"))

@cl.on_chat_start
async def on_chat_start():
    cl.user_session.set("memory", ConversationBufferMemory(return_messages=True, memory_key="chat_history"))
    cl.user_session.set("current_thread", None)

    app_user = cl.user_session.get("user")
    user_id = app_user.identifier

    session = Session()
    try:
        user = session.query(User).filter_by(id=user_id).first()
        user_timezone = user.timezone if user else "UTC"
        username = user.username if user else "Guest"
    except Exception as e:
        cl.error(f"Error retrieving user data: {e}")
    finally:
        session.close()

    if user_timezone != "UTC":
        user_timezone = pytz.timezone(user_timezone) 
    else:
        user_timezone = pytz.utc

    utc_now = datetime.now(pytz.utc)
    user_time = utc_now.astimezone(user_timezone)
    current_date = user_time.strftime("%A %Y-%m-%d %I:%M:%S %p")

    await setup_runnable(date=current_date, user_id=user_id, user_timezone=user_timezone)

@cl.on_chat_resume
async def on_chat_resume(thread: ThreadDict):
    cl.user_session.set("current_thread", thread["id"])

    # Create a new ConversationSummaryBufferMemory with the specified parameters
    memory = ConversationBufferMemory(return_messages=True, memory_key="chat_history")

    # Retrieve the root messages from the thread
    root_messages = [m for m in thread["steps"] if m["parentId"] is None]
    # Iterate over the root messages
    for message in root_messages:
        # Check the type of the message
        if message["type"] == "USER_MESSAGE":
            # Add user message to the chat memory
            memory.chat_memory.add_user_message(message["output"])
        else:
            # Add AI message to the chat memory
            memory.chat_memory.add_ai_message(message["output"])

    # Call the setup_runnable function to continue the chat application
    cl.user_session.set("memory", memory)
    app_user = cl.user_session.get("user")
    user_id = app_user.identifier

    session = Session()
    try:
        user = session.query(User).filter_by(id=user_id).first()
        user_timezone = user.timezone if user else "UTC"
        username = user.username if user else "Guest"
    except Exception as e:
        cl.error(f"Error retrieving user data: {e}")
    finally:
        session.close()

    if user_timezone != "UTC":
        user_timezone = pytz.timezone(user_timezone) 
    else:
        user_timezone = pytz.utc

    utc_now = datetime.now(pytz.utc)
    user_time = utc_now.astimezone(user_timezone)
    current_date = user_time.strftime("%A %Y-%m-%d %I:%M:%S %p")
    await setup_runnable(date=current_date, user_id=user_id, user_timezone=user_timezone)

@cl.on_message
async def on_message(message: cl.Message):
    cl.user_session.set("current_thread", message.thread_id)
    
    # Get the agent executor from the user session
    agent_executor: AgentExecutor = cl.user_session.get("agent_executor")

    # Invoke the agent with the user message as input
    try:
        result = await agent_executor.ainvoke(
            {"input": message.content},
            {"callbacks": [cl.AsyncLangchainCallbackHandler()]},
        )
        output = result.get("output") if isinstance(result, dict) else str(result)
        await cl.Message(
            author="assistant",
            content=output,
        ).send()
    except Exception as e:
        await cl.Message(
            author="system",
            content="An error occurred while processing the message. Please try again.",
        ).send()

    # await cl.Message(response['output']).send()

    # memory = cl.user_session.get("memory")  # type: ConversationBufferMemory

    # runnable = cl.user_session.get("runnable")  # type: Runnable

    # res = cl.Message(content="")

    # async for chunk in runnable.astream(
    #     {"question": message.content},
    #     config=RunnableConfig(callbacks=[cl.LangchainCallbackHandler()]),
    # ):
    #     await res.stream_token(chunk)

    # await res.send()

    # memory.chat_memory.add_user_message(message.content)
    # memory.chat_memory.add_ai_message(res.content)