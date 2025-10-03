from typing import TypedDict, Literal, Optional
from langgraph.graph import StateGraph, START, END
from llmUtils import JobListing, CerebrasUtils 
from IPython.display import Image, display

class HRRecruitingState(TypedDict):
    position: str
    jd: Optional[str]
    jd_approved: Optional[bool]
    jd_suggestions: Optional[str]
    job_posted: Optional[bool]
    job_post_json: Optional[JobListing]
    resume_reviewed: Optional[bool]
    application_threshhold: Optional[int]
    current_number_of_application: Optional[int]
    offer_letter: Optional[str]
    offer_letter_specifications: Optional[str]
    offer_letter_approved: Optional[bool]
    offer_sent: Optional[bool]
    status: Optional[Literal[
        "received_position", "jd_created", "jd_approved", "job_posted", "resume_reviewed", "offer_sent"
    ]]

class HRRecruitingGraph:
    def __init__(self):
        self.graph = self._build_graph()
        self.cerebras_utils = CerebrasUtils()

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
        print(f"Posted Job Listing Data: *8888*")
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
        selection_successful = state.get("candidate_selected", False)
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
        graphBuilder.add_edge("send_offer", END)
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

