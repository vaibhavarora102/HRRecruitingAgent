from ast import List
from typing import TypedDict, Literal, Optional
from langgraph.graph import StateGraph, START, END
from llmUtils import JobListing, CerebrasUtils 
from IPython.display import Image, display
from langchain_core.tools import tool
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_cerebras import ChatCerebras
from langchain.prompts import ChatPromptTemplate
from supabase import create_client, Client
from dbModels.job_model import Job
from dbModels.application_model import Application

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
    candidate_selected: Optional[bool]
    offer_letter: Optional[str]
    offer_letter_specifications: Optional[str]
    offer_letter_approved: Optional[bool]
    offer_sent: Optional[bool]
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
    
    def create_job(self, job: Job) -> Job:
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
        response = self.supabase.table("applications").select("resume_url").eq("id", job_id).execute()
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

    
    def make_jd(self, state):
        suggestion = state.get('jd_suggestions', '')
        if suggestion == "":
            print("*"*45)
            print(f"Entering JD creation for First Time")
            state['jd'] = self.cerebras_utils.create_job_description(state['position'])
            print(f"Generated JD: {state['jd']}")
            print("*"*45)
        else:
            print("*"*45)
            print(f"Entering JD modification with suggestions: {suggestion}")
            state['jd'] = self.cerebras_utils.change_job_description(state['jd'], suggestion)
            print(f"Modified JD: {state['jd']}")
            print("*"*45)
        jd = state['jd']
        return {"jd": jd, "jd_suggestions": suggestion, "status": "jd_created"}

    @staticmethod
    def jd_suggestions(state):
        suggestions = "Include experience with Python and AI."
        print(f"JD suggestions: {suggestions}")
        return {"jd_suggestions": suggestions}

    @staticmethod
    def approve_jd(state):
        is_approved = True  # Hardcoded for demonstration
        print(f"JD to approve: {state['jd']}")
        return {"jd_approved": is_approved, "status": "jd_approved"}

    
    def create_job_posting_data(self, state):
        job_post_json = self.cerebras_utils.create_post_listing_data(state['jd'])
        print(f"Created Job Posting Data: {job_post_json}")
        return {"job_post_json": job_post_json}

    def post_job(self, state):
        print("*"*45)   
        job_post_json = json.loads(state['job_post_json'])
        job = Job.from_dict(job_post_json)        
        state['job'] = self.create_job(job)
        print(f"Posted Job Listing Data")
        print("*"*45)
        return {"job_posted": True, "status": "job_posted"}

    @staticmethod
    def check_application_threshold_node(state):
        threshold = 5
        current_app_count = 6
        print(f"Application threshold set to: {threshold}. Current count: {current_app_count}")
        return {
            'application_threshhold': threshold,
            'current_number_of_application': current_app_count
        }

    def tweak_job_post(self, state): 
        print("Since we are not getting enough applications, tweaking the Job Posting slightly.")
        new_posting = self.cerebras_utils.tweak_job_description(state['jd'], state['job_post_json'])
        print(f"Tweaked Job Posting Data: {new_posting}")
        return {"job_post_json": new_posting}

    @staticmethod
    def review_resume(state):
        print("Reviewed resumes. Moving to selection.")
        return {"resume_reviewed": True, "status": "resume_reviewed"}

    @staticmethod
    def schedule_interview(state):
        print("Scheduled interviews.")
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

    @staticmethod
    def create_offer_letter(state):
        offer = f"Offer letter for position {state['position']}. Details: {state['offer_letter_specifications']}"
        print(f"Created offer letter: {offer}")
        return {"offer_letter": offer}

    @staticmethod
    def approve_offer_letter(state):
        is_approved = True
        print(f"Offer letter approved: {is_approved}")
        return {"offer_letter_approved": is_approved}

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
            prompt_str = "Draft an email to aroravaibhav102@gmail.com sending him offer letter for the position {position} and this job description {jd} and complete the Hiring process.".format(
                position=state.get('position', ''),
                jd=state.get('jd', '')
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
        if state.get('jd_approved'):
            return "create_job_posting_data"
        else:
            return "jd_suggestions"

    @staticmethod
    def route_on_threshold(state: HRRecruitingState) -> str:
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
        if state.get('offer_letter_approved'):
            return "send_offer"
        else:
            return "ask_for_offer_letter_specifications"

    def _build_graph(self):
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
        graphBuilder.add_edge("review_resume", "schedule_interview")
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
        graphBuilder.add_edge("send_offer", "gmail_agent")
        # graphBuilder.add_edge("gmail_agent", "tools")
        graphBuilder.add_conditional_edges("gmail_agent", tools_condition)
        graphBuilder.add_edge("tools", "gmail_agent")
        graphBuilder.add_edge("gmail_agent", END)
        return graphBuilder.compile()

    def draw_grapy(self, save_path: str = "graph.png"):
        img_bytes = self.graph.get_graph().draw_mermaid_png()
        with open(save_path, "wb") as f:
            f.write(img_bytes)
        print(f"Graph image saved to {save_path}")
    def run(self, initial_state: dict):
        return self.graph.invoke(initial_state)
    
    def print_graph_mermaid(self):
        print(self.graph.get_graph().draw_mermaid_text())
    


# ...existing code...

if __name__ == "__main__":
    hr_graph = HRRecruitingGraph()
    # hr_graph.draw_grapy()
    result = hr_graph.run({"position": "Software Engineer"})

    # print(result)

