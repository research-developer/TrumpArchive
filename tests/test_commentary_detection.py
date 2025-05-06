"""
Test the AI-based commentary detection functionality.

This script:
1. Takes a transcript sample
2. Uses LangChain with OpenAI to evaluate commentary level
3. Reports confidence levels for different commentary types
"""

import os
import json
from dotenv import load_dotenv
from langchain.llms import OpenAI
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate

# Load environment variables
load_dotenv()

# Get OpenAI API key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

def evaluate_commentary(title, description, transcript_segment):
    """Evaluate the level of commentary in a video based on transcript."""
    # Initialize OpenAI
    llm = OpenAI(temperature=0, openai_api_key=OPENAI_API_KEY)
    
    # Create prompt template
    commentary_prompt = PromptTemplate(
        input_variables=["title", "description", "transcript_segment"],
        template="""
        You are evaluating a YouTube video to determine if it contains commentary on Donald Trump or is a direct recording.
        
        Title: {title}
        Description: {description}
        Transcript segment: {transcript_segment}
        
        On a scale of 0-100, what is the confidence level that this video:
        1. Contains NO commentary (just Trump speaking or being interviewed)
        2. Contains MINIMAL commentary (brief intro/outro only)
        3. Contains SUBSTANTIAL commentary (analysis, interpretation, reaction)
        
        Output your answer as a JSON object with these fields:
        - no_commentary_confidence: 0-100
        - minimal_commentary_confidence: 0-100
        - substantial_commentary_confidence: 0-100
        - reasoning: Brief explanation of your reasoning
        - final_classification: One of ["no_commentary", "minimal_commentary", "substantial_commentary"]
        """
    )
    
    # Create chain
    commentary_chain = LLMChain(llm=llm, prompt=commentary_prompt)
    
    # Run chain
    result = commentary_chain.run({
        "title": title,
        "description": description,
        "transcript_segment": transcript_segment
    })
    
    # Parse JSON result
    try:
        evaluation = json.loads(result)
        return evaluation
    except json.JSONDecodeError:
        print(f"Error parsing result: {result}")
        return None

def main():
    # Test cases
    test_cases = [
        {
            "title": "FULL REMARKS: President Trump delivers commencement speech at University of Alabama",
            "description": "President Trump's spring commencement address to graduating seniors at The University at Alabama.",
            "transcript_segment": "Thank you, coach. Wow, what a nice looking group this is. What a beautiful group of people. And especially a very big hello to the University of Alabama. Congratulations to the class of 2025. Roll tide. Roll tide. There are things that happen in life that are very important and you always remember where you were when they happened.",
            "expected_result": "no_commentary"
        },
        {
            "title": "Trump DESTROYS Liberal Policies in EPIC New Hampshire Speech",
            "description": "President Trump delivers remarks on Biden's failed policies during a campaign rally. Watch how he exposes the truth about the radical left agenda!",
            "transcript_segment": "As you can see, Trump's speech today was filled with the usual talking points. He started by attacking Biden's border policies, claiming - without evidence - that millions of illegal immigrants are pouring into the country. Let's listen to what he said: 'We're going to close the border and we're going to do it fast. No country can survive with open borders.'",
            "expected_result": "substantial_commentary"
        },
        {
            "title": "President Trump Interview with Sean Hannity - Full Interview",
            "description": "Former President Donald Trump sits down with Sean Hannity for an exclusive interview on Fox News.",
            "transcript_segment": "HANNITY: Welcome back to 'Hannity.' Joining us now, the 45th President of the United States, Donald Trump. Mr. President, thank you for being with us tonight. TRUMP: Thank you, Sean. It's great to be with you as always. HANNITY: Let's start with the economy. Inflation is at a 40-year high. How would you have handled this differently?",
            "expected_result": "minimal_commentary"
        }
    ]
    
    # Run evaluations
    for i, case in enumerate(test_cases):
        print(f"\nTesting Case {i+1}:")
        print(f"Title: {case['title']}")
        print(f"Expected result: {case['expected_result']}")
        
        # Run evaluation
        evaluation = evaluate_commentary(
            case["title"],
            case["description"],
            case["transcript_segment"]
        )
        
        if evaluation:
            print("\nResults:")
            print(f"No commentary confidence: {evaluation['no_commentary_confidence']}")
            print(f"Minimal commentary confidence: {evaluation['minimal_commentary_confidence']}")
            print(f"Substantial commentary confidence: {evaluation['substantial_commentary_confidence']}")
            print(f"Final classification: {evaluation['final_classification']}")
            print(f"Reasoning: {evaluation['reasoning']}")
            
            # Check if result matches expectation
            if evaluation['final_classification'] == case['expected_result']:
                print("✅ Test passed!")
            else:
                print("❌ Test failed!")
        else:
            print("❌ Evaluation failed!")

if __name__ == "__main__":
    if not OPENAI_API_KEY:
        print("OpenAI API key not found. Please set OPENAI_API_KEY in .env file.")
        exit(1)
    
    main()