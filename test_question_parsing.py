#!/usr/bin/env python3
"""
Test script to evaluate OpenAI's ability to parse complex legal questions
into structured data for enhanced search strategies.
"""

import os
import json
from openai import OpenAI
from typing import List, Dict
from app.config import settings

# Initialize OpenAI client
client = OpenAI(api_key=settings.openai_api_key)

def parse_question_with_functions(question: str) -> Dict:
    """
    Use OpenAI function calling to parse a legal question into structured data.
    """
    
    # Define the function schema for parsing legal questions
    functions = [
        {
            "name": "extract_constitutional_topics",
            "description": "Extract constitutional topics, sections, and concepts from legal questions",
            "parameters": {
                "type": "object",
                "properties": {
                    "topics": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of constitutional topics and concepts (e.g., 'Congress powers', 'Presidential powers', '22nd Amendment')"
                    },
                    "sections": {
                        "type": "array", 
                        "items": {"type": "string"},
                        "description": "Specific constitutional sections and articles (e.g., 'Article I Section 8', 'Article II Section 2', 'Amendment XXII')"
                    },
                    "legal_concepts": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Legal concepts and terms (e.g., 'impeachment', 'commerce clause', 'due process')"
                    },
                    "question_type": {
                        "type": "string",
                        "description": "Type of question: 'simple', 'comparison', 'multi-part', 'complex'"
                    }
                },
                "required": ["topics", "sections", "legal_concepts", "question_type"]
            }
        }
    ]
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system", 
                    "content": "You are an expert at analyzing questions and breaking them down into essential components. Analyze the given question and break it down into the most essential sub-questions needed to provide a complete answer. Focus on distinct aspects that require separate consideration."
                },
                {
                    "role": "user", 
                    "content": f"Parse this legal question: '{question}'"
                }
            ],
            functions=functions,
            function_call={"name": "extract_constitutional_topics"}
        )
        
        # Extract the function call arguments
        function_call = response.choices[0].message.function_call
        if function_call and function_call.name == "extract_constitutional_topics":
            return json.loads(function_call.arguments)
        else:
            return {"error": "No function call returned"}
            
    except Exception as e:
        return {"error": f"OpenAI API error: {str(e)}"}

def test_question_parsing():
    """
    Test OpenAI's question parsing ability with various complexity levels.
    """
    
    # Test questions from simple to complex
    test_questions = [
        # Simple single-concept questions
        "Who appoints ambassadors?",
        "What is the 22nd Amendment?",
        
        # Medium complexity - multiple related concepts
        "What are the requirements for impeachment and how does it work?",
        "Compare the powers of Congress vs the President",
        
        # Complex multi-part questions
        "What are the requirements for impeachment, how does it differ from removal, and what role does the Supreme Court play?",
        "Explain the commerce clause, the necessary and proper clause, and how they've been interpreted in different amendments",
        "Compare the powers of Congress in Article I vs the President in Article II, and how do the 22nd Amendment limits interact with emergency powers?",
        
        # Very complex cross-referencing questions
        "How do the 14th Amendment's due process and equal protection clauses relate to the 1st Amendment's free speech protections, and what role does the Supreme Court play in balancing these rights?",
        "What are the war powers of Congress under Article I, the President's commander-in-chief powers under Article II, and how have these been interpreted in cases involving the War Powers Resolution?"
    ]
    
    print("🧪 Testing OpenAI Question Parsing")
    print("=" * 80)
    
    for i, question in enumerate(test_questions, 1):
        print(f"\n📝 Question {i}: {question}")
        print("-" * 60)
        
        # Parse the question
        result = parse_question_with_functions(question)
        
        if "error" in result:
            print(f"❌ Error: {result['error']}")
            continue
        
        # Display results
        print(f"🎯 Question Type: {result.get('question_type', 'N/A')}")
        
        print(f"📚 Topics ({len(result.get('topics', []))}):")
        for topic in result.get('topics', []):
            print(f"   • {topic}")
        
        print(f"📖 Sections ({len(result.get('sections', []))}):")
        for section in result.get('sections', []):
            print(f"   • {section}")
        
        print(f"⚖️ Legal Concepts ({len(result.get('legal_concepts', []))}):")
        for concept in result.get('legal_concepts', []):
            print(f"   • {concept}")
        
        # Evaluate the parsing quality
        topics = result.get('topics', [])
        sections = result.get('sections', [])
        concepts = result.get('legal_concepts', [])
        
        quality_score = 0
        if topics: quality_score += 1
        if sections: quality_score += 1  
        if concepts: quality_score += 1
        if len(topics) >= 2: quality_score += 1  # Multiple topics for complex questions
        if any('Article' in s or 'Amendment' in s for s in sections): quality_score += 1
        
        print(f"✅ Quality Score: {quality_score}/5")
        
        if quality_score >= 4:
            print("🎉 Excellent parsing!")
        elif quality_score >= 3:
            print("👍 Good parsing")
        else:
            print("⚠️ Needs improvement")

def split_question_basic(question: str) -> List[str]:
    """
    Basic approach - simple splitting with truncation.
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "Break down complex legal questions into simpler sub-questions. Return only the sub-questions, one per line, without numbering or bullets."
                },
                {
                    "role": "user",
                    "content": f"Break down this question: '{question}'"
                }
            ],
            max_tokens=200
        )
        
        sub_questions = response.choices[0].message.content.strip().split('\n')
        sub_questions = [q.strip() for q in sub_questions if q.strip()]
        
        # Truncate to 3 as originally planned
        return sub_questions[:3]
        
    except Exception as e:
        return [f"Error: {e}"]

def split_question_smart(question: str) -> List[str]:
    """
    Smart approach - let OpenAI decide optimal number with quality focus.
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "Break down this legal question into the most essential sub-questions needed to answer it completely. Focus on core concepts that must be addressed and distinct aspects that need separate consideration. Avoid redundant or overly specific questions. Return only the most relevant sub-questions, one per line, without numbering."
                },
                {
                    "role": "user",
                    "content": f"Question: '{question}'"
                }
            ],
            max_tokens=200
        )
        
        sub_questions = response.choices[0].message.content.strip().split('\n')
        return [q.strip() for q in sub_questions if q.strip()]
        
    except Exception as e:
        return [f"Error: {e}"]

def split_question_structured(question: str) -> Dict:
    """
    Structured approach - function calling with reasoning.
    """
    functions = [
        {
            "name": "analyze_question_complexity",
            "description": "Analyze question complexity and extract essential sub-questions",
            "parameters": {
                "type": "object",
                "properties": {
                    "complexity": {
                        "type": "string",
                        "enum": ["simple", "medium", "complex"],
                        "description": "Question complexity level"
                    },
                    "sub_questions": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Essential sub-questions needed to answer the original question"
                    },
                    "reasoning": {
                        "type": "string", 
                        "description": "Brief explanation of why these sub-questions were selected"
                    }
                },
                "required": ["complexity", "sub_questions", "reasoning"]
            }
        }
    ]
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system", 
                    "content": "You are an expert at analyzing questions and breaking them down into essential components. Analyze the given question and break it down into the most essential sub-questions needed to provide a complete answer. Focus on distinct aspects that require separate consideration."
                },
                {
                    "role": "user", 
                    "content": f"Analyze this question: '{question}'"
                }
            ],
            functions=functions,
            function_call={"name": "analyze_question_complexity"}
        )
        
        function_call = response.choices[0].message.function_call
        if function_call and function_call.name == "analyze_question_complexity":
            return json.loads(function_call.arguments)
        else:
            return {"error": "No function call returned"}
            
    except Exception as e:
        return {"error": f"OpenAI API error: {str(e)}"}

def test_question_splitting_comparison():
    """
    Test all three approaches and compare results.
    """
    
    print("\n\n🔬 Testing Question Splitting Approaches")
    print("=" * 80)
    
    test_questions = [
        "What are the requirements for impeachment, how does it differ from removal, and what role does the Supreme Court play?",
        "Explain the commerce clause, the necessary and proper clause, and how they've been interpreted in different amendments",
        "Compare the powers of Congress in Article I vs the President in Article II, and how do the 22nd Amendment limits interact with emergency powers?"
    ]
    
    for i, question in enumerate(test_questions, 1):
        print(f"\n📝 Question {i}: {question}")
        print("-" * 80)
        
        # Test all three approaches
        print("\n🔹 Approach 1: Basic (Truncated to 3)")
        basic_results = split_question_basic(question)
        print(f"   Count: {len(basic_results)}")
        for j, sub_q in enumerate(basic_results, 1):
            print(f"   {j}. {sub_q}")
        
        print("\n🔹 Approach 2: Smart (Quality Focus)")
        smart_results = split_question_smart(question)
        print(f"   Count: {len(smart_results)}")
        for j, sub_q in enumerate(smart_results, 1):
            print(f"   {j}. {sub_q}")
        
        print("\n🔹 Approach 3: Structured (With Reasoning)")
        structured_results = split_question_structured(question)
        if "error" not in structured_results:
            print(f"   Complexity: {structured_results.get('complexity', 'N/A')}")
            print(f"   Count: {len(structured_results.get('sub_questions', []))}")
            print(f"   Reasoning: {structured_results.get('reasoning', 'N/A')}")
            for j, sub_q in enumerate(structured_results.get('sub_questions', []), 1):
                print(f"   {j}. {sub_q}")
        else:
            print(f"   Error: {structured_results['error']}")
        
        # Analysis
        print(f"\n📊 Analysis:")
        print(f"   Basic: {len(basic_results)} sub-questions")
        print(f"   Smart: {len(smart_results)} sub-questions")
        if "error" not in structured_results:
            print(f"   Structured: {len(structured_results.get('sub_questions', []))} sub-questions")
        
        # Determine best approach
        if "error" not in structured_results:
            structured_count = len(structured_results.get('sub_questions', []))
            if structured_count <= len(smart_results) and structured_count <= len(basic_results):
                print(f"   🏆 Winner: Structured approach (most concise)")
            elif len(smart_results) <= len(basic_results):
                print(f"   🏆 Winner: Smart approach (good balance)")
            else:
                print(f"   🏆 Winner: Basic approach (simplest)")
        else:
            if len(smart_results) <= len(basic_results):
                print(f"   🏆 Winner: Smart approach")
            else:
                print(f"   🏆 Winner: Basic approach")

if __name__ == "__main__":
    # Check if OpenAI API key is set
    if not settings.openai_api_key:
        print("❌ Error: OpenAI API key not found in configuration")
        print("Please check your .env file or environment variables")
        exit(1)
    
    # Run tests
    test_question_parsing()
    test_question_splitting_comparison()
    
    print("\n\n🎯 Summary")
    print("=" * 80)
    print("Review the results above to decide:")
    print("1. Is the structured parsing good enough for your use case?")
    print("2. Would simple question splitting work better?")
    print("3. Should we implement enhanced search with this approach?")
