from ast import List
from typing import TypedDict, Literal, Optional
from langgraph.graph import StateGraph, START, END
from IPython.display import Image, display
from langchain_core.tools import tool
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_cerebras import ChatCerebras
from langchain.prompts import ChatPromptTemplate
from supabase import create_client, Client
from langgraph.types import interrupt, Command
from langgraph.checkpoint.memory import MemorySaver
import streamlit as st
import time
from langsmith import traceable


# from llmUtils import JobListing, CerebrasUtils 
# from llm_rag import PDFRAGPipeline, CandidateSummary
# from dbModels.job_model import Job
# from dbModels.application_model import Application

from HrAssistantAgent.llmUtils import JobListing, CerebrasUtils 
from HrAssistantAgent.dbModels.job_model import Job
from HrAssistantAgent.dbModels.application_model import Application
from HrAssistantAgent.llm_rag import PDFRAGPipeline, CandidateSummary

import os
import smtplib
import json

class HRRecruitingState(TypedDict):
    position: str
    jd: Optional[str]
    jd_approved: Optional[bool]
    jd_suggestions: Optional[str]
    job_posted: Optional[bool]
    job_post_json: Optional[JobListing]
    job: Optional[Job]
    resume_reviewed: Optional[bool]
    application_threshhold: Optional[int]
    current_number_of_application: Optional[int]
    schedule_interview: Optional[bool]
    candidate_selected: Optional[bool]
    offer_letter: Optional[str]
    offer_letter_specifications: Optional[str]
    offer_letter_approved: Optional[bool]
    offer_sent: Optional[bool]
    selected_candidate_data : Optional[CandidateSummary]
    is_running: Optional[bool]
    email_status: Optional[str]
    messages: Optional[list[str]]
    status: Optional[Literal[
        "received_position", "jd_created", "jd_approved", "job_posted", "resume_reviewed", "offer_sent"
    ]]

class HRRecruitingGraph:
    def __init__(self):
        self.tools = [self.send_mail]
        self.graph = self._build_graph()
        self.cerebras_utils = CerebrasUtils()
        SUPABASE_URL = "https://jntavmoxtjnflnrsbulo.supabase.co"
        SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImpudGF2bW94dGpuZmxucnNidWxvIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTk0MzMyMzgsImV4cCI6MjA3NTAwOTIzOH0.QLOeL26EOGnLSSfvfod9JWcWqHqegX-GlPV-FqTcj5M"
        self.supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    def create_job(self, job: Job, state) -> Job:
        """
        Creates a job in the database.
        Args:
            job (Job): Job to create.

        Returns:
            Job: Created job.
        """
        response = self.supabase.table("jobs").insert(job.to_dict()).execute()
        if response.data and len(response.data) > 0:
            return Job.from_dict(response.data[0])
        else:
            raise Exception("Failed to create job: No data returned")
        
    def get_resume_paths_by_job_id(self, job_id: int):
        """
        Gets the resume paths by job id.
        Args:
            job_id (int): Job id.

        Returns:
            List[str]: List of resume paths.
        """
        response = self.supabase.table("applications").select("resume_url").eq("job_id", job_id).execute()
        return response.data
        
    def update_job(self, job: Job) -> Job:
        """
        Updates a job in the database.
        Args:
            job (Job): Job to update.
        Returns:
            Job: Updated job.
        """
        if(job.id == None):
            raise Exception("Failed to update: Job id is null")
        response = self.supabase.table("jobs").update(job.to_dict()).eq("id", job.id).execute()
        if response.data and len(response.data) > 0:
            return Job.from_dict(response.data[0])
        else:
            raise Exception("Failed to update job: No data returned")

    @tool
    def send_mail(subject: str, body: str, receiver_email: str):
        """
        Sends an email using Gmail's SMTP server.

        Args:
            subject (str): Subject of the email.
            body (str): Body content of the email.
            receiver_email (str): Recipient's email address.

        Returns:
            None. Prints success or error message.
        """
        print("#"*45)
        print(f"Preparing to send email to {receiver_email} with subject '{subject}'")
        print("#"*45)
        try:
            sender_email = os.environ["EMAIL_USER"]
            sender_password = os.environ["EMAIL_PASSWORD"]
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(sender_email, sender_password)
            message = f'Subject: {subject}\n\n{body}'
            server.sendmail(sender_email, receiver_email, message)
            server.quit()
            print(f"Email sent to {receiver_email}")
            return "mail successfully sent"
        except Exception as e:
            print(f"Failed to send email: {e}")
        return "mail sending failed"

    # Node functions
    @staticmethod
    def get_position(state):
        print(f"--- Received position: {state['position']} ---")
        return {"status": "received_position"}

    
    def make_jd(self, state, log_callback=None):
        suggestion = state.get('jd_suggestions', '')
        msg = f"Creating/Modifying JD for position: {state['position']} with suggestions: {suggestion}"
        if suggestion == "":
            print("*"*45)
            print(f"Entering JD creation for First Time")
            state['jd'] = self.cerebras_utils.create_job_description(state['position'])
            # st.markdown(f"Generated JD: {state['jd']}")
            print("*"*45)
            if log_callback:
                log_callback("make_jd", msg)
                state['jd'] = self.cerebras_utils.create_job_description(state['position'])
    
        else:
            print("*"*45)
            print(f"Entering JD modification with suggestions: {suggestion}")
            state['jd'] = self.cerebras_utils.change_job_description(state['jd'], suggestion)
            print(f"Modified JD: {state['jd']}")
            print("*"*45)
            if log_callback:
                log_callback("make_jd", msg)
                state['jd'] = self.cerebras_utils.change_job_description(state['jd'], suggestion)
    
        jd = state['jd']
        return {"jd": jd, "jd_suggestions": suggestion, "status": "jd_created"}

    @staticmethod
    def jd_suggestions(state):
        suggestions = "Include experience with Python and AI."
        print(f"JD suggestions: {suggestions}")
        return {"jd_suggestions": suggestions}

    @staticmethod
    def approve_jd(state):
        # The key 'jd_approval_decision' will be set when the graph is resumed
        decision = interrupt("Waiting for JD approval ('yes' or 'no').")

        # Graph resumed with a decision. Process it.
        if decision == "yes":
            state["jd_approved"] = True
        else:
            state["jd_approved"] = False
        print(f"JD approval decision received: {decision}")

        # Clear the decision from state for the next graph run, if applicable
        # This dictionary is what the graph expects as the node's output.
        return {"status": "jd_approved", "jd_approved": state["jd_approved"]}
    
    def create_job_posting_data(self, state):
        job_post_json = self.cerebras_utils.create_post_listing_data(state['jd'])
        print(f"Created Job Posting Data: {job_post_json}")
        return {"job_post_json": job_post_json}

    def post_job(self, state):
        print("in post job node")
        print("*"*45)   
        job_post_json = json.loads(state['job_post_json'])
        job = Job.from_dict(job_post_json)        
        state['job'] = self.create_job(job, state=state)  # Save created job to state
        print("*"*45)
        print("sleeeeeeeeping . . . ...")
        time.sleep(100) 
        print("sleeeeeeeeping over . . . ...")
        return {"job_posted": True, "status": "job_posted", "job": state['job']}
        

    @staticmethod
    def check_application_threshold_node(state):
        print("Checking application threshold...")
        threshold = 5
        current_app_count = 6
        print(f"Application threshold set to: {threshold}. Current count: {current_app_count}")
        return {
            'application_threshhold': threshold,
            'current_number_of_application': current_app_count
        }

    def tweak_job_post(self, state): 
        print("in tweak job post node")
        print("Since we are not getting enough applications, tweaking the Job Posting slightly.")
        new_posting = self.cerebras_utils.tweak_job_description(state['jd'], state['job_post_json'])
        print(f"Tweaked Job Posting Data: {new_posting}")
        return {"job_post_json": new_posting}

    
    def review_resume(self, state):
        print("Reviewing resumes...")
        print("*"*45)
        print(f"Fetching resumes for Job ID: {state['job'].id}")
        Resume = self.get_resume_paths_by_job_id(state['job'].id)
        print(f"Resumes found: {Resume}")
        # Initialize RAG pipeline
        rag = PDFRAGPipeline()
        candidate_summary = rag.full_run(Resume, state['jd'])
        state['selected_candidate_data'] = candidate_summary


        decision = interrupt("should we Proceed with interview? (yes/no)")

        if decision == "yes":
            state["schedule_interview"] = True
        else:
            state["schedule_interview"] = False
        
        print("*"*45)
        print("Reviewed resumes. Moving to selection.")
        return {"resume_reviewed": True, "status": "resume_reviewed", "selected_candidate_data": state['selected_candidate_data'], "schedule_interview": state["schedule_interview"]}

    @staticmethod
    def schedule_interview(state):
        print("Scheduled interviews. . . . ")
        return {"interviews_scheduled": True}

    @staticmethod
    def candidate_selection(state):
        print("Selected candidates for interview.")
        state['candidate_selected'] = True  # Ensure state is updated
        return {"candidate_selected": True}

    @staticmethod
    def ask_for_offer_letter_specifications(state):
        specs = "Standard offer letter with salary details (USD 120k)."
        print(f"Offer letter specifications: {specs}")
        return {"offer_letter_specifications": specs}

    
    def create_offer_letter(self, state):
        suggestion = state.get('jd_suggestions', 'salary to be 30LPA CTC including 2 Lankh bonus, benefits to be health insurance')
        # msg = f"Creating/Modifying JD for position: {state['position']} with suggestions: {suggestion}"
        
            
        
        print("*"*45)
        print(f"Generating offer Letter with suggestions: {suggestion}")
        state['offer'] = self.cerebras_utils.generate_offer_letter(
            candidate_name=state['selected_candidate_data'].name if state['selected_candidate_data'] and 'name' in state['selected_candidate_data'] else "Candidate",
            position=state['position'],
            details=suggestion
        )
        print(f"Modified JD: {state['jd']}")
        print("*"*45)
            
        jd = state['jd']
        # return {"jd": jd, "jd_suggestions": suggestion, "status": "jd_created"}
        return {"offer_letter": state['offer']}

    @staticmethod
    def approve_jd(state):
        # The key 'jd_approval_decision' will be set when the graph is resumed
        decision = interrupt("Waiting for JD approval ('yes' or 'no').")

        # Graph resumed with a decision. Process it.
        if decision == "yes":
            state["jd_approved"] = True
        else:
            state["jd_approved"] = False
        print(f"JD approval decision received: {decision}")

        # Clear the decision from state for the next graph run, if applicable
        # This dictionary is what the graph expects as the node's output.
        return {"status": "jd_approved", "jd_approved": state["jd_approved"]}
    @staticmethod
    def approve_offer_letter(state):
        decision = interrupt("Waiting for Offer Letter approval ('yes' or 'no').")
        
        # Graph resumed with a decision. Process it.
        if decision == "yes":
            state["offer_letter_approved"] = True
        else:
            state["offer_letter_approved"] = False
        print(f"JD approval decision received: {decision}")
        print(f"Offer letter approved: state['offer_letter_approved']")
        return {"offer_letter_approved": state['offer_letter_approved']}

    @staticmethod
    def send_offer(state):
        print(f"--- Sent offer letter for {state['position']} ---")
        return {"offer_sent": True, "status": "offer_sent"}

    def gmail_agent(self, state):
        tool_model = ChatCerebras(model="llama-4-scout-17b-16e-instruct")
        llm_with_tools = tool_model.bind_tools(self.tools)

        # Use the last user message as input
        messages = state.get("messages", [])
        if not messages:
            # Fallback to default prompt if no messages
            prompt_str = "Draft an email to {candidate} \n sending him offer letter for the position {position} and this job description {jd} and complete the Hiring process.".format(
                position=state.get('position', ''),
                jd=state.get('jd', ''),
                candidate=state['selected_candidate_data']
            )
            messages = [{"role": "user", "content": prompt_str}]
        
        # Pass messages to the LLM
        response = llm_with_tools.invoke(messages)
        print("Gmail agent result:", response)

        # Append the LLM response to the messages list
        state = dict(state)
        state["messages"] = messages + [response]
        return state


    # Router functions
    @staticmethod
    def route_jd_approval(state: HRRecruitingState) -> str:
        print(f"Routing based on JD approval: {state['jd_approved']}")
        if state["jd_approved"]:
            return "create_job_posting_data"
        else:
            return "jd_suggestions"

        
    @staticmethod
    def route_interview_schedule(state: HRRecruitingState) -> str:
        print(f"Routing based on interview scheduling decision: {state['schedule_interview']}")
        if state["schedule_interview"]:
            return "schedule_interview"
        else:
            return "tweak_job_post"

    @staticmethod
    def route_on_threshold(state: HRRecruitingState) -> str:
        print("Checking application threshold for routing...")
        current_count = state.get('current_number_of_application', 0)
        threshold = state.get('application_threshhold', 0)
        if current_count >= threshold:
            print("--- Router: Threshold MET. Reviewing. ---")
            return "review_resume"
        else:
            print("--- Router: Threshold NOT MET. Tweaking. ---")
            return "tweak_job_post"

    @staticmethod
    def route_candidate_selection(state: HRRecruitingState) -> str:
        selection_successful = state["candidate_selected"]
        if selection_successful:
            return "ask_for_offer_letter_specifications"
        else:
            return END

    @staticmethod
    def route_offer_approval(state: HRRecruitingState) -> str:

        if state['offer_letter_approved']:
            return "send_offer"
        else:
            return "ask_for_offer_letter_specifications"

    def _build_graph(self):
        memory = MemorySaver()
        graphBuilder = StateGraph(HRRecruitingState)
        # Add Nodes
        graphBuilder.add_node("get_position", self.get_position)
        graphBuilder.add_node("make_jd", self.make_jd)
        graphBuilder.add_node("approve_jd", self.approve_jd)
        graphBuilder.add_node("jd_suggestions", self.jd_suggestions)
        graphBuilder.add_node("create_job_posting_data", self.create_job_posting_data)
        graphBuilder.add_node("post_job", self.post_job)
        graphBuilder.add_node("tweak_job_post", self.tweak_job_post)
        graphBuilder.add_node("review_resume", self.review_resume)
        graphBuilder.add_node("schedule_interview", self.schedule_interview)
        graphBuilder.add_node("candidate_selection", self.candidate_selection)
        graphBuilder.add_node("ask_for_offer_letter_specifications", self.ask_for_offer_letter_specifications)
        graphBuilder.add_node("create_offer_letter", self.create_offer_letter)
        graphBuilder.add_node("approve_offer_letter", self.approve_offer_letter)
        graphBuilder.add_node("gmail_agent", self.gmail_agent)
        graphBuilder.add_node("tools", ToolNode(self.tools))
        graphBuilder.add_node("send_offer", self.send_offer)
        graphBuilder.add_node("check_application_threshold", self.check_application_threshold_node)

        # Edges
        graphBuilder.add_edge(START, "get_position")
        graphBuilder.add_edge("get_position", "make_jd")
        graphBuilder.add_edge("make_jd", "approve_jd")
        graphBuilder.add_conditional_edges(
            "approve_jd",
            self.route_jd_approval,
            {
                "create_job_posting_data": "create_job_posting_data",
                "jd_suggestions": "jd_suggestions"
            }
        )
        graphBuilder.add_edge("create_job_posting_data", "post_job")
        graphBuilder.add_edge("jd_suggestions", "make_jd")
        graphBuilder.add_conditional_edges(
            "check_application_threshold",
            self.route_on_threshold,
            {
                "review_resume": "review_resume",
                "tweak_job_post": "tweak_job_post"
            }
        )
        graphBuilder.add_edge("tweak_job_post", "post_job")
        graphBuilder.add_edge("post_job", "check_application_threshold")
        # graphBuilder.add_edge("check_application_threshold", "review_resume")
        graphBuilder.add_conditional_edges(
            "review_resume",
            self.route_interview_schedule,
            {
                "schedule_interview": "schedule_interview",
                "tweak_job_post": "tweak_job_post"
            }
        )
        # graphBuilder.add_edge("review_resume", "schedule_interview")
        graphBuilder.add_edge("schedule_interview", "candidate_selection")
        graphBuilder.add_conditional_edges(
            "candidate_selection",
            self.route_candidate_selection,
            {
                "ask_for_offer_letter_specifications": "ask_for_offer_letter_specifications",
                END: END,
            }
        )
        graphBuilder.add_edge("ask_for_offer_letter_specifications", "create_offer_letter")
        graphBuilder.add_edge("create_offer_letter", "approve_offer_letter")
        graphBuilder.add_conditional_edges(
            "approve_offer_letter",
            self.route_offer_approval,
            {
                "send_offer": "send_offer",
                "ask_for_offer_letter_specifications": "ask_for_offer_letter_specifications",
            }
        )
        # graphBuilder.add_edge("send_offer", END)
        graphBuilder.add_edge("send_offer", "gmail_agent")
        # graphBuilder.add_edge("gmail_agent", "tools")
        graphBuilder.add_conditional_edges("gmail_agent", tools_condition)
        graphBuilder.add_edge("tools", END)
        graphBuilder.add_edge("gmail_agent", END)
        
        return graphBuilder.compile(checkpointer=memory)

    def draw_grapy(self, save_path: str = "graph.png"):
        img_bytes = self.graph.get_graph().draw_mermaid_png()
        with open(save_path, "wb") as f:
            f.write(img_bytes)
        print(f"Graph image saved to {save_path}")

    def get_interruption_node_name(interruption_value):
        """Safely extracts the node name from the complex interruption value."""
        # 1. Handle the simplest case (which is what .stream() often provides)
        if isinstance(interruption_value, str):
            return interruption_value
        
        # 2. Handle the case where the value is a list/tuple (common in .invoke() final result)
        if isinstance(interruption_value, (list, tuple)):
            # If it's a tuple from a previous fix, take the first element
            interruption_value = interruption_value[0]
            
        
        
        interrupt_str = str(interruption_value)
        if 'Job Description' in interrupt_str:
            return 'approve_jd'
        if 'Offer Letter' in interrupt_str:
            return 'approve_offer_letter'

        # Fallback to a placeholder if we can't parse it
        return 'unknown_approval_node'
    
    @traceable
    def run(self, input_data): # Use a generic type for input_data
        thread_id = "demo-thread-1"
        # The invoke method handles whether input_data is a dict (new run) or a Command (resume)
        return self.graph.invoke(input_data, config={"configurable": {"thread_id": thread_id}})
    

    def print_graph_mermaid(self):
        print(self.graph.get_graph().draw_mermaid_text())
    


# ... (existing code and HRRecruitingGraph class definition) ...

if __name__ == "__main__":
    hr_graph = HRRecruitingGraph()
    initial_state = {"position": "Testing Expert"}
    thread_id = "demo-thread-1" 
    
    print("--- Starting Graph Execution ---")
    
    # Start the first run
    hr_graph.draw_grapy()
    current_result = hr_graph.run(initial_state)
    print("\n--- Initial Run Result ---")

    # The main loop to handle interruptions
    while '__interrupt__' in current_result:
        # The key '__interrupt__' often contains the name of the node that interrupted
        interruption_node = current_result['__interrupt__'] 
        print(f"\n--- Graph Interrupted at '{interruption_node}'. Resuming with approval. ---")
        
        # --- Handle Specific Interruption Logic ---
        if interruption_node == 'approve_jd':
            prompt = "Approve Job Description (yes/no): "
        elif interruption_node == 'approve_offer': # Assuming a node named 'approve_offer'
            prompt = "Approve Offer Letter (yes/no): "
        else:
            # Fallback for unexpected interruptions
            prompt = f"Approve action for '{interruption_node}' (yes/no): "

        # Get the user input
        decision = input(prompt)
        print(f"User decision: {decision}")
        # The 'resume' argument is the positional argument for the state update, 
        # which is what the next node will process.
        approval_command = Command(resume=decision) 
        
        # 2. Call graph.invoke with the Command object to continue execution
        print(f"\n--- Resuming Graph execution from '{interruption_node}' with decision: '{decision}' ---")
        current_result = hr_graph.graph.invoke(
            approval_command, 
            config={"configurable": {"thread_id": thread_id}}
        )
        print("\n--- Run Result after Resume ---")
        print(current_result)
        