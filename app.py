import streamlit as st
import time
from HrAssistantAgent.graphUtil import HRRecruitingGraph 

# 1. Initialize session state variables for graph management
if 'hr_graph' not in st.session_state:
    st.session_state.hr_graph = HRRecruitingGraph()
if 'current_state' not in st.session_state:
    st.session_state.current_state = None
if 'workflow_log' not in st.session_state:
    st.session_state.workflow_log = []
if 'is_running' not in st.session_state:
    st.session_state.is_running = False

st.title("🤖 HR Assistant Agent Workflow")

# --- UI for Position Input ---
default_position = "Software Engineer"
if st.session_state.current_state and st.session_state.current_state.get('position'):
    default_position = st.session_state.current_state['position']

position = st.text_input(
    "Enter the job position:", 
    value=default_position
)

# --- Define the function to run the graph ---
def run_hr_workflow(start_state=None):
    """Runs the graph, yielding steps until completion or human intervention."""
    hr_graph_instance = st.session_state.hr_graph.graph # Get the compiled graph
    
    # Determine the initial state for the run
    if start_state is None:
        initial_state = {"position": position, "jd_approved": True}
        st.session_state.workflow_log = [] # Clear log for a new run
    else:
        initial_state = start_state
        
    # Stream the graph execution
    for step in hr_graph_instance.stream(initial_state):
        # Langgraph yields a dictionary with the node name as the key
        node_name = next(iter(step)) 
        state_updates = step[node_name]

        msg = state_updates.get("msg", "")
        state_display = {k: v for k, v in state_updates.items() if k != "msg"}

        log_message = f"### Node: `{node_name}`\n"
        if msg:
            log_message += f"{msg}\n"
        if state_display:
            log_message += "**State Updates:**\n"
            for k, v in state_display.items():
                log_message += f"- **{k}**: `{v}`\n"

        # Log the step in a streaming fashion
        st.session_state.workflow_log.append(log_message)
        st.session_state.current_state = state_updates
        yield log_message


        # Check for specific states that require human intervention (JD Approval)
        # if node_name == "approve_jd":
        #     st.session_state.current_state = state_updates # Save state before human input
        #     st.session_state.workflow_log.append("--- **PAUSED:** Awaiting **JD Approval** ---")
        #     st.session_state.is_running = False
        #     return
        
        # # Log the step in a streaming fashion
        # st.session_state.workflow_log.append(log_message)
        
        # # Update current state for the next step or final result
        # st.session_state.current_state = state_updates
        # yield log_message

# # --- Display Log Container ---
# st.subheader("Workflow Log")
# log_container = st.container() # Use a fixed-height container for log
# for log_entry in st.session_state.workflow_log:
#     with log_container:
#         with st.chat_message("Agent"):
#             st.markdown(log_entry)


# # --- 2. Human-in-the-Loop Logic (JD Approval) ---

# # Check if the graph is paused at the JD approval step
# if st.session_state.current_state and st.session_state.current_state.get('jd') and st.session_state.current_state.get('jd_approved') is None:
#     st.session_state.is_running = False
    
#     st.divider()
#     st.error("🚨 **Human-in-the-Loop Required: Review Job Description**")
    
#     current_jd = st.session_state.current_state.get('jd', 'No JD found.')
    
#     with st.expander("Review Generated Job Description", expanded=True):
#         st.code(current_jd, language="markdown")
        
#     # Capture human decision
#     jd_decision = st.radio(
#         "Action:",
#         ("Approve and Continue", "Suggest Revisions"),
#         key="jd_decision_radio"
#     )
    
#     revision_suggestions = ""
#     if jd_decision == "Suggest Revisions":
#         revision_suggestions = st.text_area(
#             "Enter suggestions for revision:",
#             "Include experience with Python and AI.",
#             key="jd_revisions_text"
#         )

#     # Button to submit the decision and resume the graph
#     if st.button("Submit JD Decision"):
        
#         # Update the state based on human input
#         new_state = st.session_state.current_state
#         if jd_decision == "Approve and Continue":
#             new_state['jd_approved'] = True
#             new_state['jd_suggestions'] = None
#             st.session_state.workflow_log.append("--- **HUMAN ACTION:** JD Approved. ---")
#         else:
#             # When suggesting revisions, approve_jd will be False, and we pass the suggestions
#             new_state['jd_approved'] = False 
#             new_state['jd_suggestions'] = revision_suggestions
#             st.session_state.workflow_log.append(f"--- **HUMAN ACTION:** Revisions requested: '{revision_suggestions[:50]}...' ---")

#         # Rerun the workflow with the updated state
#         st.session_state.is_running = True
        
#         # Rerunning the workflow log will update the container
#         for step_output in run_hr_workflow(new_state):
#              with log_container:
#                  with st.chat_message("Agent"):
#                      st.markdown(step_output)
                     
#         st.session_state.is_running = False
#         st.rerun() # Use rerun to update the main UI cleanly

# is_paused_for_approval = (
#     st.session_state.current_state is not None and
#     st.session_state.current_state.get('jd_approved') is None
# )
if st.button(
    "▶️ Run HR Workflow",
    # disabled=bool(st.session_state.is_running or is_paused_for_approval)
    disabled=bool(st.session_state.is_running or False)
):
    st.session_state.is_running = True
    st.session_state.current_state = None
    st.session_state.workflow_log = []

    st.subheader("Workflow Log")
    log_container = st.container()
    for step_output in run_hr_workflow():
        with log_container:
            with st.chat_message("Agent"):
                st.markdown(step_output)
            
        time.sleep(1)  # Optional: add a small delay for effect

    if st.session_state.current_state and st.session_state.current_state.get('jd_approved') is None:
        st.warning("Workflow paused for human approval.")
    else:
        st.success("🎉 Workflow completed successfully!")
        st.session_state.is_running = False

        
# if st.button(
#     "▶️ Run HR Workflow",
#     disabled=bool(st.session_state.is_running or is_paused_for_approval)
# ):
# # --- 3. Main Run Button ---    
#     st.session_state.is_running = True
    
#     # Clear previous state/log for a fresh start
#     st.session_state.current_state = None
#     st.session_state.workflow_log = []

#     # Run the graph and stream to the log container
#     # for step_output in run_hr_workflow():
#     #     with log_container:
#     #         with st.chat_message("Agent"):
#     #             st.markdown(step_output)
    
#     # After the loop finishes (either completed or paused)
#     if st.session_state.current_state and st.session_state.current_state.get('jd_approved') is None:
#         st.warning("Workflow paused for human approval.")
#     else:
#         st.success("🎉 Workflow completed successfully!")
#         st.session_state.is_running = False