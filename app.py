import streamlit as st
import time
# Assuming HrAssistantAgent is the folder name, and graphUtil is the file
from HrAssistantAgent.graphUtil import HRRecruitingGraph 
from langgraph.types import Command, Interrupt # Import both Command and Interrupt

# --- 1. Initialize session state variables for graph management ---
THREAD_ID = "streamlit-hr-thread"

if 'hr_graph' not in st.session_state:
    st.session_state.hr_graph = HRRecruitingGraph()
if 'current_state' not in st.session_state:
    st.session_state.current_state = {} 
if 'workflow_log' not in st.session_state:
    st.session_state.workflow_log = []
if 'is_running' not in st.session_state:
    st.session_state.is_running = False
if 'interruption_node' not in st.session_state:
    st.session_state.interruption_node = None 
if 'interruption_message' not in st.session_state:
    st.session_state.interruption_message = None 

st.title("🤖 HR Assistant Agent Workflow")

# --- UI for Position Input ---
default_position = st.session_state.current_state.get('position', "Software Engineer")

position = st.text_input(
    "Enter the job position:", 
    value=default_position,
    disabled=bool(st.session_state.interruption_node or st.session_state.is_running)
)

# --- Define helper to extract interruption data ---
def _extract_interruption_data(step: dict) -> tuple[str, str]:
    """Extracts node name and clean message from the __interrupt__ step."""
    interruption_node_raw = step['__interrupt__']
    
    node_name = 'unknown_node'
    pause_message = "Workflow paused for human input."

    item_to_inspect = interruption_node_raw
    if isinstance(interruption_node_raw, (list, tuple)):
        # If it's a tuple, take the first element for the Interrupt object
        item_to_inspect = interruption_node_raw[0]
        # Also check for the node name string if it's included in the list/tuple
        for item in interruption_node_raw:
             if isinstance(item, str) and item != '__interrupt__':
                 node_name = item
                 
    # Extract value from Interrupt Command (the part the user wants)
    if isinstance(item_to_inspect, Interrupt):
        pause_message = item_to_inspect.value
        # Use node name from ID as a fallback
        if node_name == 'unknown_node':
            node_name = str(item_to_inspect.id) 
            # Simple heuristic to clean up the ID to a node name
            if '-' in node_name and not node_name.startswith('approve_'):
                node_name = node_name.split('-')[0]
    
    # Final check for node name (use the only key if it's not the interrupt key)
    if node_name == 'unknown_node' and next(iter(step.keys())) != '__interrupt__':
         node_name = next(iter(step.keys()))

    return node_name, pause_message


# --- Define the function to run the graph or resume it ---
def run_workflow_stream(initial_input):
    """
    Runs or resumes the graph, yielding steps until completion or human intervention.
    initial_input can be a dict (for start) or a Command (for resume).
    """
    hr_graph_instance = st.session_state.hr_graph.graph 
    config = {"configurable": {"thread_id": THREAD_ID}}
    
    # Stream the graph execution
    for step in hr_graph_instance.stream(initial_input, config=config):
        
        if step is None:
            continue 

        # Check for interruption command in the stream output first
        if '__interrupt__' in step:
             
             node_name, pause_message = _extract_interruption_data(step)
             
             # --- Set State ---
             st.session_state.interruption_node = node_name
             st.session_state.interruption_message = pause_message
             st.session_state.is_running = False
             
             # Log the message
             log_message = f"### Node: `{node_name}`\n"
             log_message += f"⚠️ **Workflow PAUSED!** {pause_message}\n"
             st.session_state.workflow_log.append(log_message)
             yield log_message 
             return # Stop the generator
             
        # Normal step logging
        node_name = next(iter(step)) 
        state_updates = step[node_name]

        if state_updates is None:
            continue
            
        # Update the overall state before logging
        st.session_state.current_state.update(state_updates) 

        # Prepare log message
        msg = state_updates.get("msg", "")
        # Filter out the internal LangChain/LangGraph messages that are dicts or objects
        state_display = {k: v for k, v in state_updates.items() if k != "msg" and not isinstance(v, (dict, list))}

        log_message = f"### Node: `{node_name}`\n"
        if msg:
            log_message += f"{msg}\n"
        if state_display:
            log_message += "**State Updates:**\n"
            for k, v in state_display.items():
                if k in ['jd', 'offer_letter']: # Truncate long strings for cleaner log
                    v_display = v[:100] + "..." if v and len(v) > 100 else v
                else:
                    v_display = v
                log_message += f"- **{k}**: `{v_display}`\n"

        st.session_state.workflow_log.append(log_message)
        yield log_message


# --- Main Run Button ---
if st.button(
    "▶️ Run HR Workflow",
    disabled=st.session_state.is_running or bool(st.session_state.interruption_node)
):
    st.session_state.is_running = True
    st.session_state.current_state = {} 
    st.session_state.workflow_log = []
    st.session_state.interruption_node = None # Clear any previous pause
    st.session_state.interruption_message = None
    

    st.subheader("Workflow Log")
    log_container = st.container()
    
    initial_state = {"position": position, "is_running": True}

    with log_container:
        for step_output in run_workflow_stream(initial_state):
            with st.chat_message("Agent"):
                st.markdown(step_output)
            time.sleep(0.2) 
            
    st.session_state.is_running = False
    st.rerun() 


# --- Generic Interruption Handler (Conditional) ---
if st.session_state.interruption_node:
    interruption_node = st.session_state.interruption_node
    
    # Use the clean message for the subheader
    st.subheader(f"Human Intervention Required: {st.session_state.interruption_message}")
    
    # --- 1. Dynamic UI for Interruption Type (uses node name for routing) ---
    
    # Use the stored message, stripping the "Waiting for" part for clarity
    prompt = st.session_state.interruption_message.strip().replace("Waiting for ", "Confirm: ") 
    Submission_key = "Approval"
    if 'JD' in st.session_state.interruption_message :
        if st.session_state.current_state.get('jd'):
            with st.expander("Review Generated Job Description (JD)"):
                st.markdown(st.session_state.current_state['jd'])
        Submission_key = "JD"
                
    elif 'Offer Letter' in st.session_state.interruption_message:
        if st.session_state.current_state.get('offer_letter'):
            with st.expander("Review Generated Offer Letter"):
                st.markdown(st.session_state.current_state['offer_letter'])
        Submission_key = "Offer Letter"

    elif 'interview' in st.session_state.interruption_message:
        if st.session_state.current_state.get('selected_candidate_data'):
            with st.expander("Review Proposed Interview Schedule"):
                st.markdown(st.session_state.current_state['selected_candidate_data'])
        Submission_key = "Interview Schedule"
                
    else:
        st.info(f"Unknown interruption node: {interruption_node}. Proceeding with 'yes/no' approval.")
        
    approval_decision = st.radio(
        prompt,
        options=["yes", "no"],
        key="approval_radio"
    )

    # --- 2. Resume Button Logic ---
    if st.button(f"Submit Approval for {Submission_key}"):
        
        approval_command = Command(resume=approval_decision) 

        # Reset pause flag and set running flag
        st.session_state.interruption_node = None
        st.session_state.interruption_message = None
        st.session_state.is_running = True
        
        st.subheader("Workflow Log (Resuming...)")
        log_container = st.container()

        # Resume the workflow stream
        with log_container:
            for step_output in run_workflow_stream(approval_command):
                with st.chat_message("Agent"):
                    st.markdown(step_output)
                time.sleep(0.1)
                
        # Final state check after resuming
        st.session_state.is_running = False
        if st.session_state.interruption_node:
             st.warning(f"Workflow paused again at **{st.session_state.interruption_node}**.")
        else:
             st.success("🎉 Workflow completed or continued successfully!")
        
        st.rerun() 


# --- Display Current Workflow Log ---
st.subheader("Current Workflow Log")
for log in st.session_state.workflow_log:
    with st.chat_message("Agent"):
        st.markdown(log)

# --- Final Status ---
if not st.session_state.is_running and not st.session_state.interruption_node and st.session_state.workflow_log:
    final_status = st.session_state.current_state.get('status')
    if final_status == 'offer_sent':
        st.balloons()
        st.success("🚀 HR Workflow completed successfully: Offer Sent!")
    elif final_status:
        st.info(f"Current State Status: `{final_status}`")