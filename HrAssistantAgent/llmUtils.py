from langchain_cerebras import ChatCerebras
from langchain.prompts import ChatPromptTemplate
from langchain_community.document_loaders import TextLoader
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import PromptTemplate


from typing import List
from pydantic import BaseModel, Field
from dotenv import load_dotenv



load_dotenv()


class JobListing(BaseModel):
    """
    Represents a detailed job posting, based on the provided TypeScript interface.
    """
    title: str = Field(
        description='The title of the job position (e.g., "Senior Software Engineer")'
    )
    company: str = Field(
        description='The name of the company posting the job'
    )
    type: str = Field(
        description='The employment type (e.g., "Full-time", "Contract")'
    )
    description: str = Field(
        description='A detailed, markdown-formatted description of the job role'
    )
    requirements: List[str] = Field(
        description='A list of required skills or qualifications for the role'
    )



class CerebrasUtils:
    def __init__(self):
        self.llm = ChatCerebras(model="llama-3.3-70b")
        self.JobListingParser = PydanticOutputParser(pydantic_object=JobListing)
    

    def create_job_description(self, position: str) -> str:
        loader = TextLoader("companyinfo.txt",encoding='utf-8')
        docs= loader.load()
        company_context = docs[0].page_content 

        prompt = PromptTemplate.from_template(
            "You are an HR assistant. Write a job description for the position: {position}. "
            "Context about company can be taken from: {company_context}."
        )
        chain = prompt | self.llm
        response = chain.invoke({"position": position, "company_context": company_context})
        return response.content
    
    def change_job_description(self, jd: str, suggestions: str) -> str:
        prompt = PromptTemplate.from_template(
            "You are an HR assistant. Modify the following job description based on these suggestions: {suggestions}\n"
            "Job Description: {jd}"
        )
        chain = prompt | self.llm
        response = chain.invoke({"jd": jd, "suggestions": suggestions})
        return response.content
    


    def create_post_listing_data(self, jd: str) -> JobListing:
    
        prompt = ChatPromptTemplate.from_template(
            template = "You are an HR assistant. Extract the job listing details from the following job description: {jd}\n Return the details in a structured format. \n {format_instruction}",
            partial_variables={'format_instruction':self.JobListingParser.get_format_instructions()},
        )
        chain = prompt | self.llm | self.JobListingParser
        response = chain.invoke({"jd": jd})
        return response.model_dump_json(indent=2)
    

    def tweak_job_description(self, jd: str, post_listing: JobListing) -> str:
        
        prompt = ChatPromptTemplate.from_template(
            template = """You are an HR assistant. The job description is not attracting enough candidates.\n Make slight modifications to improve its appeal.\n
            Job Description: {jd}\n
            previous Job Listing: {post_listing}
            \n {format_instruction}
            """,
            partial_variables={'format_instruction':self.JobListingParser.get_format_instructions()},
        )

        chain = prompt | self.llm | self.JobListingParser
        response = chain.invoke({"jd": jd, post_listing: post_listing})
        return response.model_dump_json(indent=2)
    

    def review_resumes(self, resumes: List[str], jd: str) -> List[str]:
        prompt = PromptTemplate.from_template(
            "You are an HR assistant. Review the following resumes against the job description: {jd}\n"
            "Resumes: {resumes}\n"
            "Return a list of the most suitable candidates."
        )
        chain = prompt | self.llm
        response = chain.invoke({"jd": jd, "resumes": resumes})
        return response.content.splitlines()
    
    def generate_offer_letter(self, candidate_name: str, position: str, salary: str, benefits: str) -> str:
        prompt = PromptTemplate.from_template(
            "You are an HR assistant. Generate a formal offer letter for the candidate {candidate_name} for the position of {position}.\n"
            "Include the salary of {salary} and benefits: {benefits}."
        )
        chain = prompt | self.llm
        response = chain.invoke({"candidate_name": candidate_name, "position": position, "salary": salary, "benefits": benefits})
        return response.content
    
  

    
    


def main():
    # 1. Instantiate the utility class (Create the object)
    hr_tool = CerebrasUtils()

    # 2. Define your desired inputs
    position_title = "Senior Data Scientist (AI Inference Optimization)"
    jd = """
**Job Title: Senior Data Scientist (AI Inference Optimization)**

**Company Overview:**
Cerebras Systems is a pioneering AI technology company that designs and builds the world's fastest AI infrastructure to accelerate deep learning and generative AI workloads. Our mission is to deliver unmatched speed and ultra-low latency, enabling real-time and agentic AI applications. We are seeking a highly skilled Senior Data Scientist to join our team, focusing on AI Inference Optimization.

**Job Summary:**
We are looking for a seasoned Senior Data Scientist to lead the optimization of AI inference workloads on our Wafer-Scale Engine (WSE) and CS-3 System. The ideal candidate will have a deep understanding of AI, machine learning, and deep learning principles, as well as experience with optimization techniques for inference workloads. The Senior Data Scientist will work closely with our engineering teams to develop and implement optimized AI models, leveraging our custom compiler, scheduler, and runtime. The goal is to further enhance the performance of our AI supercomputing systems, delivering up to 20x faster inference than traditional GPU solutions.

**Key Responsibilities:**

1. **Optimize AI Inference Workloads**: Develop and implement optimized AI models for inference workloads on our WSE and CS-3 System, leveraging our custom hardware and software integrations.
2. **Collaborate with Engineering Teams**: Work closely with our engineering teams to develop and refine our custom compiler, scheduler, and runtime to optimize AI inference performance.
3. **AI Frameworks and APIs**: Utilize and optimize our custom Cerebras API and Model Zoo, as well as integrate with popular AI frameworks like PyTorch, LangChain, Hugging Face, and OpenRouter.
4. **Performance Analysis and Optimization**: Conduct in-depth performance analysis of AI inference workloads and develop strategies to optimize performance, leveraging techniques such as model pruning, quantization, and knowledge distillation.
5. **Stay Up-to-Date with AI Trends**: Stay current with the latest developments in AI, machine learning, and deep learning, applying this knowledge to continually improve our AI inference optimization capabilities.    
6. **Communicate with Cross-Functional Teams**: Collaborate with and communicate technical results to cross-functional teams, including sales, marketing, and customer support.
7. **Develop and Maintain Documentation**: Develop and maintain technical documentation of optimized AI models, workflows, and best practices for inference workloads on our systems.

**Requirements:**

1. **Advanced Degree**: Master's or Ph.D. in Computer Science, Electrical Engineering, or a related field.
2. **AI and Machine Learning Expertise**: 5+ years of experience in AI, machine learning, and deep learning, with a focus on optimization techniques for inference workloads.
3. **Programming Skills**: Proficiency in programming languages such as C, C++, Python, and experience with AI frameworks like PyTorch, TensorFlow, or similar.
4. **Custom Hardware and Software**: Experience with custom hardware and software integrations, including compilers, schedulers, and runtime environments.
5. **Strong Analytical and Problem-Solving Skills**: Ability to analyze complex problems, develop creative solutions, and optimize system performance.
6. **Excellent Communication Skills**: Effective communication and collaboration skills, with the ability to work with cross-functional teams and communicate technical results to non-technical stakeholders.

**Nice to Have:**

1. **Experience with Wafer-Scale Engine or Similar Architectures**: Familiarity with our Wafer-Scale Engine or similar architectures, including experience with optimizing AI workloads on custom hardware.
2. **Knowledge of LangChain, Hugging Face, or OpenRouter**: Experience with LangChain, Hugging Face, or OpenRouter, and their integration with our systems.
3. **Cloud Computing Experience**: Experience with cloud computing platforms, including our Cerebras Cloud API.

**What We Offer:**

1. **Competitive Salary and Benefits**: A competitive salary and benefits package, including health insurance, retirement planning, and paid time off.
2. **Opportunity to Work on Cutting-Edge Technology**: The chance to work on the world's fastest AI infrastructure, accelerating deep learning and generative AI workloads.
3. **Collaborative and Dynamic Work Environment**: A collaborative and dynamic work environment, with a team of experienced professionals passionate about AI and machine learning.
4. **Professional Development Opportunities**: Opportunities for professional growth and development, including training, mentorship, and conferenonal growth and development, including training, mentorship, and conference attendance.

ce attendance.

If you are a motivated and experienced Senior Data Scientist looking to work on the latest AI technologies, we encourage you to apply for this exc

If you are a motivated and experienced Senior Data Scientist looking to work on the latest AI technologies, we encourage you to apply for this excIf you are a motivated and experienced Senior Data Scientist looking to work on the latest AI technologies, we encourage you to apply for this excork on the latest AI technologies, we encourage you to apply for this exciting opportunity to join our team!

"""


  
        # 3. Call the method on the instantiated object
    result = hr_tool.create_post_listing_data(
        jd=jd
    )
    
    # 4. Print the result
    print("\n---------------------------------------------------------")
    print(result)
    print("\n---------------------------------------------------------")

# This calls the main function when the script is run directly
if __name__ == "__main__":
    main()